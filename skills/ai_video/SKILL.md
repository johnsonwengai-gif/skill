---
description: AI Video Generation Agent — An intelligent orchestration agent that analyzes complex video generation requests, plans multi-step workflows, and coordinates sub-agents to produce video content. All actions are driven by SSE events received from the backend workflow API. Triggers when users want to create, edit, or plan video generation tasks.
name: ai-video
---

# AI Video — Intelligent Video Generation Agent

> Intelligent video generation orchestrator. Plans, coordinates, and executes video creation workflows — all guided by the API.

---

## Prerequisites — API Key Setup

> Before using this skill, you must register and purchase an API key.

**Step 1: Register and Purchase**
Visit the platform to register your account and purchase an API key:
> `https://your-platform-domain.com/register`

**Step 2: Enter Your API Key**
After purchasing, provide your API key. The system will verify it before enabling video generation capabilities.

**Step 3: Verify Access**
Once verified, all video generation capabilities become available immediately.

> Credits / Quota: Each video generation consumes credits. If your balance is insufficient, you will be prompted to purchase additional credits at:
> `https://your-platform-domain.com/pricing`

---

## What Is AI Video?

AI Video is a **video generation orchestration agent**. Instead of calling tools manually, you describe what you want — and the system automatically:

1. **Classifies** the task type
2. **Plans** required sub-tasks and steps
3. **Selects** appropriate video generation capabilities
4. **Executes** step by step via the API
5. **Handles** cross-modal pipelines (e.g., script -> storyboard -> video)

All decisions and actions are determined by the backend API response.

---

## How It Works

```
User Request
    |
    v
API Call -> API Response (action)
    |
    v
Execute as instructed
    |
    v
Repeat until done
```

---

## Video Agent Capability Boundaries

> IMPORTANT: The following defines the hard technical limits of the video agent. The API enforces these boundaries. The agent MUST respect these limits and inform users when requests exceed them.

### Short Clip Generation (Single Clip, 15 seconds or less)

| Parameter | Specification |
|-----------|---------------|
| **Max Duration** | 15 seconds per clip |
| **Max Keyframes** | Max 2 (Image-to-Video) |
| **Max Reference Images** | Max 3 |
| **Max Per Request** | 4 videos per single request |
| **Output Format** | MP4 |

**Supported Modes:**
- Text-to-Video (text script -> video clip)
- Image-to-Video (single image -> animated video)
- First Frame -> Video (start from a reference image)
- Last Frame -> Video (end at a reference image)
- First + Last Frame -> Video (start and end at reference images)
- Reference Images (up to 3) -> Video

### AI Short Film (Multi-segment, 15s - 120s)

| Parameter | Specification |
|-----------|---------------|
| **Duration Range** | 15 - 120 seconds |
| **Workflow** | Script -> Storyboard -> Multi-segment Synthesis |
| **Activation** | Automatically triggered when duration exceeds short clip limit |
| **Aspect Ratio** | 16:9 (horizontal) or 9:16 (vertical) |
| **Resolution** | 720p or 1080p |
| **Frame Rate** | Max 24fps |
| **Max Per Request** | 1 video per single request |
| **Output Format** | MP4 (consolidated final file) |

**Supported Modes:**
- Text-to-Video (up to 120s)
- Image-to-Video (up to 120s)

---

## Practical Application Scenarios

### Short Video Creation
Convert a text script and reference image into an AI-generated video clip, then layer in background music to produce a complete short video ready for social media distribution.

**Example:** User provides a product description and lifestyle photo -> API generates a dynamic product showcase video -> Background music added -> Final MP4 delivered.

### Marketing & Advertising Materials
Take product photography or lifestyle images and generate dynamic, visually engaging display videos for advertisements, brand campaigns, or e-commerce showcases.

**Example:** User uploads product photos -> API generates animated product videos with cinematic transitions -> Suitable for platform ads, social campaigns, or brand storytelling.

### Talking Head & Avatar Content
Combine a video of a person (or avatar) with audio to create lip-synced broadcast content, narration, or virtual presenter videos for training, education, or content marketing.

**Example:** User provides a presenter video and audio narration -> API synchronizes the video with the audio track -> Lip-synced presenter content generated -> Final video delivered.

---

## API-First Execution Flow

Every action is determined by the API response. The agent follows the `action` field exactly.

### Standard Workflow

```
1. User submits request (e.g., "Create a 20-second cinematic video about X")
       |
2. API returns task_plan
   -> If duration <= 15s: Short Clip workflow
   -> If duration > 15s: AI Short Film workflow
       |
3. Agent executes each step as instructed
       |
4. API returns done -> Present final video to user
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
IF duration <= 15s:
  -> Short Clip Generation
  -> Available modes: Text2Video, Image2Video, FirstFrame, LastFrame, FirstLastFrame, RefImages
       |
IF duration > 15s AND duration <= 120s:
  -> AI Short Film (Multi-segment)
  -> Triggers: Script -> Storyboard -> Synthesis pipeline
       |
IF duration > 120s:
  -> NOT SUPPORTED
  -> Inform user: "This duration exceeds the maximum supported length (120s)"
```

---

## Parameter Handling

### Missing Input Parameters

When the API reports missing required parameters:
```
-> Display required fields to user
-> Wait for user to provide values
-> Resend with complete parameters
```

**Common required fields for video:**
- `prompt` — Text description of the video scene
- `duration` — Video length in seconds (max 120)
- `aspect_ratio` — 16:9 or 9:16
- `resolution` — 720p or 1080p

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
| `DURATION_EXCEEDED` | Inform user of 120s max limit, suggest alternatives |
| Rate limit | Wait as specified, retry |
| Network error | Retry once, then report |

---

## Quick Reference

| Item | Value |
|------|-------|
| Skill Name | ai-video |
| Mode | API-first |
| Key Required | Yes |
| Short Clip | max 15s |
| AI Short Film | 15s - 120s |
| Max Duration | 120 seconds |
| Supported Modes | Text2Video, Image2Video, FirstFrame, LastFrame, FirstLastFrame, RefImages |
| Output | MP4 |
| Scripts | `scripts/main.py`, `scripts/api_client.py` |
| API Reference | `references/api_reference.md` |
