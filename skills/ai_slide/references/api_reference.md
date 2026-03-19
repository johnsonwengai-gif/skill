---
# API Reference — AI Slide Agent

> Complete API integration specification. All behavior is driven by the API response.

---

> Note: Slide generation time varies by page count and image generation complexity. Set timeout to at least 180 seconds.

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
    "task_type": "slide_generation",
    "flow": "structured_content -> html_intermediate -> pptx_conversion -> image_generation",
    "steps": [
      {
        "step": 1,
        "agent": "slide",
        "params": {
          "topic": "<topic>",
          "pages": 10,
          "audience": "investor",
          "scenario": "roadshow",
          "visual_preferences": {},
          "illustration_source": "ai_generated",
          "image_count": 5,
          "speaker_notes": false,
          "material_list": false
        },
        "output_key": "presentation_deck"
      }
    ],
    "estimated_credits": 8,
    "estimated_time_seconds": 90
  }
}
```

### call_agent — Slide Generation

```json
{
  "action": "call_agent",
  "message": "Calling slide generation agent.",
  "data": {
    "agent": "slide",
    "params": {
      "topic": "<topic_or_outline>",
      "pages": 10,
      "max_pages": 30,
      "audience": "investor",
      "scenario": "roadshow",
      "visual_preferences": {
        "brand_colors": [],
        "fonts": [],
        "style_reference": "<url_or_description>"
      },
      "illustration_source": "ai_generated",
      "image_model": "nano_banana_pro",
      "max_images": 10,
      "image_count": 5,
      "speaker_notes": false,
      "material_list": false,
      "page_structure": ["cover", "toc", "body", "summary", "appendix"]
    }
  },
  "meta": {
    "estimated_credits": 8,
    "estimated_time_seconds": 90
  }
}
```

### call_agent — Image Generation (nano_banana_pro)

```json
{
  "action": "call_agent",
  "message": "Calling per-slide image generation (nano_banana_pro).",
  "data": {
    "agent": "image",
    "params": {
      "model": "nano_banana_pro",
      "prompt": "<per_slide_image_prompt>",
      "page_index": 1,
      "aspect_ratio": "16:9",
      "resolution": "2K",
      "output_format": "PNG"
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
      {"name": "topic", "label": "Topic or Outline", "type": "text", "required": true},
      {"name": "pages", "label": "Number of Pages", "type": "number", "min": 1, "max": 30, "default": 10, "required": true},
      {"name": "audience", "label": "Audience", "type": "select", "options": ["investor", "client", "employee", "academic", "general"], "required": true},
      {"name": "scenario", "label": "Scenario", "type": "select", "options": ["roadshow", "pitch", "training", "review", "academic", "event"], "required": true},
      {"name": "illustration_source", "label": "Illustration Source", "type": "select", "options": ["ai_generated", "web_images", "user_uploaded"], "required": false},
      {"name": "speaker_notes", "label": "Include Speaker Notes", "type": "boolean", "required": false},
      {"name": "material_list", "label": "Include Material List", "type": "boolean", "required": false}
    ]
  }
}
```

### wait_user_confirm

```json
{
  "action": "wait_user_confirm",
  "message": "Presentation generated. Review and confirm.",
  "data": {
    "preview": "<deck_url_or_description>",
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
    "final_output": "<final_deck_url>",
    "outputs": {
      "pptx_url": "<url>",
      "html_url": "<url>",
      "speaker_notes_url": "<url_or_null>",
      "material_list_url": "<url_or_null>",
      "pages_generated": 10,
      "images_generated": 5,
      "image_model": "nano_banana_pro",
      "page_structure": ["cover", "toc", "body", "summary", "appendix"]
    },
    "steps_completed": 2,
    "total_credits_consumed": 8,
    "remaining_credits": 992
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
    "estimated_credits_for_completion": 15,
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
| `PAGES_EXCEEDED` | 400 | Pages > 30 per deck | Cap at 30, notify user |
| `IMAGES_EXCEEDED` | 400 | AI images > 10 per deck | Cap at 10, notify user |
| `UNSUPPORTED_SCENARIO` | 400 | Scenario not in supported list | Suggest alternatives |
| `SUB_AGENT_FAILURE` | 500 | Slide or image generation failed | Report, offer retry |
| `NETWORK_ERROR` | 503 | Connectivity issue | Retry once |
| `CONTENT_FILTERED` | 400 | Content policy violation | Stop, suggest revision |

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

Every response includes credit usage:

```json
"meta": {
  "credits_consumed": 8,
  "remaining_credits": 992,
  "credit_status": "ok"
}
```

> Note: More pages and AI image generation consume more credits. Check balance before generating large decks.

---

## Quick Verification Checklist

- [ ] API key obtained and provided
- [ ] Key verification returned ok
- [ ] Credits > 0 confirmed
- [ ] Test request sent and response received
- [ ] Pages within limit (max 30 per generation, default 10)
- [ ] AI images within limit (max 10 per deck)
- [ ] Scenario is supported (roadshow / pitch / training / review / academic / event)
- [ ] User informed of out-of-scope items if applicable

---

## Capability Summary Table

| Capability | Supported | Limits |
|-----------|-----------|--------|
| Structured Content to PPTX | Yes | HTML intermediate flow |
| nano_banana_pro Image Model | Yes | Per-slide generation |
| Max Pages Per Generation | Yes | 30 pages (default 10) |
| Max AI Images Per Deck | Yes | 10 images |
| User Image Priority | Yes | User images preferred over AI |
| PPTX (Editable) | Yes | Standard output |
| Title Hierarchy | Yes | |
| Chart Placeholders | Yes | |
| Simple Charts | Yes | |
| Speaker Notes | Optional | |
| Material List | Optional | |
| Out of Scope: Large Data Viz | No | Multi-dim interactive charts |
| Out of Scope: Complex Animations | No | Custom transitions/effects |
| Out of Scope: Strict Brand VI | No | No guarantee |
| Out of Scope: Image Copyright | No | User responsibility |
