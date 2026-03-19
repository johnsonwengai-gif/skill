---
description: AI Image Generation Agent — An intelligent orchestration agent that analyzes image generation requests, plans multi-step workflows, and coordinates sub-agents to produce image content. All actions are driven by SSE events received from the backend workflow API. Triggers when users want to create, edit, or plan image generation tasks.
name: ai-image
---

# AI Image — Intelligent Image Generation Agent

> Intelligent image generation orchestrator. Plans, coordinates, and executes image creation and editing workflows — all guided by the API.

---

## Prerequisites — API Key Setup

> Before using this skill, you must register and purchase an API key.

**Step 1: Register and Purchase**
Visit the platform to register your account and purchase an API key:
> `https://your-platform-domain.com/register`

**Step 2: Enter Your API Key**
After purchasing, provide your API key. The system will verify it before enabling image generation capabilities.

**Step 3: Verify Access**
Once verified, all image generation capabilities become available immediately.

> Credits / Quota: Each image generation or editing task consumes credits. If your balance is insufficient, you will be prompted to purchase additional credits at:
> `https://your-platform-domain.com/pricing`

---

## What Is AI Image?

AI Image is an **image generation and editing orchestration agent**. Instead of calling tools manually, you describe what you want — and the system automatically:

1. **Classifies** the task type
2. **Plans** required sub-tasks and steps
3. **Selects** appropriate image generation or editing capabilities
4. **Executes** step by step via the API
5. **Handles** cross-modal pipelines (e.g., prompt + reference -> image -> upscale / edit)

All decisions and actions are determined by SSE events from the backend.

---

## How It Works

```
User Request  →  hixChat.createChat (tRPC, session + chatId)
       ↓
POST /api/hix/chat  (SSE stream)
       ↓
SSE Events: WorkflowStarted → StepOutput × N → CustomEnd
       ↓
[DONE] — stream closed
```

All multi-modal capabilities are driven by **SSE events** received from the platform.

---

## API-First Execution Flow (SSE Event Protocol)

Every action is delivered as an **SSE event**. The client parses `event:` types and routes accordingly.

### SSE Event Types

| Event | When | Agent Behavior |
|-------|------|---------------|
| `WorkflowStarted` | Workflow begins | Log, prepare resources |
| `StepOutput` | Each step result | Parse payload, execute downstream |
| `CustomEnd` | Final output ready | Deliver result to user |
| `CHAT_ANSWER` (2002) | Answer initiated | Store `detailId` for reconnect |
| `[DONE]` | Stream ended | Close loop |
| `error` | On error | Handle per policy |

### Action Routing (from `StepOutput.data.action`)

| `action` | Behavior |
|---------|----------|
| `task_plan` | Execute planned steps |
| `call_agent` | Call specified sub-agent |
| `request_parameter` | Ask user for required fields |
| `wait_user_confirm` | Show preview, wait |
| `done` | Deliver final output |
| `credit_warning` | Warn user, continue if accepted |
| `credit_exhausted` | Stop, prompt purchase |
| `error` | Report to user |

### Credit Handling

```
credit_warning  → Inform user → Let them decide
credit_exhausted → Stop task → Prompt purchase at https://your-platform-domain.com/pricing
```

---

## Error Handling

| SSE Event Data `action` | Agent Behavior |
|------------------------|---------------|
| `error` + `retry: true` | Retry once, then stop |
| `error` + `retry: false` | Report error, stop |
| `error` + `recoverable: true` | Await user correction |
| Rate limit (429) | Wait, retry |
| Network error | Retry once, then report |
| `CONTENT_FILTERED` | Inform user, suggest revision |
## Image Agent Capability Boundaries

> IMPORTANT: The following defines the hard technical limits of the image agent. The API enforces these boundaries. The agent MUST respect these limits and inform users when requests exceed them.

### Generation & Processing Limits

| Parameter | Limit |
|-----------|-------|
| Max Images Per Request | Up to 12 images in a single request |
| Max Reference Images | Up to 10 reference images (for img2img or style reference) |
| Max Upscale Resolution | 8K |
| Failure Auto-Retry | Single image failure auto-retries up to 3 times |
| Output Format | PNG, JPG |

### Image Generation

| Parameter | Specification |
|-----------|---------------|
| **Input Modes** | Text-to-Image, Image-to-Image |
| **Output Format** | PNG, JPG |

### Image Editing

| Capability | Description |
|-----------|-------------|
| Upscale  | Enlarge image resolution without quality loss (up to 8K) |
| Expand Image  | Extend image boundaries to adjust aspect ratio or composition |
| Background Removal  | Remove the background from an image, isolate the subject |
| Background Replacement  | Replace the original background with a new one |
| Text/Watermark Removal  | Remove unwanted text or watermarks from images |

### Aspect Ratios

| Ratio | Use Case |
|-------|----------|
| `1:1` | Instagram post, avatar, square content |
| `4:5` | Instagram feed, portrait |
| `16:9` | YouTube thumbnail, cover, widescreen |
| `9:16` | Stories, vertical video, mobile |
| `3:2` | Photography, banner |

