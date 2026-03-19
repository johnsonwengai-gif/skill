#!/usr/bin/env python3
"""
API Client — AI Chat (Multi-Modal General Orchestration Agent).
SSE streaming + tRPC client for the General Agent protocol.

Workflow:
  1. hixChat.createChat (tRPC)  →  chatId
  2. generalAgent.sendMessage (tRPC)  →  runId
  3. GET /api/hix/generalAgent?chatId=...  (SSE, GET, supports Last-Event-ID)
  4. generalAgent.memoryList / memoryRead  →  download output files
  5. generalAgent.getMessages  →  history rehydration

Auth: session-based via chatId (from hixChat.createChat).
"""
import json
import urllib.request
import urllib.error
from typing import Any, Dict, Iterator, Optional

BASE_URL = "https://api.your-platform-domain.com"

# ── tRPC helpers ──────────────────────────────────────────────────────────────

def trpc_call(path: str, payload: Dict) -> Dict[str, Any]:
    """Make a tRPC POST call. Returns parsed JSON response."""
    body = json.dumps(payload).encode()
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(
        url, data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def create_chat(title: str, bot_id: int, agent_type: str = "GENERAL_AGENT",
                extra_data: Optional[Dict] = None) -> Dict[str, Any]:
    """Call hixChat.createChat (tRPC) to create a new General Agent session.
    Returns: {"id": chatId, "title": str, "answer": str, "relatedQuestions": list}
    """
    return trpc_call("/api/trpc/hixChat.createChat", {
        "title":      title,
        "botId":      bot_id,
        "agentType":  agent_type,
        "extraData":  extra_data or {},
    })


def delete_chat(chat_id: str) -> Dict[str, Any]:
    """Call hixChat.deleteChat (tRPC). Logical delete (enable=false)."""
    return trpc_call("/api/trpc/hixChat.deleteChat", {"id": chat_id})


def send_message(chat_id: str, message: Dict) -> Dict[str, Any]:
    """Call generalAgent.sendMessage (tRPC).
    Sends a user/tool message to the General Agent.
    Returns: {"status": "queued", "run_id": string}
    Raises : RuntimeError on TASK_LIMIT_EXCEEDED / RUN_ALREADY_ACTIVE /
             INVALID_SESSION_STATE.
    """
    result = trpc_call("/api/trpc/generalAgent.sendMessage", {
        "chatId":  chat_id,
        "message": message,
    })
    status = result.get("status", "")
    if status != "queued":
        code  = result.get("error", {}).get("code", "UNKNOWN")
        msg   = result.get("error", {}).get("message", str(result))
        raise RuntimeError(f"[{code}] sendMessage failed: {msg}")
    return result


def cancel_task(chat_id: str) -> Dict[str, Any]:
    """Call generalAgent.cancelTask (tRPC). Cancels the active run."""
    return trpc_call("/api/trpc/generalAgent.cancelTask", {"chatId": chat_id})


def get_session(chat_id: str) -> Dict[str, Any]:
    """Call generalAgent.getSession (tRPC). Returns session metadata."""
    return trpc_call("/api/trpc/generalAgent.getSession", {"chatId": chat_id})


def get_messages(chat_id: str, last_n_runs: Optional[int] = None) -> Dict[str, Any]:
    """Call generalAgent.getMessages (tRPC).
    Returns AG-UI format messages; key fields: is_active, active_run_id, messages.
    """
    payload = {"chatId": chat_id}
    if last_n_runs is not None:
        payload["last_n_runs"] = last_n_runs
    return trpc_call("/api/trpc/generalAgent.getMessages", payload)


def memory_list(chat_id: str) -> Dict[str, Any]:
    """Call generalAgent.memoryList (tRPC).
    Returns: {"files": [{"path": str, "size": int, "last_modified": str}]}
    """
    return trpc_call("/api/trpc/generalAgent.memoryList", {"chatId": chat_id})


def memory_read(path: str, chat_id: Optional[str] = None,
                share_id: Optional[str] = None) -> Dict[str, Any]:
    """Call generalAgent.memoryRead (tRPC).
    Returns: {"url": string}  (pre-signed short-lived download URL)
    Pass chatId for own files, or shareId for shared files.
    """
    payload = {"path": path}
    if chat_id:  payload["chatId"]  = chat_id
    if share_id: payload["shareId"] = share_id
    return trpc_call("/api/trpc/generalAgent.memoryRead", payload)


def archive_download_url(chat_id: str, filename: Optional[str] = None) -> str:
    """Build the archive-download URL (GET, no auth header needed)."""
    url = f"{BASE_URL}/api/hix/generalAgent/archive-download?session_id={chat_id}"
    if filename:
        url += f"&filename={urllib.request.quote(filename)}"
    return url


# ── SSE event streaming ──────────────────────────────────────────────────────

def stream_sse_events(url: str,
                      last_event_id: Optional[str] = None) -> Iterator[Dict]:
    """POST to an SSE endpoint and yield parsed events.

    Yields dicts with keys:
      type : str  (event name, e.g. "RUN_STARTED", "TEXT_MESSAGE_CONTENT", "[DONE]")
      data : Any  (parsed JSON, or raw string on parse failure)
      id   : str  (event id / cursor, or None)

    Terminal events:
      "DONE"         → task finished normally
      "ERROR"        → task error
      "[DONE]"       → raw SSE terminator
    """
    headers = {"Accept": "text/event-stream"}
    if last_event_id:
        headers["Last-Event-ID"] = last_event_id

    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=300) as resp:
        event_type = None
        event_id   = None
        for line in resp:
            line = line.decode("utf-8").rstrip("\n")
            if not line or line.startswith(":"):
                continue
            if line.startswith("id: "):
                event_id = line[4:].strip()
            elif line.startswith("event: "):
                event_type = line[7:].strip()
            elif line.startswith("data: "):
                raw = line[6:].strip()
                # Terminal markers
                if raw == "[DONE]":
                    yield {"type": "[DONE]", "data": None, "id": event_id}
                    break
                try:
                    data_obj = json.loads(raw)
                except json.JSONDecodeError:
                    data_obj = raw
                yield {
                    "type": event_type or "[data]",
                    "data": data_obj,
                    "id":   event_id,
                }
                event_type = None
                event_id   = None


