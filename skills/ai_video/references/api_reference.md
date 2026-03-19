---
# API Reference — AI Video Agent

> Complete API integration specification. All behavior is driven by the API response.

---

> Note: Video generation may take longer than typical API calls. Set timeout to at least 300 seconds (5 minutes).

---



## API Architecture

This agent uses the **SSE (Server-Sent Events)** streaming protocol.

```
Client  →  POST /api/trpc/hixChat.createChat  (tRPC, get chatId)
          →  POST /api/hix/chat  (SSE stream)
          ←  event: WorkflowStarted
          ←  event: StepOutput  (action, data, meta)
          ←  …
          ←  event: CustomEnd
          ←  data: [DONE]  (connection closed)
Reconnect →  POST /api/hix/agentEvent
```

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/trpc/hixChat.createChat` | POST (tRPC) | Create session, get `chatId` |
| `/api/hix/chat` | POST (SSE) | Send message, stream events |
| `/api/hix/agentEvent` | POST (SSE) | Resume stream after disconnect |

### Authentication

> No API key header required. Identity is established by the `chatId` returned from `hixChat.createChat`.
> The user must have permission on the `chatId` (403 if forbidden).

### tRPC — Create Session

**POST `/api/trpc/hixChat.createChat`**

Request body (JSON):
```json
{
  "title": "My task",
  "botId": 0,
  "agentType": "",
  "extraData": {}
}
```

Success response (HTTP 200):
```json
{
  "id": "chat_xxxxx",
  "title": "My task",
  "answer": "",
  "relatedQuestions": []
}
```

### POST /api/hix/chat — Send + Stream (SSE)

Request body (JSON):
```json
{
  "chatId": "chat_xxxxx",
  "question": "自然语言请求 / natural language request",
  "markdown": "",
  "parentId": null,
  "parentQuestionId": null,
  "fileUrls": [],
  "search": false,
  "searchType": "internet",
  "agentType": "",
  "extraData": {},
  "isSimilarStyle": false
}
```

### SSE Response Format

Each SSE frame:
```
id: <cursor>
event: <event_type>
data: <json>
```

Terminal: `data: [DONE]` (server closes connection)

### Key SSE Events

| Event | `data` contains |
|-------|----------------|
| `2001` / `CHAT_QUESTION` | `questionId: number` |
| `2002` / `CHAT_ANSWER` | `detailId: number` (needed for reconnect) |
| `WorkflowStarted` | Workflow metadata |
| `StepOutput` | Step result with `action`, `message`, `data`, `meta` |
| `CustomEnd` | Final output with all results |

### StepOutput — Primary Work Event

Most sub-agent results arrive as `StepOutput` events. The `data` field has this structure:

```json
{
  "action": "done",
  "message": "Generation complete.",
  "data": {
    "outputs": {},
    "steps_completed": 1,
    "total_credits_consumed": 5
  },
  "meta": {
    "credits_consumed": 5,
    "remaining_credits": 995,
    "credit_status": "ok"
  }
}
```

### Reconnect — POST /api/hix/agentEvent

```json
{
  "chatId": "chat_xxxxx",
  "detailId": 12345,
  "lastCursor": "cursor_string"
}
```


---
## Response — Action Types (from `StepOutput.data`)

### task_plan

```json
{
  "action": "task_plan",
  "message": "Task analyzed. Execution plan ready.",
  "data": {
    "task_type": "multi_step",
    "workflow": "short_clip",
    "steps": [
      {
        "step": 1,
        "agent": "video",
        "params": {
          "prompt": "<prompt>",
          "duration": 10,
          "resolution": "1080p",
          "aspect_ratio": "16:9"
        },
        "output_key": "video_clip"
      }
    ],
    "estimated_credits": 15,
    "estimated_time_seconds": 120
  }
}
```

### call_agent

```json
{
  "action": "call_agent",
  "message": "Calling video generation agent.",
  "data": {
    "agent": "video",
    "params": {
      "prompt": "<scene_description>",
      "duration": 10,
      "resolution": "1080p",
      "aspect_ratio": "16:9",
      "mode": "text2video",
      "first_frame": "<image_url_or_base64>",
      "last_frame": "<image_url_or_base64>",
      "reference_images": ["<url1>", "<url2>"]
    }
  },
  "meta": {
    "estimated_credits": 10,
    "estimated_time_seconds": 90
  }
}
```

### request_parameter

```json
{
  "action": "request_parameter",
  "message": "Additional parameters required.",
  "data": {
    "required_fields": [
      {"name": "prompt", "label": "Video Prompt", "type": "text", "required": true},
      {"name": "duration", "label": "Duration (seconds)", "type": "number", "min": 1, "max": 120, "required": true},
      {"name": "aspect_ratio", "label": "Aspect Ratio", "type": "select", "options": ["16:9", "9:16"], "required": true},
      {"name": "resolution", "label": "Resolution", "type": "select", "options": ["720p", "1080p"], "required": true},
      {"name": "first_frame", "label": "First Frame Image", "type": "text", "required": false},
      {"name": "last_frame", "label": "Last Frame Image", "type": "text", "required": false},
      {"name": "reference_images", "label": "Reference Images", "type": "text", "required": false}
    ]
  }
}
```

### wait_user_confirm

```json
{
  "action": "wait_user_confirm",
  "message": "Video generated. Review and confirm.",
  "data": {
    "preview": "<video_url_or_description>",
    "confirm_prompt": "Should I proceed? (yes/no/revise)",
    "cancel_prompt": "Say 'cancel' to abort."
  }
}
```

### done

```json
{
  "action": "done",
  "message": "Task completed.",
  "data": {
    "final_output": "<final_video_url>",
    "outputs": {
      "video_file": "<mp4_url>",
      "cover_image": "<jpg_url>",
      "keyframes": ["<url1>", "<url2>"]
    },
    "steps_completed": 2,
    "total_credits_consumed": 12,
    "remaining_credits": 988,
    "duration_seconds": 10,
    "resolution": "1080p"
  }
}
```

### credit_warning

```json
{
  "action": "credit_warning",
  "message": "Credits are running low.",
  "data": {
    "remaining_credits": 45,
    "estimated_credits_for_completion": 60,
    "purchase_url": "https://your-platform-domain.com/pricing"
  }
}
```

### credit_exhausted

```json
{
  "action": "credit_exhausted",
  "message": "Credits exhausted. Task paused.",
  "data": {
    "remaining_credits": 0,
    "partial_output": "<partial_results>",
    "purchase_url": "https://your-platform-domain.com/pricing"
  }
}
```

### error

```json
{
  "action": "error",
  "message": "An error occurred.",
  "data": {
    "code": "<ERROR_CODE>",
    "details": "<error_details>",
    "recoverable": false,
    "retry": false
  }
}
```

---

## Error Codes

| Code | HTTP | Description | Agent Action |
|------|------|-------------|--------------|
| `INVALID_API_KEY` | 401 | Key invalid or expired | Prompt registration |
| `CREDITS_EXHAUSTED` | 402 | No credits remaining | Stop, prompt purchase |
| `MISSING_PARAMETER` | 400 | Required field absent | Collect from user |
| `PARAM_REQUIRED_IN_RESPONSE` | 400 | API needs more params | Display to user, collect |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests | Wait, retry |
| `DURATION_EXCEEDED` | 400 | Duration > 120s | Inform user limit, suggest alternatives |
| `SUB_AGENT_FAILURE` | 500 | Video generation failed | Report, offer retry |
| `NETWORK_ERROR` | 503 | Connectivity issue | Retry once |
| `INVALID_MODEL` | 400 | Unknown model ID | Use recommended model |
| `CONTENT_FILTERED` | 400 | Content policy violation | Stop, report to user |

---


## Conversation Loop (SSE)

```
1. hixChat.createChat  →  chatId
       |
