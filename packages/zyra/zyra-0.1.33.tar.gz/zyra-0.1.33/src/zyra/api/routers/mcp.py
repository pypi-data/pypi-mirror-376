# SPDX-License-Identifier: Apache-2.0
"""MCP adapter router.

Exposes a minimal JSON-RPC 2.0 interface and progress streaming for MCP clients:

- ``POST /mcp`` (JSON-RPC)
  - ``initialize``: MCP handshake; returns protocol version, server info, capabilities.
  - ``tools/list``: returns tools with JSON Schema input definitions.
  - ``tools/call``: invokes a tool by ``name`` with ``arguments``.
  - ``listTools``: returns the enriched capabilities manifest and a flattened tools list
    (includes domain, args_schema, example_args, options, positionals, description).
  - ``callTool``: dispatches to ``/cli/run`` (sync or async). Sync failures map to
    JSON-RPC error ``-32000`` with details in ``error.data``.
  - ``statusReport``: returns ``{ status: 'ok', version }`` mapped from ``/health``.

- ``GET /mcp/progress/{job_id}`` (SSE)
  - Emits JSON events (``data: {...}\n\n``) with ``job_id``, ``status``, ``exit_code``, ``output_file``
    until terminal status or ``max_ms`` timeout.

Notes
- Request body size limits can be enforced via ``ZYRA_MCP_MAX_BODY_BYTES``.
- Structured logs for MCP calls are emitted via the ``zyra.api.mcp`` logger.
"""

from __future__ import annotations

import logging
from contextlib import suppress
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from zyra.api import __version__ as dvh_version
from zyra.api.models.cli_request import CLIRunRequest
from zyra.api.routers.cli import get_cli_matrix, run_cli_endpoint
from zyra.api.routers.search import post_search as _post_search
from zyra.api.routers.search import search as _get_search
from zyra.api.services import manifest as manifest_svc
from zyra.api.utils.obs import log_mcp_call
from zyra.api.workers import jobs as jobs_backend
from zyra.utils.env import env_int

router = APIRouter(tags=["mcp"])

# MCP protocol version advertised by initialize() per MCP spec
PROTOCOL_VERSION = "2025-06-18"


class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: dict[str, Any] | None = None
    id: Any | None = None


def _rpc_error(
    id_val: Any, code: int, message: str, data: Any | None = None
) -> dict[str, Any]:
    err: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": id_val, "error": err}


def _rpc_result(id_val: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_val, "result": result}


