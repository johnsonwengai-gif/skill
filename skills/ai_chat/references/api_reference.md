---

# API Reference — AI Chat (Multi-Modal General Orchestration Agent)

> Complete API integration specification for the General Agent protocol. All behavior is driven by SSE events received from the backend.

---

## API Architecture Overview

AI Chat uses the **General Agent SSE protocol** — distinct from the sub-agent streaming protocol.

```
1. hixChat.createChat (tRPC)          → chatId
2. generalAgent.sendMessage (tRPC)     → run_id
3. GET /api/hix/generalAgent?chatId=… (SSE, GET)
       ←  RUN_STARTED / TEXT_MESSAGE_CONTENT / TOOL_CALL_* / RUN_FINISHED …
       ←  DONE / ERROR
Reconnect: add Last-Event-ID header
4. generalAgent.memoryList / memoryRead → download output files
5. generalAgent.getMessages            → history rehydration
```

> **Auth**: No API key header. Identity is established by `chatId` from `hixChat.createChat`. Returns 403 if the user has no permission on the `chatId`.

---

## Endpoints Summary

| Endpoint | Method | Protocol | Purpose |
|----------|--------|----------|---------|
| `/api/trpc/hixChat.createChat` | POST | tRPC | Create session → get `chatId` |
| `/api/trpc/hixChat.deleteChat` | POST | tRPC | Logical delete session |
| `/api/trpc/generalAgent.sendMessage` | POST | tRPC | Send message → get `run_id` |
| `/api/trpc/generalAgent.cancelTask` | POST | tRPC | Cancel active run |
| `/api/trpc/generalAgent.getSession` | POST | tRPC | Get session metadata |
| `/api/trpc/generalAgent.getMessages` | POST | tRPC | Get AG-UI format history |
| `/api/trpc/generalAgent.memoryList` | POST | tRPC | List output files |
| `/api/trpc/generalAgent.memoryRead` | POST | tRPC | Get pre-signed file URL |
| `/api/hix/generalAgent?chatId=…` | GET | SSE | Real-time event stream |
| `/api/hix/generalAgent/archive-download` | GET | HTTP | ZIP download of session files |

---

## tRPC — Create Session

### `hixChat.createChat`

**POST `/api/trpc/hixChat.createChat`**

```json
{
  "title":      "My multi-modal task",
  "botId":      0,
  "agentType":  "GENERAL_AGENT",
  "extraData":  {}
}
```

> Note: `agentType: "GENERAL_AGENT"` triggers extra concurrency / quota checks.

**Success response** (HTTP 200):
```json
{
  "id":                  "chat_xxxxx",
  "title":               "My multi-modal task",
  "answer":              "",
  "relatedQuestions":    []
}
```

**Error** (e.g. quota exceeded):
```json
{
  "error": {
    "code":    "TASK_LIMIT_EXCEEDED",
    "message": "..."
  }
}
```

---

## tRPC — Send Message

### `generalAgent.sendMessage`

**POST `/api/trpc/generalAgent.sendMessage`**

```json
{
  "chatId":  "chat_xxxxx",
  "message": {
    "role":    "user",
    "content": [
      {"type": "text",     "text": "Create a video about our Q1 report"},
      {"type": "image_url","image_url": {"url": "https://..."}}
    ],
    "parentId": null
  }
}
```

**Success response**:
```json
{
  "status": "queued",
  "run_id": "run_abc123"
}
```

**Common errors**:

| Code | Meaning |
|------|---------|
| `TASK_LIMIT_EXCEEDED` | User concurrency limit exceeded |
| `RUN_ALREADY_ACTIVE` | A run is already in progress (`active_run_id` may be returned) |
| `INVALID_SESSION_STATE` | Frontend thinks it is resuming but server state is out of sync |

---

## tRPC — Cancel Task

### `generalAgent.cancelTask`

**POST `/api/trpc/generalAgent.cancelTask`**

```json
{"chatId": "chat_xxxxx"}
```

**Success**: `{"status": "cancelling"}`
**No active run**: `{"error": {"code": "NO_ACTIVE_RUN"}}`

---

## tRPC — Session & Message Introspection

### `generalAgent.getSession`

**POST `/api/trpc/generalAgent.getSession`**

```json
{"chatId": "chat_xxxxx"}
```

Returns: FastAPI `GET /api/sessions/{session_id}` JSON response.

---

### `generalAgent.getMessages`

**POST `/api/trpc/generalAgent.getMessages`**

```json
{"chatId": "chat_xxxxx", "last_n_runs": 3}
```

Returns FastAPI `GET /api/sessions/{session_id}/messages` (AG-UI format):
```json
{
  "is_active":    false,
  "active_run_id": null,
  "messages":     [...],
  "session_state": {}
}
```

Use this for history rehydration or checking whether a run is still active.

---

## tRPC — Memory / File System

### `generalAgent.memoryList`

**POST `/api/trpc/generalAgent.memoryList`**

```json
{"chatId": "chat_xxxxx"}
```

Returns:
```json
{
  "files": [
    {"path": "output/video_001.mp4", "size": 10485760, "last_modified": "2026-03-19T10:00:00Z"}
  ]
}
```

---

### `generalAgent.memoryRead`

**POST `/api/trpc/generalAgent.memoryRead`**

```json
{"chatId": "chat_xxxxx", "path": "output/video_001.mp4"}
```

Returns: `{"url": "https://..."}` — pre-signed short-lived download URL.

For shared files: use `shareId` instead of `chatId`.

---

## SSE — Real-Time Event Stream

### `GET /api/hix/generalAgent?chatId=…`

**GET** (no body; SSE via `Accept: text/event-stream`)