def stream_chat(chat_id: str,
                text: str = "",
                image_urls: Optional[list] = None,
                file_urls: Optional[list] = None,
                parent_id: Optional[int] = None,
                is_similar_style: bool = False,
                ) -> Iterator[Dict]:
    """
    Full General Agent streaming workflow:

      1. sendMessage (tRPC)  →  run_id
      2. GET /api/hix/generalAgent?chatId=...  (SSE)

    Yields SSE events with type + data.
    Handles playback hints (history refresh needed).
    """
    # Build AG-UI user message
    content_blocks = [{"type": "text", "text": text}]
    if image_urls:
        for img in image_urls:
            content_blocks.append({"type": "image_url", "image_url": {"url": img}})
    if file_urls:
        for f in file_urls:
            content_blocks.append({"type": "file", "file": {"url": f}})

    message = {
        "role":    "user",
        "content": content_blocks,
    }
    if parent_id is not None:
        message["parentId"] = parent_id

    # Step 1: send message → get run_id
    send_result = send_message(chat_id, message)
    run_id = send_result.get("run_id", "")
    if not run_id:
        raise RuntimeError("sendMessage returned no run_id")

    # Step 2: SSE stream
    sse_url = f"{BASE_URL}/api/hix/generalAgent?chatId={chat_id}"
    last_event_id = None
    for ev in stream_sse_events(sse_url, last_event_id=last_event_id):
        t = ev["type"]
        d = ev["data"]
        last_event_id = ev["id"] or last_event_id

        # Playback hint: is_active was true but Redis run was cleared
        if t == "PLAYBACK":
            print(f"[HINT] Playback: history may need refresh. {d}")
            # Trigger history refresh
            try:
                hist = get_messages(chat_id)
                yield {"type": "PLAYBACK_HISTORY_REFRESH", "data": hist, "id": last_event_id}
            except Exception as e:
                print(f"[WARN] Failed to refresh history: {e}")
            continue

        yield ev

    return run_id