@router.post("/mcp")
def mcp_rpc(req: JSONRPCRequest, request: Request, bg: BackgroundTasks):
    """Handle a JSON-RPC 2.0 request for MCP methods.

    Methods:
    - listTools: optional { refresh: bool } — ALIAS of ``tools/list`` returning ``{ tools: [...] }``.
    - callTool: { stage: str, command: str, args?: dict, mode?: 'sync'|'async' }.
      Sync failures return JSON-RPC error ``-32000``.
    - statusReport: returns MCP-ready service status and version.

    Design:
    - Avoid tool-specific fast paths; always delegate to the canonical CLI
      execution path (``/cli/run``) so behavior remains consistent and future
      changes to commands are reflected uniformly without bespoke logic here.
    """
    # Optional size limit from env (bytes). When set to >0, enforce via Content-Length.
    try:
        max_bytes = int(env_int("MCP_MAX_BODY_BYTES", 0))
    except (ValueError, TypeError):
        max_bytes = 0
    except Exception as exc:  # pragma: no cover - unexpected config/state
        # Log unexpected exceptions rather than silently masking all errors
        with suppress(Exception):
            logging.getLogger("zyra.api.mcp").warning(
                "Failed to parse MCP_MAX_BODY_BYTES: %s", exc
            )
        max_bytes = 0
    # Cache id early to avoid implicit outer-scope dependencies in helpers
    id_val = req.id

    if max_bytes and max_bytes > 0:
        try:
            cl = int(request.headers.get("content-length") or 0)
        except Exception:
            cl = 0
        if cl and cl > max_bytes:
            return _rpc_error(
                id_val,
                -32001,
                f"Request too large: {cl} bytes (limit {max_bytes})",
            )

    if req.jsonrpc != "2.0":  # Basic protocol check
        return _rpc_error(id_val, -32600, "Invalid Request: jsonrpc must be '2.0'")

    method = (req.method or "").strip()
    params = req.params or {}

    import time as _time

    _t0 = _time.time()

    # Helpers to respect JSON-RPC notifications (no response when id is None).
    # Explicitly capture id_val (not the req model) to limit implicit deps.
    def _ok(payload: Any) -> Any:
        return (
            Response(status_code=204)
            if id_val is None
            else _rpc_result(id_val, payload)
        )

    def _err(code: int, message: str, data: Any | None = None) -> Any:
        return (
            Response(status_code=204)
            if id_val is None
            else _rpc_error(id_val, code, message, data)
        )

    try:
        if method == "listTools":
            # Alias of namespaced tools/list
            refresh = bool(params.get("refresh", False))
            tools = _mcp_tools_list(refresh=refresh)
            with suppress(Exception):
                log_mcp_call(method, params, _t0, status="ok")
            return _ok({"tools": tools})

        # MCP initialize handshake
        if method == "initialize":
            # Per MCP spec, capabilities should be structured (not bare booleans).
            # Advertise tools with listChanged support, allowing clients to
            # subscribe to changes in tool listings.
            result = {
                "protocolVersion": PROTOCOL_VERSION,
                "serverInfo": {"name": "zyra", "version": dvh_version},
                "capabilities": {"tools": {"listChanged": True}},
            }
            with suppress(Exception):
                log_mcp_call(method, params, _t0, status="ok")
            return _ok(result)

        if method in {"statusReport", "status/report"}:
            # Lightweight mapping of /health
            return _ok({"status": "ok", "version": dvh_version})

        # MCP tools/list (namespaced)
        if method == "tools/list":
            refresh = bool(params.get("refresh", False))
            tools = _mcp_tools_list(refresh=refresh)
            with suppress(Exception):
                log_mcp_call(method, params, _t0, status="ok")
            return _ok({"tools": tools})

        # MCP prompts and resources (minimal stubs for compliance)
        if method == "prompts/list":
            with suppress(Exception):
                log_mcp_call(method, params, _t0, status="ok")
            return _ok({"prompts": []})

        if method == "resources/list":
            with suppress(Exception):
                log_mcp_call(method, params, _t0, status="ok")
            return _ok({"resources": []})

        if method == "resources/subscribe":
            # Accept and acknowledge subscription; no live events yet
            with suppress(Exception):
                log_mcp_call(method, params, _t0, status="ok")
            return _ok({"ok": True})

        if method in {"callTool", "tools/call"}:
            # Accept both legacy shape (stage/command/args) and MCP shape (name/arguments)
            name = params.get("name")
            arguments = params.get("arguments", {}) or {}
            stage = params.get("stage")
            command = params.get("command")
            args = params.get("args", {}) or {}
            mode = params.get("mode") or "sync"

            # Allow a couple of graceful aliases observed in some clients
            try:
                nm = str(name or "").strip().lower()
                if nm in {"zsearch-queryrequest", "zsearch_queryrequest"}:
                    name = "search-query"
                elif nm in {"zsearch-semanticrequest", "zsearch_semanticrequest"}:
                    name = "search-semantic"
            except Exception:
                pass

            # MCP-only tools: search-query and search-semantic
            if name in {"search-query", "search-semantic"}:
                q = arguments.get("query") or args.get("query")
                if not isinstance(q, str) or not q.strip():
                    return _err(-32602, "Invalid params: missing 'query'")
                try:
                    limit = int(arguments.get("limit", args.get("limit", 10)))
                except Exception:
                    limit = 10
                profile = arguments.get("profile", args.get("profile"))
                profile_file = arguments.get("profile_file", args.get("profile_file"))
                include_local = bool(
                    arguments.get("include_local", args.get("include_local", False))
                )
                remote_only = bool(
                    arguments.get("remote_only", args.get("remote_only", False))
                )
                ogc_wms = arguments.get("ogc_wms", args.get("ogc_wms"))
                ogc_records = arguments.get("ogc_records", args.get("ogc_records"))
                offline = bool(arguments.get("offline", args.get("offline", False)))
                https_only = bool(
                    arguments.get("https_only", args.get("https_only", False))
                )
                # Optional: include a compact markdown table in text content
                want_table = bool(arguments.get("table", args.get("table", False)))
                if name == "search-query":
                    try:
                        items = _get_search(
                            q=q,
                            limit=limit,
                            catalog_file=None,
                            profile=str(profile) if profile else None,
                            profile_file=str(profile_file) if profile_file else None,
                            ogc_wms=str(ogc_wms) if ogc_wms else None,
                            ogc_records=str(ogc_records) if ogc_records else None,
                            remote_only=bool(remote_only),
                            include_local=bool(include_local),
                            enrich=None,
                            enrich_timeout=3.0,
                            enrich_workers=4,
                            cache_ttl=86400,
                            offline=bool(offline),
                            https_only=bool(https_only),
                            allow_hosts=None,
                            deny_hosts=None,
                            max_probe_bytes=None,
                        )
                        # Return MCP-friendly content so IDE clients display results
                        try:
                            n = len(items) if isinstance(items, list) else 0
                            lines: list[str] = [
                                f"Search query '{q}' returned {n} item(s).",
                            ]
                            if isinstance(items, list) and items:
                                for it in items[: min(10, limit)]:
                                    if not isinstance(it, dict):
                                        continue
                                    title = str(
                                        it.get("title")
                                        or it.get("name")
                                        or it.get("id")
                                        or "Untitled"
                                    )
                                    url = (
                                        it.get("url")
                                        or it.get("href")
                                        or it.get("link")
                                        or it.get("uri")
                                    )
                                    if url:
                                        lines.append(f"- {title} — {url}")
                                    else:
                                        lines.append(f"- {title}")
                            # Optional markdown table for nicer rendering
                            if want_table and isinstance(items, list) and items:
                                rows: list[str] = [
                                    "",
                                    "| Name | Link |",
                                    "| --- | --- |",
                                ]
                                for it in items[: min(10, limit)]:
                                    if not isinstance(it, dict):
                                        continue
                                    title = str(
                                        it.get("title")
                                        or it.get("name")
                                        or it.get("id")
                                        or "Untitled"
                                    ).replace("|", " ")
                                    url = (
                                        it.get("url")
                                        or it.get("href")
                                        or it.get("link")
                                        or it.get("uri")
                                        or ""
                                    )
                                    rows.append(f"| {title} | {url} |")
                                lines.extend(rows)
                            summary = "\n".join(lines)
                        except Exception:
                            summary = f"Search query '{q}' returned results."

                        payload = {
                            # Text-only content for broad MCP client compatibility
                            "content": [{"type": "text", "text": summary}],
                            # Preserve machine-readable items for clients that use result fields
                            "items": items,
                        }
                        return _ok(payload)
                    except HTTPException as he:
                        return _err(
                            int(getattr(he, "status_code", 400) or 400),
                            "Invalid request",
                        )
                    except Exception:
                        return _err(-32603, "Internal error")
                else:
                    # search-semantic: leverage POST /search with analyze=true
                    try:
                        body = {"query": q, "limit": limit, "analyze": True}
                        if profile:
                            body["profile"] = str(profile)
                        if profile_file:
                            body["profile_file"] = str(profile_file)
                        if include_local:
                            body["include_local"] = True
                        if remote_only:
                            body["remote_only"] = True
                        if ogc_wms:
                            body["ogc_wms"] = str(ogc_wms)
                        if ogc_records:
                            body["ogc_records"] = str(ogc_records)
                        if offline:
                            body["offline"] = True
                        if https_only:
                            body["https_only"] = True
                        res = _post_search(body)

                        # Wrap in MCP text content for IDE visibility (avoid unsupported types)
                        try:
                            items = res.get("items") if isinstance(res, dict) else None
                            n = len(items) if isinstance(items, list) else None
                            lines: list[str] = [
                                f"Semantic search for '{q}' returned {n if n is not None else 'some'} item(s).",
                            ]
                            if isinstance(items, list) and items:
                                for it in items[: min(10, limit)]:
                                    if not isinstance(it, dict):
                                        continue
                                    title = str(
                                        it.get("title")
                                        or it.get("name")
                                        or it.get("id")
                                        or "Untitled"
                                    )
                                    url = (
                                        it.get("url")
                                        or it.get("href")
                                        or it.get("link")
                                        or it.get("uri")
                                    )
                                    if url:
                                        lines.append(f"- {title} — {url}")
                                    else:
                                        lines.append(f"- {title}")
                            # Optional markdown table for nicer rendering
                            if want_table and isinstance(items, list) and items:
                                rows: list[str] = [
                                    "",
                                    "| Name | Link |",
                                    "| --- | --- |",
                                ]
                                for it in items[: min(10, limit)]:
                                    if not isinstance(it, dict):
                                        continue
                                    title = str(
                                        it.get("title")
                                        or it.get("name")
                                        or it.get("id")
                                        or "Untitled"
                                    ).replace("|", " ")
                                    url = (
                                        it.get("url")
                                        or it.get("href")
                                        or it.get("link")
                                        or it.get("uri")
                                        or ""
                                    )
                                    rows.append(f"| {title} | {url} |")
                                lines.extend(rows)
                            summary = "\n".join(lines)
                        except Exception:
                            summary = f"Semantic search for '{q}' returned results."

                        payload: dict[str, Any] = {
                            # Text-only content for compatibility
                            "content": [{"type": "text", "text": summary}],
                        }
                        if isinstance(res, dict):
                            # Include original fields for compatibility
                            for k, v in res.items():
                                if k == "content":
                                    continue
                                payload[k] = v
                        else:
                            payload["data"] = res
                        return _ok(payload)
                    except HTTPException as he:
                        return _err(
                            int(getattr(he, "status_code", 400) or 400),
                            "Invalid request",
                        )
                    except Exception:
                        return _err(-32603, "Internal error")

            if name and (not stage or not command):
                # Parse name like "stage.tool" or "stage tool"
                n = str(name)
                if "." in n:
                    stage, command = n.split(".", 1)
                elif " " in n:
                    stage, command = n.split(" ", 1)
                elif ":" in n:
                    stage, command = n.split(":", 1)
                elif "-" in n:
                    # Try split on first dash only when the prefix matches a known stage
                    try:
                        matrix = get_cli_matrix()
                        prefix, rest = n.split("-", 1)
                        if prefix in matrix:
                            stage, command = prefix, rest
                    except Exception:
                        pass
                else:
                    stage, command = n, n
                # Prefer MCP 'arguments' over legacy 'args' if provided
                if arguments:
                    args = arguments

            # Validate against the CLI matrix for clearer errors
            matrix = get_cli_matrix()
            if stage not in matrix:
                return _rpc_error(
                    req.id,
                    -32602,
                    f"Invalid params: unknown stage '{stage}'",
                    {"allowed_stages": sorted(list(matrix.keys()))},
                )
            allowed = set(matrix[stage].get("commands", []) or [])
            if command not in allowed:
                return _rpc_error(
                    req.id,
                    -32602,
                    f"Invalid params: unknown command '{command}' for stage '{stage}'",
                    {"allowed_commands": sorted(list(allowed))},
                )

            # Delegate to existing /cli/run implementation
            req_model = CLIRunRequest(
                stage=stage, command=command, mode=mode, args=args
            )
            resp = run_cli_endpoint(req_model, bg)
            if getattr(resp, "job_id", None):
                # Async accepted; provide polling URL to align with progress semantics
                payload = {
                    "status": "accepted",
                    "job_id": resp.job_id,
                    "poll": f"/jobs/{resp.job_id}",
                    "ws": f"/ws/jobs/{resp.job_id}",
                    "download": f"/jobs/{resp.job_id}/download",
                    "manifest": f"/jobs/{resp.job_id}/manifest",
                }
                # Include a small text content hint for MCP UIs
                with suppress(Exception):
                    payload["content"] = [
                        {
                            "type": "text",
                            "text": (
                                f"Job accepted: {resp.job_id}. "
                                f"Poll {payload['poll']} or subscribe {payload['ws']}."
                            ),
                        }
                    ]
                return _ok(payload)
            # Sync execution result: map failures to JSON-RPC error
            exit_code = getattr(resp, "exit_code", None)
            if isinstance(exit_code, int) and exit_code != 0:
                out = _err(
                    -32000,
                    "Execution failed",
                    {
                        "exit_code": exit_code,
                        "stderr": getattr(resp, "stderr", None),
                        "stdout": getattr(resp, "stdout", None),
                        "stage": stage,
                        "command": command,
                    },
                )
                with suppress(Exception):
                    log_mcp_call(method, params, _t0, status="error", error_code=-32000)
                return out

            # Build MCP-friendly text content so IDE clients surface results
            def _content_from_stdio(
                _out: str | None, _err: str | None
            ) -> list[dict[str, str]]:
                try:
                    text = (_out or "").strip()
                    if not text and _err:
                        text = "stderr:\n" + _err.strip()
                    # Truncate overly long content to keep frames reasonable
                    if len(text) > 8000:
                        text = text[:8000] + "\n… (truncated)"
                    return [{"type": "text", "text": text}] if text else []
                except Exception:
                    return []

            out = _ok(
                {
                    "status": "ok",
                    "stdout": getattr(resp, "stdout", None),
                    "stderr": getattr(resp, "stderr", None),
                    "exit_code": exit_code,
                    "content": _content_from_stdio(
                        getattr(resp, "stdout", None), getattr(resp, "stderr", None)
                    ),
                }
            )
            with suppress(Exception):
                log_mcp_call(method, params, _t0, status="ok")
            return out

        # Method not found (avoid echoing arbitrary method names verbatim)
        return _err(-32601, "Method not found")
    except HTTPException as he:  # Map FastAPI errors to JSON-RPC error
        # Do not leak internal exception details to clients
        code = int(getattr(he, "status_code", 500) or 500)
        msg = "Invalid request" if 400 <= code < 500 else "Server error"
        out = _err(code, msg)
        with suppress(Exception):
            log_mcp_call(method, params, _t0, status="error", error_code=he.status_code)
        return out
    except Exception:
        # Log full exception internally; return a generic error to clients
        with suppress(Exception):
            logging.getLogger("zyra.api.mcp").exception(
                "Unhandled MCP exception for method %s", method
            )
        out = _err(-32603, "Internal error")
        with suppress(Exception):
            log_mcp_call(method, params, _t0, status="error", error_code=-32603)
        return out


