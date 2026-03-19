#!/usr/bin/env python3
"""
API Client — DeepResearch Agent.
SSE streaming client for the hix workflow API protocol.
  POST /api/hix/chat        — send message, stream SSE events
  POST /api/hix/agentEvent  — resume SSE stream after disconnect
  Auth : session-based via chatId (from hixChat.createChat)
"""
import json
import urllib.request
from typing import Any, Dict, Iterator, Optional

BASE_URL = "https://api.your-platform-domain.com"


def create_chat(title: str, bot_id: int, agent_type: str = "",
                extra_data: Optional[Dict] = None) -> Dict[str, Any]:
    """Call hixChat.createChat (tRPC) to create a new chat session.
    Returns: {"id": chatId, "title": str, "answer": str, "relatedQuestions": list}
    Raises : Exception on network or HTTP error.
    """
    payload = {
        "title": title,
        "botId": bot_id,
        "agentType": agent_type,
        "extraData": extra_data or {},
    }
    body = json.dumps(payload).encode()
    url = f"{BASE_URL}/api/trpc/hixChat.createChat"
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def stream_events(url: str, payload: Dict) -> Iterator[Dict]:
    """POST to an SSE endpoint and yield parsed events.
    Yields: {"type": str, "data": Any, "id": str|None}
    Terminal: {"type": "[DONE]"}
    """
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=300) as resp:
        event_type = None
        event_id   = None
        for line in resp:
            line = line.decode("utf-8").rstrip("\n")
            if not line or line.startswith(":"):
                continue
            if line.startswith("event: "):
                event_type = line[7:].strip()
            elif line.startswith("id: "):
                event_id = line[4:].strip()
            elif line.startswith("data: "):
                raw = line[6:].strip()
                if raw == "[DONE]":
                    yield {"type": "[DONE]", "data": None, "id": event_id}
                    break
                try:
                    data_obj = json.loads(raw)
                except json.JSONDecodeError:
                    data_obj = raw
                yield {"type": event_type or "[data]", "data": data_obj, "id": event_id}
                event_type = None
                event_id   = None


def stream_chat(chat_id: str, question: str,
                markdown: Optional[str] = None,
                file_urls: Optional[list] = None,
                search: bool = False,
                search_type: Optional[str] = None,
                agent_type: Optional[str] = None,
                extra_data: Optional[Dict] = None,
                is_similar_style: bool = False,
                parent_id: Optional[int] = None,
                parent_question_id: Optional[int] = None,
                ) -> Iterator[Dict]:
    """POST /api/hix/chat — send message, receive SSE stream."""
    payload = {
        "chatId":    chat_id,
        "question":  question,
        "agentType": agent_type or "",
        "extraData": extra_data  or {},
    }
    if markdown:               payload["markdown"]            = markdown
    if file_urls:              payload["fileUrls"]            = list(file_urls)
    if search:                 payload["search"]              = search
    if search_type:            payload["searchType"]          = search_type
    if is_similar_style:       payload["isSimilarStyle"]      = is_similar_style
    if parent_id is not None:  payload["parentId"]            = parent_id
    if parent_question_id is not None:
                               payload["parentQuestionId"]    = parent_question_id
    yield from stream_events(f"{BASE_URL}/api/hix/chat", payload)


def reconnect(chat_id: str, detail_id: int,
              last_cursor: Optional[str] = None) -> Iterator[Dict]:
    """POST /api/hix/agentEvent — resume SSE stream after disconnect."""
    payload = {"chatId": chat_id, "detailId": detail_id}
    if last_cursor:
        payload["lastCursor"] = last_cursor
    yield from stream_events(f"{BASE_URL}/api/hix/agentEvent", payload)


def verify_key(chat_id: str) -> bool:
    """Session liveness check — chatId proves identity."""
    try:
        for _ in stream_chat(chat_id, "ping"):
            pass
        return True
    except Exception:
        return False


def check_balance(chat_id: str) -> Dict:
    """Balance / quota managed by platform per chatId."""
    return {"status": "ok", "message": "Balance managed per session", "chatId": chat_id}


def run_loop(chat_id: str, question: str,
             agent_type: str = "",
             extra_data: Optional[Dict] = None):
    """Drive SSE event loop, yielding step payloads. Stops on [DONE]."""
    for ev in stream_chat(chat_id, question, agent_type=agent_type,
                          extra_data=extra_data):
        t = ev["type"]
        d = ev["data"]
        if t in ("2002", "CHAT_ANSWER"):
            continue
        if t == "WorkflowStarted":
            print(f"[EVENT] WorkflowStarted: {d}")
        elif t == "StepOutput":
            print(f"[EVENT] StepOutput: {d}")
            yield d
        elif t == "CustomEnd":
            print(f"[EVENT] CustomEnd: {d}")
            yield d
        elif t == "[DONE]":
            break
        elif d is not None:
            print(f"[EVENT] {t}: {d}")
            yield d
