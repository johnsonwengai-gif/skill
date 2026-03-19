---

# API Reference — Deep Research Agent

> Complete API integration specification. All behavior is driven by the API response.

---

> Note: Deep research tasks involve source retrieval and long-form writing. Set timeout to at least 180 seconds.

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
  "message": "Research task analyzed. Execution plan ready.",
  "data": {
    "task_type": "deep_research",
    "steps": [
      {
        "step": 1,
        "agent": "retrieve",
        "params": {
          "topic": "<topic>",
          "scope": "<region/time/industry/caliber>",
          "max_sources": 30,
          "max_chars_per_source": 204800
        },
        "output_key": "retrieved_sources"
      },
      {
        "step": 2,
        "agent": "research",
        "params": {
          "topic": "<topic>",
          "audience": "consulting",
          "style": "consulting",
          "min_length": 2000,
          "max_length": 15000,
          "sources": "<retrieved_sources>"
        },
        "output_key": "draft_report"
      },
      {
        "step": 3,
        "agent": "write",
        "params": {
          "topic": "<topic>",
          "audience": "consulting",
          "style": "consulting",
          "include_summary": true,
          "include_citations": true,
          "citation_style": "footnote"
        },
        "output_key": "final_markdown_report"
      }
    ],
    "estimated_credits": 12,
    "estimated_time_seconds": 120
  }
}
```

### call_agent — Retrieval

```json
{
  "action": "call_agent",
  "message": "Calling source retrieval agent.",
  "data": {
    "agent": "retrieve",
    "params": {
      "topic": "<research_topic>",
      "scope": "<region/time/industry/caliber>",
      "provided_sources": ["<url1>", "<url2>"],
      "max_sources": 30,
      "max_chars_per_source": 204800
    }
  },
  "meta": {
    "estimated_credits": 4,
    "estimated_time_seconds": 30
  }
}
```

### call_agent — Research Synthesis

```json
{
  "action": "call_agent",
  "message": "Calling research synthesis agent.",
  "data": {
    "agent": "research",
    "params": {
      "topic": "<research_topic>",
      "sources": "<retrieved_sources>",
      "audience": "consulting",
      "style": "consulting",
      "min_length": 2000,
      "max_length": 15000,
      "scope": "<region/time/industry>"
    }
  },
  "meta": {
    "estimated_credits": 6,
    "estimated_time_seconds": 60
  }
}
```

### call_agent — Report Writing

```json
{
  "action": "call_agent",
  "message": "Calling report writing agent.",
  "data": {
    "agent": "write",
    "params": {
      "topic": "<research_topic>",
      "synthesis": "<synthesized_findings>",
      "sources": "<retrieved_sources>",
      "audience": "consulting",
      "style": "consulting",
      "min_length": 2000,
      "max_length": 15000,
      "include_summary": true,
      "include_key_points": true,
      "include_analysis": true,
      "include_conclusions": true,
      "include_citations": true,
      "citation_style": "footnote"
    }
  },
  "meta": {
    "estimated_credits": 2,
    "estimated_time_seconds": 30
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
      {"name": "topic", "label": "Research Topic / Question", "type": "text", "required": true},
      {"name": "audience", "label": "Audience", "type": "select", "options": ["general", "consulting", "investor", "technical"], "required": true},
      {"name": "style", "label": "Writing Style", "type": "select", "options": ["popular_science", "consulting", "investment", "technical"], "required": true},
      {"name": "scope", "label": "Scope & Constraints", "type": "text", "required": false},
      {"name": "sources", "label": "Data Sources (URLs / Files)", "type": "textarea", "required": false},
      {"name": "max_length", "label": "Max Report Length", "type": "number", "min": 2000, "max": 15000, "default": 15000, "required": false}
    ]
  }
}
```

### wait_user_confirm

```json
{
  "action": "wait_user_confirm",
  "message": "Research report draft ready. Review and confirm.",
  "data": {
    "preview": "<report_url_or_content_preview>",
    "confirm_prompt": "Approve this report? (yes / revise / cancel)",
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
    "final_output": "<final_report_url>",
    "outputs": {
      "markdown_url": "<url>",
      "summary": "<abstract_text>",
      "key_points": ["<bullet1>", "<bullet2>"],
      "character_count": 8500,
      "source_count": 18,
      "citation_count": 18,
      "revision_count": 0
    },
    "report_structure": ["summary", "key_points", "analysis", "conclusions", "citations"],
    "style": "consulting",
    "audience": "consulting",
    "sources_used": 18,
    "sources_limit": 30,
    "steps_completed": 3,
    "total_credits_consumed": 12,
    "remaining_credits": 988
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
    "estimated_credits_for_completion": 20,
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
    "partial_output": "<partial_report_or_sources>",
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
| `SOURCES_EXCEEDED` | 400 | More than 30 sources requested | Cap at 30, notify user |
| `SOURCE_TOO_LARGE` | 400 | Source > 200 KB pure text | Truncate at 200 KB, notify user |
| `LENGTH_OUT_OF_RANGE` | 400 | Report length outside 2k–15k | Adjust to valid range |
| `PAYWALL_DETECTED` | 400 | Source behind paywall | Note limitation, skip source |
| `RETRIEVAL_FAILED` | 500 | Source retrieval failed | Skip source, continue |
| `SUB_AGENT_FAILURE` | 500 | Retrieval or writing agent failed | Report, offer retry |
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
  "credits_consumed": 12,
  "remaining_credits": 988,
  "credit_status": "ok"
}
```

> Note: Retrieval (per source), synthesis, and writing each consume credits. Longer reports and more sources increase credit cost. Each revision round also consumes credits.

---

## Quick Verification Checklist

- [ ] API key obtained and provided
- [ ] Key verification returned ok
- [ ] Credits > 0 confirmed
- [ ] Research topic clearly defined
- [ ] Scope and constraints specified (recommended)
- [ ] Audience and style selected
- [ ] Sources provided or public retrieval authorized
- [ ] Report length within 2,000–15,000 characters
- [ ] Sources within limit (max 30)
- [ ] User informed of out-of-scope items (paywall, real-time facts, copyright)

---

## Capability Summary Table

| Capability | Supported | Limits |
|-----------|-----------|--------|
| Research Topic / Question | Yes | Required |
| Scope & Constraints | Yes | Region / time / industry / caliber |
| Audience & Style | Yes | general / consulting / investor / technical |
| Data Sources (URLs / Files) | Yes | Optional; public web + user materials |
| Markdown Report Output | Yes | Editable, revision supported |
| Summary / Abstract | Yes | |
| Key Points | Yes | |
| Analysis & Argumentation | Yes | |
| Conclusions | Yes | |
| Citations | Yes | Footnotes + links, all sources attributed |
| Report Length | Yes | 2,000 – 15,000 characters |
| Max External Sources | Yes | 30 per report |
| Max Text Per Source | Yes | 200 KB pure text |
| Iterative Revision | Yes | Multiple rounds supported |
| Out of Scope: Paywall Completeness | No | Not guaranteed |
| Out of Scope: Real-Time Fact Verification | No | Not a final authority |
| Out of Scope: Long Copyright Text | No | Content paraphrased |