def _sse_format(data: dict) -> bytes:
    import json as _json

    return ("data: " + _json.dumps(data) + "\n\n").encode("utf-8")


def _json_type(t: str | None) -> str | None:
    if not t:
        return None
    t = t.lower()
    if t in {"str", "string"}:
        return "string"
    if t in {"int", "integer"}:
        return "integer"
    if t in {"float", "number"}:
        return "number"
    if t in {"bool", "boolean"}:
        return "boolean"
    return None


def _search_args_schema() -> dict[str, Any]:
    """Return JSON Schema for MCP search tool arguments.

    Includes standard query/limit plus profile and filtering flags supported by
    the handlers in tools/call for search-query and search-semantic.
    """
    return {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "limit": {
                "type": "integer",
                "description": "Max results",
                "minimum": 1,
                "maximum": 100,
            },
            # Presentation
            "table": {
                "type": "boolean",
                "description": "Include a compact markdown table in text content",
            },
            # Profiles and configuration
            "profile": {
                "type": "string",
                "description": "Search profile name (e.g., 'default')",
            },
            "profile_file": {
                "type": "string",
                "description": "Path to a profile JSON file",
            },
            # Source selection
            "include_local": {
                "type": "boolean",
                "description": "Include local catalog assets",
            },
            "remote_only": {
                "type": "boolean",
                "description": "Restrict to remote results only",
            },
            # Protocol filters
            "ogc_wms": {
                "type": "string",
                "description": "Restrict to, or prioritize, a specific OGC WMS endpoint",
            },
            "ogc_records": {
                "type": "string",
                "description": "Restrict to, or prioritize, a specific OGC Records endpoint",
            },
            # Network and security
            "offline": {
                "type": "boolean",
                "description": "Avoid network requests (use cache/local only)",
            },
            "https_only": {
                "type": "boolean",
                "description": "Filter results to HTTPS URLs only",
            },
        },
        "required": ["query"],
    }


