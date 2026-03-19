---
# API Reference — AI Image Agent

> Complete API integration specification. All behavior is driven by the API response.

---

> Note: Image generation and editing time varies by operation type and resolution. Set timeout to at least 120 seconds.

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
    "steps": [
      {
        "step": 1,
        "agent": "image",
        "params": {
          "prompt": "<prompt>",
          "aspect_ratio": "16:9",
          "resolution": "2K",
          "output_format": "PNG",
          "count": 1
        },
        "output_key": "generated_image"
      }
    ],
    "estimated_credits": 3,
    "estimated_time_seconds": 30
  }
}
```

### call_agent — Generation

```json
{
  "action": "call_agent",
  "message": "Calling image generation agent.",
  "data": {
    "agent": "image",
    "params": {
      "mode": "text2img",
      "prompt": "<scene_description>",
      "aspect_ratio": "16:9",
      "resolution": "2K",
      "output_format": "PNG",
      "count": 1,
      "reference_images": ["<url1>", "<url2>"]
    }
  },
  "meta": {
    "estimated_credits": 3,
    "estimated_time_seconds": 30,
    "retry_policy": "auto_retry_3x"
  }
}
```

### call_agent — Batch Generation (up to 12 images)

```json
{
  "action": "call_agent",
  "message": "Calling image generation agent (batch).",
  "data": {
    "agent": "image",
    "params": {
      "mode": "text2img",
      "prompt": "<scene_description>",
      "aspect_ratio": "16:9",
      "resolution": "2K",
      "output_format": "PNG",
      "count": 12,
      "reference_images": []
    }
  }
}
```

### call_agent — Editing

```json
{
  "action": "call_agent",
  "message": "Calling image editing agent.",
  "data": {
    "agent": "image_editing",
    "params": {
      "mode": "upscale",
      "input_image": "<url_or_base64>",
      "target_resolution": "8K"
    }
  }
}
```

```json
{
  "action": "call_agent",
  "message": "Calling image editing agent.",
  "data": {
    "agent": "image_editing",
    "params": {
      "mode": "background_removal",
      "input_image": "<url_or_base64>"
    }
  }
}
```

```json
{
  "action": "call_agent",
  "message": "Calling image editing agent.",
  "data": {
    "agent": "image_editing",
    "params": {
      "mode": "background_replacement",
      "input_image": "<url_or_base64>",
      "background_prompt": "<description_of_new_background>"
    }
  }
}
```

```json
{
  "action": "call_agent",
  "message": "Calling image editing agent.",
  "data": {
    "agent": "image_editing",
    "params": {
      "mode": "text_removal",
      "input_image": "<url_or_base64>",
      "remove_areas": [{"x": 0, "y": 0, "w": 100, "h": 50}]
    }
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
      {"name": "prompt", "label": "Image Prompt", "type": "text", "required": true},
      {"name": "aspect_ratio", "label": "Aspect Ratio", "type": "select", "options": ["1:1", "4:5", "16:9", "9:16", "3:2"], "required": true},
      {"name": "resolution", "label": "Resolution", "type": "select", "options": ["1K", "2K", "4K", "8K"], "required": true},
      {"name": "output_format", "label": "Output Format", "type": "select", "options": ["PNG", "JPG"], "required": true},
      {"name": "reference_images", "label": "Reference Images (up to 10)", "type": "text", "required": false}
    ]
  }
}
```

### wait_user_confirm

```json
{
  "action": "wait_user_confirm",
  "message": "Image generated. Review and confirm.",
  "data": {
    "preview": "<image_url_or_description>",
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
    "final_output": "<final_image_url>",
    "outputs": {
      "image_url": "<url>",
      "thumbnail_url": "<url>",
      "images": [
        {"url": "<url1>", "index": 1},
        {"url": "<url2>", "index": 2}
      ]
    },
    "steps_completed": 1,
    "total_credits_consumed": 3,
    "remaining_credits": 997,
    "resolution": "2K",
    "aspect_ratio": "16:9",
    "format": "PNG",
    "images_generated": 1,
    "retry_count": 0
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
    "estimated_credits_for_completion": 6,
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
| `REFERENCE_IMAGES_EXCEEDED` | 400 | More than 10 reference images provided | Reduce to 10 or fewer |
| `UPSCAILE_RESOLUTION_EXCEEDED` | 400 | Resolution above 8K requested | Cap at 8K |
| `SUB_AGENT_FAILURE` | 500 | Image generation failed | Auto-retry up to 3 times |
| `NETWORK_ERROR` | 503 | Connectivity issue | Retry once |
| `INVALID_MODEL` | 400 | Unknown model ID | Use recommended model |
| `CONTENT_FILTERED` | 400 | Content policy violation | Stop, report, suggest revision |
| `IMAGE_TOO_SMALL` | 400 | Input image below minimum size | Upscale first, retry |

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

Image generation and editing credit costs vary by operation type and resolution. Every response includes credit usage:

```json
"meta": {
  "credits_consumed": 3,
  "remaining_credits": 997,
  "credit_status": "ok"
}
```

> Note: Higher resolution (4K, 8K), batch generation, and editing operations consume more credits. Check balance before large batches. The API automatically retries failed images up to 3 times per the retry policy.

---

## Quick Verification Checklist

- [ ] API key obtained and provided
- [ ] Key verification returned ok
- [ ] Credits > 0 confirmed
- [ ] Test request sent and response received
- [ ] Image output received successfully
- [ ] Reference images within 10-image limit
- [ ] Upscale resolution at or below 8K

---

## Capability Summary Table

| Capability | Supported | Limits |
|-----------|-----------|--------|
| Text-to-Image | Yes | Batch up to 12 images per request |
| Max Per Request | Yes | Up to 12 images |
| Reference Images | Yes | Up to 10 reference images |
| Upscale | Yes | Max 8K resolution |
| Expand Image | Yes | Boundary extension |
| Background Removal | Yes | Subject isolation |
| Background Replacement | Yes | New background prompt required |
| Text/Watermark Removal | Yes | Area spec or auto-detection |
| Auto-Retry on Failure | Yes | Up to 3 retries per image |
| Multiple Resolutions | Yes | 1K, 2K, 4K, 8K |
| Multiple Formats | Yes | PNG, JPG |