def reconnect(chat_id: str, last_event_id: Optional[str] = None) -> Iterator[Dict]:
    """Resume SSE stream from last_event_id (GET /api/hix/generalAgent)."""
    yield from stream_sse_events(
        f"{BASE_URL}/api/hix/generalAgent?chatId={chat_id}",
        last_event_id=last_event_id,
    )


# ── Session helpers ──────────────────────────────────────────────────────────

def verify_session(chat_id: str) -> bool:
    """Session liveness check via getSession."""
    try:
        get_session(chat_id)
        return True
    except Exception:
        return False


# ── High-level orchestration loop ────────────────────────────────────────────

def run_loop(chat_id: str,
             text: str = "",
             image_urls: Optional[list] = None,
             file_urls: Optional[list] = None,
             is_similar_style: bool = False,
             ) -> Iterator[Dict]:
    """
    Drive the General Agent SSE event loop, yielding parsed payloads.

    Yields:
      RUN_STARTED           → workflow started
      TEXT_MESSAGE_CONTENT  → incremental text output
      TOOL_CALL_START       → sub-agent started
      TOOL_CALL_END         → sub-agent finished
      RUN_FINISHED          → run completed
      DONE                  → stream ended normally
      ERROR                 → error occurred
      PLAYBACK_HISTORY_REFRESH → session history refreshed
      Other events          → logged

    Returns run_id on completion.
    """
    last_event_id = None
    for ev in stream_chat(chat_id, text=text,
                          image_urls=image_urls,
                          file_urls=file_urls,
                          is_similar_style=is_similar_style):
        t = ev["type"]
        d = ev["data"]
        last_event_id = ev["id"] or last_event_id

        if t == "RUN_STARTED":
            run_id = (d or {}).get("run_id", "")
            print(f"[EVENT] RUN_STARTED: run_id={run_id}")
            yield {"type": "RUN_STARTED", "data": d, "run_id": run_id}

        elif t == "TEXT_MESSAGE_CONTENT":
            content = (d or {}).get("content", "") if isinstance(d, dict) else str(d)
            print(f"[TEXT] {content}", end="", flush=True)
            yield {"type": "TEXT_MESSAGE_CONTENT", "data": d}

        elif t == "TOOL_CALL_START":
            tool = (d or {}).get("tool", "unknown") if isinstance(d, dict) else str(d)
            print(f"\n[EVENT] TOOL_CALL_START: {tool}")
            yield {"type": "TOOL_CALL_START", "data": d}

        elif t == "TOOL_CALL_END":
            tool  = (d or {}).get("tool", "unknown") if isinstance(d, dict) else str(d)
            print(f"[EVENT] TOOL_CALL_END: {tool}")
            yield {"type": "TOOL_CALL_END", "data": d}

        elif t == "RUN_FINISHED":
            print(f"\n[EVENT] RUN_FINISHED: {d}")
            yield {"type": "RUN_FINISHED", "data": d}

        elif t == "DONE":
            print(f"\n[EVENT] DONE")
            break

        elif t == "ERROR":
            print(f"\n[EVENT] ERROR: {d}")
            yield {"type": "ERROR", "data": d}
            break

        elif t == "PLAYBACK_HISTORY_REFRESH":
            yield ev

        elif t == "[DONE]":
            break

        else:
            print(f"\n[EVENT] {t}: {str(d)[:200]}")
            yield {"type": t, "data": d}

    return last_event_id