def _mcp_discovery_payload(refresh: bool = False) -> dict[str, Any]:
    """Return a spec-compatible MCP discovery payload.

    Structure:
    {
      "mcp_version": "0.1",
      "name": "zyra",
      "description": "...",
      "capabilities": { "commands": [ { name, description, parameters } ] }
    }
    """
    result = manifest_svc.list_commands(
        format="json", stage=None, q=None, refresh=refresh
    )
    cmds = result.get("commands", {}) if isinstance(result, dict) else {}
    commands: list[dict[str, Any]] = []
    for full, meta in cmds.items():
        # Build name as stage.tool (e.g., "process.decode-grib2")
        try:
            stage, tool = full.split(" ", 1)
        except ValueError:
            stage, tool = full, full
        # Normalize name for MCP clients (dashes, not dots)
        name = f"{stage}-{tool}"

        # Build JSON Schema parameters from options + positionals
        properties: dict[str, Any] = {}
        required: list[str] = []

        # Positionals: add as required named properties
        for pos in meta.get("positionals") or []:
            if not isinstance(pos, dict):
                continue
            pname = str(pos.get("name") or "arg").strip()
            if not pname:
                continue
            ptype = _json_type(str(pos.get("type") or ""))
            schema: dict[str, Any] = {}
            if ptype:
                schema["type"] = ptype
            if pos.get("choices"):
                schema["enum"] = list(pos.get("choices"))
            if pos.get("help"):
                schema["description"] = pos.get("help")
            properties[pname] = schema or {"type": "string"}
            if bool(pos.get("required", False)):
                required.append(pname)

        # Options: prefer long flags ("--flag"), convert to property names
        opts = meta.get("options") or {}
        seen: set[str] = set()
        for flag, o in opts.items():
            if not isinstance(flag, str) or not flag.startswith("--"):
                continue
            prop = flag.lstrip("-").replace("-", "_")
            if prop in seen:
                continue
            seen.add(prop)
            if not isinstance(o, dict):
                properties[prop] = {"type": "string"}
                continue
            jtype = _json_type(str(o.get("type") or ""))
            schema: dict[str, Any] = {}
            if jtype:
                schema["type"] = jtype
            if o.get("help"):
                schema["description"] = o.get("help")
            if o.get("choices"):
                from contextlib import suppress as _suppress

                with _suppress(Exception):
                    schema["enum"] = list(o.get("choices"))
            # We don't currently track required options; leave optional
            properties[prop] = schema or {"type": "string"}
            from contextlib import suppress as _suppress

            with _suppress(Exception):
                if bool(o.get("required")):
                    required.append(prop)

        parameters: dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }
        if required:
            parameters["required"] = sorted(required)

        commands.append(
            {
                "name": name,
                "description": meta.get("description", f"zyra {full}"),
                "parameters": parameters,
            }
        )

    # Append MCP-only helpers (search)
    search_schema = _search_args_schema()
    commands.append(
        {
            "name": "search-query",
            "description": "Search datasets (standard query)",
            "parameters": search_schema,
        }
    )
    commands.append(
        {
            "name": "search-semantic",
            "description": "Semantic search (LLM-assisted planning)",
            "parameters": search_schema,
        }
    )

    return {
        "mcp_version": "0.1",
        "name": "zyra",
        "description": "Zyra MCP server for domain-specific data visualization",
        "capabilities": {"commands": commands},
    }