Supports `Last-Event-ID` request header for resumable streaming.

---

### SSE Frame Format

```
id: <cursor>
event: <event_type>
data: <json>
```

Terminal: `data: [DONE]` (server closes connection)

---

### SSE Event Types

#### Control Events

| Event | Meaning |
|-------|---------|
| `HEARTBEAT` | Keep-alive pulse |
| `DONE` | Task finished normally |
| `ERROR` | Task error occurred |

#### Worker / Run Events

| Event | `data` contains |
|-------|----------------|
| `RUN_STARTED` | `run_id` |
| `TEXT_MESSAGE_CONTENT` | `content` (incremental text) |
| `TOOL_CALL_START` | `tool`, `input` |
| `TOOL_CALL_END` | `tool`, `output` |
| `RUN_FINISHED` | `run_id`, summary |
| `PLAYBACK` | Hint: history may need refresh (Redis run was cleared before reconnect) |

#### Playback Handling

If the SSE stream sends a `PLAYBACK` event (server detected `is_active=true` in history but the Redis `active_run` was already cleared), the client should:

1. Call `generalAgent.getMessages({ chatId })` to refresh history
2. Yield a `PLAYBACK_HISTORY_REFRESH` event to the caller
3. Continue consuming the SSE stream

---

### Typical Event Sequence

```
RUN_STARTED           → run_id=run_abc123
TEXT_MESSAGE_CONTENT  → "Thinking about the request..."
TOOL_CALL_START       → {tool: "slide", input: {...}}
TOOL_CALL_END         → {tool: "slide", output: {...}}
TEXT_MESSAGE_CONTENT  → "Slide deck ready."
RUN_FINISHED          → {run_id: "run_abc123", summary: {...}}
DONE
```

---

## ZIP Archive Download

### `GET /api/hix/generalAgent/archive-download?session_id=…`

Returns `application/zip` stream — server proxies FastAPI's ZIP stream directly to browser.

Query params:
- `session_id` (or alias `chatId`): session identifier
- `filename`: optional suggested filename

---

## Recommended Call Chain

### New Session + Send + Stream + Retrieve Files

```
1. hixChat.createChat(
     title="multi-modal task",
     botId=0,
     agentType="GENERAL_AGENT"
   )  →  chatId

2. generalAgent.sendMessage(
     chatId=chatId,
     message={role:"user", content:[{type:"text", text:"..."}]}
   )  →  run_id

3. GET /api/hix/generalAgent?chatId=chatId   (SSE, GET)
   Process events: RUN_STARTED → TOOL_CALL_* → RUN_FINISHED → DONE

4. # Optional: refresh history
   generalAgent.getMessages(chatId)

5. # Optional: download output files
   generalAgent.memoryList(chatId)  →  files[]
   generalAgent.memoryRead(chatId, path="...")  →  pre-signed URL
```

### Resume After Disconnect

```
1. generalAgent.getMessages(chatId)  →  is_active, active_run_id
2. If is_active=true:
     → SSE stream is still alive; reconnect with Last-Event-ID
   If is_active=false but Redis run was cleared (PLAYBACK event):
     → Refresh history: generalAgent.getMessages(chatId)
3. Reconnect: GET /api/hix/generalAgent?chatId=…  (Last-Event-ID: <cursor>)
```

---

## Error Codes

| Code | Source | Meaning |
|------|--------|---------|
| `TASK_LIMIT_EXCEEDED` | sendMessage | User concurrency / quota exceeded |
| `RUN_ALREADY_ACTIVE` | sendMessage | A run is already running; `active_run_id` may be returned |
| `INVALID_SESSION_STATE` | sendMessage | Session state mismatch (resume vs server state) |
| `NO_ACTIVE_RUN` | cancelTask | No running task to cancel |
| 403 | All | User lacks permission on `chatId` |

---

## Quick Verification Checklist

- [ ] `hixChat.createChat` returned a valid `chatId`
- [ ] `generalAgent.sendMessage` returned `status: "queued"` with `run_id`
- [ ] SSE stream received `RUN_STARTED` event
- [ ] `TOOL_CALL_*` events correctly routed to sub-agents (image / video / slide / writer / research)
- [ ] `RUN_FINISHED` received before `DONE`
- [ ] `PLAYBACK` handled (if received): history refreshed
- [ ] Output files retrieved via `memoryList` / `memoryRead`
- [ ] `cancelTask` tested (optional)

---

## Capability Summary Table

| Capability | Supported | Notes |
|-----------|-----------|-------|
| Session creation (tRPC) | Yes | `hixChat.createChat` |
| Session deletion (tRPC) | Yes | `hixChat.deleteChat` |
| Send message (tRPC) | Yes | `generalAgent.sendMessage` |
| SSE real-time stream (GET) | Yes | `GET /api/hix/generalAgent` |
| Reconnect with Last-Event-ID | Yes | Resume from cursor |
| Playback hint handling | Yes | Refresh history if Redis run was cleared |
| Cancel active run | Yes | `generalAgent.cancelTask` |
| Session metadata | Yes | `generalAgent.getSession` |
| History / message fetch | Yes | `generalAgent.getMessages` |
| Memory file listing | Yes | `generalAgent.memoryList` |
| Memory file download | Yes | `generalAgent.memoryRead` (pre-signed URL) |
| ZIP archive download | Yes | `GET /archive-download` |
| Concurrency / quota checks | Yes | `TASK_LIMIT_EXCEEDED` on `sendMessage` |
| Multi-modal sub-agent routing | Yes | `TOOL_CALL_START/END` events |
| Credit tracking | Yes | Per `meta` in `StepOutput`-equivalent events |