### Resolutions

| Level | Approx. Pixel Size | Use Case |
|-------|-------------------|----------|
| `1K` | ~1024px | Quick preview, social media |
| `2K` | ~2048px | High-quality web content |
| `4K` | ~4096px | Print, premium content |
| `8K` | ~8192px | Ultra-high quality, large format print |

---

## API-First Execution Flow

Every action is determined by the API response. The agent follows the `action` field exactly.

### Standard Workflow

```
1. User submits request (e.g., "Generate a cinematic cover image for X")
       |
2. API returns task_plan
   -> Determines: generation or editing mode, parameters
       |
3. Agent executes each step as instructed
       |
4. API returns done -> Present final image(s) to user
```

### Action Routing

| Action | Behavior |
|--------|----------|
| `task_plan` | Execute planned steps in order |
| `call_agent` | Call specified sub-agent with exact params |
| `call_api` | Call API with provided parameters |
| `request_parameter` | Ask user for required fields |
| `wait_user_confirm` | Show preview, wait for confirmation |
| `done` | Deliver final output |
| `credit_warning` | Inform user, let them decide |
| `credit_exhausted` | Stop, prompt purchase |
| `error` | Report to user |

---

## Capability Routing Rules

The API automatically routes based on task parameters:

```
IF user provides input_image AND prompt:
  -> Image-to-Image generation mode (transformation or style transfer)
       |
IF user provides multiple reference images (1-10):
  -> Style reference mode (style guided generation)
       |
IF user requests generation (prompt only, no image):
  -> Text-to-Image generation mode
       |
IF user requests upscale:
  -> Upscale pipeline (up to 8K resolution)
       |
IF user requests background removal/replacement:
  -> Background editing pipeline
       |
IF user requests text/watermark removal:
  -> Inpainting/removal pipeline
       |
IF user requests expand image:
  -> Expansion/outpainting pipeline
```

---

## Practical Application Scenarios

### Market & E-Commerce
Generate product main images, posters, banners, and event KV (key visual) assets. Create high-converting e-commerce visuals at scale for multiple platforms and campaigns.

**Example:** User describes a product and campaign theme -> API generates multiple product shots, banners, and event visuals -> User selects and downloads -> Used in stores, ads, and promotions.

### Content Creation
Create illustrations, cover images, storyboards, and illustration materials for blog posts, articles, social media, and digital publications.

**Example:** User provides a content brief -> API generates matching cover art and inline illustrations -> Assets delivered in required format and resolution.

### Office & Productivity
Generate presentation visuals, infographic backgrounds, and convert rough sketches into polished final artwork using image-to-image capabilities.

**Example:** User uploads a sketch or describes a concept -> API generates a refined, presentation-ready image -> Inserted directly into slides or documents.

### Design Exploration
Rapidly explore visual styles, layout compositions, and color schemes for creative projects. Generate mood boards and visual references for client alignment.

**Example:** User describes a brand or project direction -> API generates multiple style explorations, color variations, and layout concepts -> User reviews and selects direction -> Proceeds to final production.

---

## Parameter Handling

### Missing Input Parameters

When the API reports missing required parameters:
```
-> Display required fields to user
-> Wait for user to provide values
-> Resend with complete parameters
```

**Common required fields:**
- `prompt` — Text description of the desired image
- `aspect_ratio` — 1:1, 4:5, 16:9, 9:16, 3:2
- `resolution` — 1K, 2K, 4K, 8K
- `output_format` — PNG, JPG
- `reference_images` — Up to 10 images (optional, for img2img or style reference)

### When API Returns Additional Required Params

```
-> Display the missing parameters to user
-> Ask user to supply values
-> Retry with complete parameters
```

---

## Credit Handling

```
credit_warning  -> Inform user (credits, estimated cost) -> Let user decide
credit_exhausted -> Stop task -> Prompt purchase at https://your-platform-domain.com/pricing
```

---

## Error Handling

| API Action | Agent Behavior |
|-----------|---------------|
| `error` + `retry: true` | Retry once, then stop |
| `error` + `retry: false` | Report error, stop |
| `error` + `recoverable: true` | Await user correction |
| Rate limit | Wait as specified, retry |
| Network error | Retry once, then report |
| `CONTENT_FILTERED` | Inform user, suggest prompt revision |

> Note: Single image failure automatically retries up to 3 times per the API capability limits.

---

## Quick Reference

| Item | Value |
|------|-------|
| Skill Name | ai-image |
| Mode | API-first |
| Key Required | Yes |
| Max Per Request | 12 images |
| Max Reference Images | 10 images |
| Max Upscale | 8K |
| Auto-Retry | Up to 3 times per image |
| Supported Modes | Text2Image, Image2Image, Editing (Upscale, Expand, Background Removal/replacement, Text/Watermark Removal) |
| Aspect Ratios | 1:1, 4:5, 16:9, 9:16, 3:2 |
| Resolutions | 1K, 2K, 4K, 8K |
| Output Formats | PNG, JPG |
| Scripts | `scripts/main.py`, `scripts/api_client.py` |
| API Reference | `references/api_reference.md` |
