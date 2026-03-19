---
description: Multi-Modal General Orchestration Agent — A true multi-modal intelligent agent that coordinates complex workflows across image, video, slide, document, and research sub-agents via the General Agent SSE protocol. Automatically classifies tasks, plans multi-step routes, selects and chains sub-agents, and cross-modes existing outputs. All actions are driven by SSE events received from the backend. Triggers when users want to handle multi-modal tasks or coordinate multiple capabilities.
name: ai-chat
---

# AI Chat — Multi-Modal General Orchestration Agent

> True multi-modal orchestration agent. Coordinates image, video, slide, writer, and research sub-agents into unified workflows via the General Agent SSE protocol.

---

## Prerequisites — API Key Setup

> Before using this skill, you must register and purchase an API key.

**Step 1: Register and Purchase**
Visit the platform to register your account and purchase an API key:
> `https://your-platform-domain.com/register`

**Step 2: Enter Your API Key**
After purchasing, provide your API key. The system will verify it before enabling multi-modal capabilities.

**Step 3: Verify Access**
Once verified, all sub-agents and orchestration capabilities become available.

> Credits / Quota: Each sub-agent task consumes credits. Concurrency limits are enforced by the platform. If your balance is insufficient or concurrency is exceeded, the API will return error codes.

---

## What Is AI Chat?

AI Chat is a **true multi-modal general orchestration agent**. It is the primary entry point for users who want to handle complex, cross-modal tasks.

1. **Classifies** the task type from the user's conversational request
2. **Creates** a General Agent session via tRPC
3. **Sends** the task as a structured message
4. **Streams** real-time SSE events (`RUN_STARTED`, `TOOL_CALL_*`, `TEXT_MESSAGE_CONTENT`, `RUN_FINISHED`)
5. **Routes** sub-agent calls via `TOOL_CALL_START / TOOL_CALL_END` events
6. **Cross-modes** existing outputs as inputs to downstream sub-agents
7. **Retrieves** output files via memory APIs

All decisions and actions are determined by **SSE events** received from the backend.

> **Sub-agent capability boundaries** are maintained in `references/subagent.md`. Read that file when planning routes or answering questions about specific limits.

---

## How It Works

```
User Request
    |
    v
hixChat.createChat (tRPC)  →  chatId
    |
    v
generalAgent.sendMessage (tRPC)  →  runId
    |
    v
GET /api/hix/generalAgent?chatId=...  (SSE stream)
    |
    v
SSE Events: RUN_STARTED → TOOL_CALL_START → TEXT_MESSAGE_CONTENT → TOOL_CALL_END → RUN_FINISHED → DONE
    |
    v
generalAgent.memoryList / memoryRead  →  output files
```

---

## Multi-Modal Sub-Agent Architecture

AI Chat coordinates 5 specialized sub-agents via `TOOL_CALL_*` SSE events:

| Sub-Agent | Name | Primary Function |
|-----------|------|-----------------|
| `image` | AI Image | Text-to-image, img2img, upscale, background/text removal |
| `video` | AI Video | Text-to-video, image-to-video, video extension, merge |
| `slide` | AI Slide | PPT generation from topic/document → PPTX with nano_banana_pro images |
| `writer` | AI Writer | Long-form document generation: Markdown → Word / PDF / HTML |
| `research` | Deep Research | Structured research report: 2k–15k chars, up to 30 sources |

### Cross-Modal Reuse (Upstream → Downstream)

```
Research Report (Markdown)
    → [slide] → PPT presentation
    → [video] → video summary of report

Slide Deck (PPTX)
    → [video] → video walkthrough

Images (any source)
    → [slide] → cover / illustration images
    → [video] → video

Writer Output (Markdown)
    → [slide] → slides from document
    → [video] → video narration

PPTX
    → [image] → cover or asset images
```

---

## API-First Execution Flow (General Agent SSE Protocol)

Every action is delivered as an **SSE event**. The client parses event types and routes accordingly.

### SSE Event Types

| Event | When | Agent Behavior |
|-------|------|---------------|
| `RUN_STARTED` | Run begins | Log `run_id`, prepare resources |
| `TEXT_MESSAGE_CONTENT` | Incremental text output | Stream text to user |
| `TOOL_CALL_START` | Sub-agent begins | Log tool name, show input |
| `TOOL_CALL_END` | Sub-agent completes | Log output, store for downstream |
| `RUN_FINISHED` | Run completes | Gather all outputs |
| `PLAYBACK` | Redis cleared before reconnect | Refresh history via `getMessages` |
| `DONE` | Stream ended | Close loop |
| `ERROR` | Task error | Report to user |

### Control Flow

| Action | Behavior |
|--------|----------|
| `TOOL_CALL_START` | Sub-agent started; route to image / video / slide / writer / research |
| `TOOL_CALL_END` | Sub-agent completed; check for cross-modal downstream |
| `PLAYBACK` | Call `getMessages` to refresh history; continue stream |
| `DONE` | Deliver final output; end |
| `ERROR` | Report error to user |
| `TASK_LIMIT_EXCEEDED` | Inform user; suggest waiting or upgrading |

### Credit Handling

> Managed by the platform per session. On quota / concurrency issues, the API returns specific error codes via tRPC response.

---

## Error Handling

| SSE Event / Error Code | Agent Behavior |
|----------------------|---------------|
| `ERROR` SSE event | Report to user; end loop |
| `PLAYBACK` event | Refresh history; continue |
| `TASK_LIMIT_EXCEEDED` | Inform user; suggest plan upgrade |
| `RUN_ALREADY_ACTIVE` | Notify user; wait or cancel existing |
| `INVALID_SESSION_STATE` | Refresh session; retry |
| Rate limit (429) | Wait, retry |
| Network error | Retry once, then report |

---

## Quick Reference

| Item | Value |
|------|-------|
| Skill Name | ai-chat |
| Mode | General Agent SSE protocol |
| Session Creation | `hixChat.createChat` (tRPC) |
| Message Sending | `generalAgent.sendMessage` (tRPC) |
| Real-Time Stream | `GET /api/hix/generalAgent?chatId=…` (SSE, GET) |
| Auth | Session-based via `chatId` |
| Key Required | Yes (via platform registration) |
| Sub-Agents | image, video, slide, writer, research |
| Cross-Modal Chain | Supported |
| Parallel Execution | Via multiple `TOOL_CALL_START` events |
| Session History | `generalAgent.getMessages` |
| Output Files | `generalAgent.memoryList` / `memoryRead` |
| ZIP Download | `GET /api/hix/generalAgent/archive-download` |
| Task Cancel | `generalAgent.cancelTask` |
| Sub-Agent Limits | See `references/subagent.md` |
| Scripts | `scripts/main.py`, `scripts/api_client.py` |
| API Reference | `references/api_reference.md` |
| Sub-Agent Reference | `references/subagent.md` |