def _mcp_tools_list(refresh: bool = False) -> list[dict[str, Any]]:
    """Return tools in MCP namespaced shape.

    Each tool item: { name, description, inputSchema }
    """
    result = manifest_svc.list_commands(
        format="json", stage=None, q=None, refresh=refresh
    )
    cmds = result.get("commands", {}) if isinstance(result, dict) else {}
    tools: list[dict[str, Any]] = []
    for full, meta in cmds.items():
        try:
            stage, tool = full.split(" ", 1)
        except ValueError:
            stage, tool = full, full
        # Normalize tool name to MCP-friendly pattern: replace dots with dashes
        # Example: "process.decode-grib2" -> "process-decode-grib2"
        name = f"{stage}-{tool}"

        # Build JSON Schema parameters from options + positionals
        properties: dict[str, Any] = {}
        required: list[str] = []

        for pos in meta.get("positionals") or []:
            if not isinstance(pos, dict):
                continue
            pname = str(pos.get("name") or "arg").strip()
            if not pname:
                continue
            ptype = _json_type(str(pos.get("type") or ""))
            schema: dict[str, Any] = {}
            if ptype:
                schema["type"] = ptype
            if pos.get("choices"):
                schema["enum"] = list(pos.get("choices"))
            if pos.get("help"):
                schema["description"] = pos.get("help")
            properties[pname] = schema or {"type": "string"}
            if bool(pos.get("required", False)):
                required.append(pname)

        opts = meta.get("options") or {}
        seen: set[str] = set()
        for flag, o in opts.items():
            if not isinstance(flag, str) or not flag.startswith("--"):
                continue
            prop = flag.lstrip("-").replace("-", "_")
            if prop in seen:
                continue
            seen.add(prop)
            if not isinstance(o, dict):
                properties[prop] = {"type": "string"}
                continue
            jtype = _json_type(str(o.get("type") or ""))
            schema: dict[str, Any] = {}
            if jtype:
                schema["type"] = jtype
            if o.get("help"):
                schema["description"] = o.get("help")
            if o.get("choices"):
                from contextlib import suppress as _suppress

                with _suppress(Exception):
                    schema["enum"] = list(o.get("choices"))
            properties[prop] = schema or {"type": "string"}
            from contextlib import suppress as _suppress

            with _suppress(Exception):
                if bool(o.get("required")):
                    required.append(prop)

        input_schema: dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            input_schema["required"] = sorted(required)

        tools.append(
            {
                "name": name,
                "description": meta.get("description", f"zyra {full}"),
                "inputSchema": input_schema,
            }
        )

    # Append MCP-only search tools
    basic_search_schema = _search_args_schema()
    tools.append(
        {
            "name": "search-query",
            "description": "Search datasets (standard query)",
            "inputSchema": basic_search_schema,
        }
    )
    tools.append(
        {
            "name": "search-semantic",
            "description": "Semantic search (LLM-assisted planning)",
            "inputSchema": basic_search_schema,
        }
    )

    return tools