2. POST /api/hix/chat (SSE)
       |
Receive SSE events:
  CHAT_ANSWER (2002) → store detailId for reconnect
  WorkflowStarted     → log, prepare resources
  StepOutput          → read action in data
       |  action = done             → deliver result, break
       |  action = call_agent       → call sub-agent
       |  action = request_parameter → ask user for fields
       |  action = wait_user_confirm → show preview, wait
       |  action = credit_warning    → warn + continue
       |  action = credit_exhausted  → stop + prompt purchase
       |  action = error             → handle per policy
  CustomEnd           → deliver final result
  [DONE]              → connection closed
       |
3. On disconnect: POST /api/hix/agentEvent with {chatId, detailId, lastCursor}
```

---

## Credit Consumption

Video generation is credit-intensive. Every response includes credit usage:

```json
"meta": {
  "credits_consumed": 12,
  "remaining_credits": 988,
  "credit_status": "ok"
}
```

> Note: Higher resolution and longer duration consume more credits. Check balance before starting large tasks.

---

## Quick Verification Checklist

- [ ] API key obtained and provided
- [ ] Key verification returned ok
- [ ] Credits > 0 confirmed
- [ ] Test request sent and response received
- [ ] Duration within supported range (max 120s)

---

## Capability Summary Table

| Capability | Short Clip (<=15s) | AI Short Film (15s-120s) |
|-----------|---------------------|---------------------------|
| Text-to-Video | Yes | Yes |
| Image-to-Video | Yes | Yes |
| First Frame -> Video | Yes | No |
| Last Frame -> Video | Yes | No |
| First + Last Frame -> Video | Yes | No |
| Reference Images (<=3) | Yes | No |
| Max Duration | 15s | 120s |
| Max Resolution | Model-dependent | 1080p |
| Max Per Request | 4 videos | 1 video |
