---

# API Reference — AI Writer Agent

> Complete API integration specification. All behavior is driven by the API response.

---

> Note: Document generation time varies by document length and complexity. Set timeout to at least 120 seconds for standard documents.

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
    "task_type": "document_generation",
    "document_type": "prd",
    "steps": [
      {
        "step": 1,
        "agent": "writer",
        "params": {
          "document_type": "prd",
          "content": "<content_description>",
          "style": "formal",
          "include_toc": true,
          "include_cover": true,
          "target_format": "markdown"
        },
        "output_key": "markdown_draft"
      },
      {
        "step": 2,
        "agent": "converter",
        "params": {
          "source": "markdown_draft",
          "target_format": "word",
          "style": "formal",
          "brand_colors": []
        },
        "output_key": "final_document"
      }
    ],
    "estimated_credits": 5,
    "estimated_time_seconds": 45
  }
}
```

### call_agent — Document Generation

```json
{
  "action": "call_agent",
  "message": "Calling document generation agent.",
  "data": {
    "agent": "writer",
    "params": {
      "document_type": "prd",
      "content": "<content_bullet_points_or_outline>",
      "style": "formal",
      "include_toc": true,
      "include_cover": true,
      "brand_colors": [],
      "language": "zh",
      "max_length": 20000,
      "target_format": "markdown"
    }
  },
  "meta": {
    "estimated_credits": 5,
    "estimated_time_seconds": 45
  }
}
```

### call_agent — Format Conversion

```json
{
  "action": "call_agent",
  "message": "Converting document to target format.",
  "data": {
    "agent": "converter",
    "params": {
      "source_markdown": "<markdown_content>",
      "target_format": "word",
      "style": "formal",
      "include_toc": true,
      "include_cover": true,
      "brand_colors": []
    }
  }
}
```

### call_agent — Revision Round

```json
{
  "action": "call_agent",
  "message": "Revision round. Producing new version.",
  "data": {
    "agent": "writer",
    "params": {
      "document_type": "prd",
      "content": "<revised_content_or_feedback>",
      "previous_version": "<previous_markdown>",
      "revision_notes": "<user_feedback>",
      "max_length": 20000,
      "target_format": "markdown"
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
      {"name": "document_type", "label": "Document Type", "type": "select", "options": ["resume", "proposal", "prd", "weekly_report", "monthly_report", "review_report", "meeting_minutes", "whitepaper", "technical_spec", "personal_statement", "project_intro", "other"], "required": true},
      {"name": "content", "label": "Content Source", "type": "textarea", "required": true},
      {"name": "target_format", "label": "Output Format", "type": "select", "options": ["markdown", "word", "pdf", "html"], "required": true},
      {"name": "style", "label": "Layout Style", "type": "select", "options": ["formal", "simple"], "required": false},
      {"name": "include_toc", "label": "Include Table of Contents", "type": "boolean", "required": false},
      {"name": "include_cover", "label": "Include Cover Page", "type": "boolean", "required": false}
    ]
  }
}
```

### wait_user_confirm

```json
{
  "action": "wait_user_confirm",
  "message": "Document draft generated. Review and confirm.",
  "data": {
    "preview": "<draft_url_or_content_preview>",
    "confirm_prompt": "Approve this version? (yes / revise / cancel)",
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
    "final_output": "<final_document_url>",
    "outputs": {
      "markdown_url": "<url>",
      "word_url": "<url>",
      "pdf_url": "<url>",
      "html_url": "<url>"
    },
    "document_type": "prd",
    "character_count": 12500,
    "version": 1,
    "revision_count": 0,
    "formats_delivered": ["markdown", "word"],
    "steps_completed": 2,
    "total_credits_consumed": 5,
    "remaining_credits": 995
  }
}
```

### revision

```json
{
  "action": "revision",
  "message": "New revision version ready.",
  "data": {
    "version": 2,
    "markdown_url": "<new_version_url>",
    "changes_summary": "<brief_description_of_changes>",
    "revision_count": 1
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
    "partial_output": "<partial_markdown_or_url>",
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
| `LENGTH_EXCEEDED` | 400 | Content > 20,000 characters | Cap or split; notify user |
| `MANUSCRIPT_TOO_LONG` | 400 | Book-length or >50k chars requested | Reject, explain limit |
| `BATCH_TOO_LARGE` | 400 | >100 articles or >1000 titles | Reject, explain limit |
| `UNSUPPORTED_DOC_TYPE` | 400 | Document type not supported | List supported types |
| `CONVERSION_FAILED` | 500 | Markdown to target format failed | Report, retry |
| `SUB_AGENT_FAILURE` | 500 | Writer or converter agent failed | Report, offer retry |
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
  "credits_consumed": 5,
  "remaining_credits": 995,
  "credit_status": "ok"
}
```

> Note: Longer documents and format conversion consume more credits. Each revision round also consumes credits. Check balance before generating very long documents.

---

## Quick Verification Checklist

- [ ] API key obtained and provided
- [ ] Key verification returned ok
- [ ] Credits > 0 confirmed
- [ ] Document type is supported
- [ ] Content length within recommended max (20,000 characters)
- [ ] Target format specified
- [ ] User informed of out-of-scope items if applicable

---

## Capability Summary Table

| Capability | Supported | Limits |
|-----------|-----------|--------|
| Document Types | Yes | Resume, proposal, PRD, reports, whitepaper, etc. |
| Markdown Output | Yes | Full structure, editable |
| Word (DOCX) Output | Yes | Styled headings, tables, images |
| PDF Output | Yes | Cover, TOC, styled body |
| HTML Output | Yes | Web-ready styled HTML |
| Single Generation Limit | Yes | Recommended max 20,000 chars |
| Iterative Revision | Yes | Multiple rounds supported |
| Cover Page | Optional | Per-user preference |
| Table of Contents | Optional | Auto-generated from headings |
| Title Hierarchy | Yes | H1–H6 |
| Tables | Yes | |
| Images / Figures | Yes | |
| Code Blocks | Yes | |
| Basic Formulas | Basic | Complex LaTeX degrades |
| Footnotes / References | Basic | |
| Out of Scope: Ultra-Long Books | No | >50k chars |
| Out of Scope: Mass Batch | No | >100 articles or >1000 titles |
| Out of Scope: Complex Rich Layout | No | Multi-column/floating objects |
| Out of Scope: Legal / Medical / Financial | No | High-risk text not promised |