@router.get("/mcp")
def mcp_capabilities(refresh: bool = False) -> dict[str, Any]:
    """HTTP discovery endpoint for MCP clients (Cursor/Claude/VS Code)."""
    return _mcp_discovery_payload(refresh=refresh)


@router.options("/mcp")
def mcp_capabilities_options(refresh: bool = False) -> dict[str, Any]:
    """OPTIONS variant returning the same MCP discovery payload."""
    return _mcp_discovery_payload(refresh=refresh)


@router.get("/mcp/progress/{job_id}")
def mcp_progress(job_id: str, interval_ms: int = 200, max_ms: int = 10000):
    """Server-Sent Events (SSE) stream of job status for MCP clients.

    Emits JSON events on each tick with ``job_id``, ``status``, ``exit_code``,
    and ``output_file`` until terminal status (``succeeded``|``failed``|``canceled``)
    or ``max_ms`` timeout.
    """

    async def _gen():
        import asyncio as _asyncio
        import time as _time

        deadline = _time.time() + max(0.0, float(max_ms) / 1000.0)
        while True:
            rec = jobs_backend.get_job(job_id) or {}
            status = rec.get("status", "unknown")
            payload = {
                "job_id": job_id,
                "status": status,
                "exit_code": rec.get("exit_code"),
                "output_file": rec.get("output_file"),
            }
            # Always emit an event to avoid client hangs
            yield _sse_format(payload)
            if status in {"succeeded", "failed", "canceled"}:
                break
            if _time.time() >= deadline:
                break
            await _asyncio.sleep(max(0.0, float(interval_ms) / 1000.0))

    return StreamingResponse(_gen(), media_type="text/event-stream")
