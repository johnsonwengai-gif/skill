---
description: AI Slide Agent — An intelligent orchestration agent that analyzes presentation requests, generates structured slide decks via HTML intermediate, and converts to PPTX output. Uses nano_banana_pro model for per-slide image generation. All actions are driven by SSE events received from the backend workflow API. Triggers when users want to create, edit, or plan presentation tasks.
name: ai-slide
---

# AI Slide — Intelligent Presentation Agent

> Intelligent slide generation orchestrator. Generates structured HTML intermediate, converts to PPTX with unified theme and content density — all guided by the API.

---

## Prerequisites — API Key Setup

> Before using this skill, you must register and purchase an API key.

**Step 1: Register and Purchase**
Visit the platform to register your account and purchase an API key:
> `https://your-platform-domain.com/register`

**Step 2: Enter Your API Key**
After purchasing, provide your API key. The system will verify it before enabling slide generation capabilities.

**Step 3: Verify Access**
Once verified, all slide generation capabilities become available immediately.

> Credits / Quota: Each slide generation consumes credits. If your balance is insufficient, you will be prompted to purchase additional credits at:
> `https://your-platform-domain.com/pricing`

---

## What Is AI Slide?

AI Slide is a **slide generation orchestration agent** that produces editable PowerPoint presentations through a structured HTML intermediate layer, ensuring unified theme and consistent information density throughout the deck.

1. **Receives** topic, outline, or source document
2. **Plans** structured page layout (cover, TOC, body, summary, appendix)
3. **Generates** per-slide visuals using nano_banana_pro model
4. **Outputs** PPTX with editable layouts, title hierarchy, chart placeholders, and AI-generated illustrations
5. **Supports** optional speaker notes and material lists

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

## Slide Agent Capability Boundaries

> IMPORTANT: The following defines the hard technical limits of the slide agent. The API enforces these boundaries. The agent MUST respect these limits and inform users when requests exceed them.

### Core Generation Flow

```
Structured Content
    (topic / outline / source document)
        |
        v
HTML Intermediate Structure
    (unified theme, consistent information density)
        |
        v
PPTX Conversion
    (editable layouts, title hierarchy, chart placeholders)
        |
        v
Per-Slide Image Generation
    (nano_banana_pro model)
        |
        v
Final PPTX Delivery
```

### Input Parameters

| Parameter | Description |
|-----------|-------------|
| **Topic / Outline / Pages** | Core content: topic description, structured outline, or page count |
| **Audience & Scenario** | Context: roadshow / pitch / training / review |
| **Visual Preferences** | Optional: brand colors, fonts, style reference |
| **Illustration Source** | Optional: AI-generated images / web images / user-uploaded images |

### Output Deliverables

| Deliverable | Description |
|-------------|-------------|
| **PPTX File** | Editable Microsoft PowerPoint file with layouts, title hierarchy, and chart placeholders |
| **Speaker Notes** | Per-page speaker notes (optional) |
| **Material List** | Image sources and references (optional) |

### Page Structure

| Page Type | Description |
|-----------|-------------|
| **Cover Page** | Title, subtitle, presenter info |
| **Table of Contents** | Navigation overview |
| **Body Pages** | Main content with title hierarchy and chart/image placeholders |
| **Summary Page** | Key takeaways |
| **Appendix Page** | Supplementary materials and references |

### Generation & Processing Limits

| Parameter | Limit |
|-----------|-------|
| Pages Per Generation | Max 30 pages (default 10 pages) |
| Images Per Deck | AI-generated: max 10 images per deck |
| Image Source Priority | User-provided images are preferred; AI generation fills gaps |
| Output Format | PPTX (editable) |

### Image Generation

| Parameter | Specification |
|-----------|-------------|
| Image Model | nano_banana_pro |
| Max AI Images Per Deck | 10 images |
| Illustration Source Options | AI-generated / web images / user-uploaded |

### Output Specifications

| Item | Specification |
|------|--------------|
| PPTX Layouts | Editable |
| Title Hierarchy | Supported |
| Chart Placeholders | Supported |
| Simple Charts | Supported |
| Speaker Notes | Optional (per-page) |
| Material List | Optional (image sources/references) |

---

## Out of Scope

The following are **NOT supported** and the agent will clearly inform users when requests fall into these categories:

| Out of Scope | Reason |
|-------------|--------|
| **Large Data Visualizations** | Multi-dimensional interactive charts and complex dashboards are not supported |
| **Complex Custom Animations / Transitions** | Advanced animation and transition effects are not supported |
| **Strict Brand VI Compliance** | Font, color, and component compliance with strict corporate VI standards is not guaranteed |
| **Image Copyright / Availability** | Image copyright and availability depend on the source; users are responsible for verifying rights |

---

## Practical Application Scenarios

### Product Pitch, Funding Roadshow, Proposal Presentation
Create compelling business presentations with structured layouts, AI-generated illustrations, and professional visual hierarchy. Ideal for product launches, investor pitches, and proposal deliveries.

**Example:** User provides product concept and target audience -> API generates structured PPTX with cover, body slides, summary, and appendix -> AI images generated per page -> Final PPTX delivered with speaker notes.

### Internal Training, Review & Weekly Reports
Build training materials and operational review decks from structured outlines. Support for chart placeholders and simple charts to visualize data.

**Example:** User uploads a training outline or describes a review topic -> API generates training slides with chart placeholders and AI illustrations -> Ready for internal delivery.

### Academic Seminars, Paper Interpretation
Create academic presentation slides from paper summaries or research topics. Structured format with clear title hierarchy and illustration support.

**Example:** User provides a paper topic or abstract -> API generates academic slides with structured layout -> Per-page AI images generated -> Ready for seminar delivery.

### Exhibition & Marketing Event Quick-Intro
Rapidly generate event introduction decks for exhibitions and marketing activations. Fast turnaround with AI-generated visual content.

**Example:** User describes an event theme and key messages -> API generates a quick intro deck -> AI images per slide -> PPTX ready for event use.

---

## API-First Execution Flow

Every action is determined by the API response. The agent follows the `action` field exactly.

### Standard Workflow

```
1. User submits request (topic, outline, visual preferences, illustration source)
       |
2. API returns task_plan
   -> Structured HTML generation
   -> Page-by-page layout planning
   -> nano_banana_pro image generation per page
   -> PPTX conversion
       |
3. Agent executes each step as instructed
       |
4. API returns done -> Present PPTX, speaker notes, material list
```

### Action Routing

| Action | Behavior |
|--------|----------|
| `task_plan` | Execute planned steps in order |
| `call_agent` | Call slide or image generation agent with exact params |
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
IF user provides topic or outline:
  -> Structured content planning
  -> HTML intermediate generation
  -> nano_banana_pro image generation
  -> PPTX conversion
       |
IF user specifies audience and scenario:
  -> Apply relevant visual style and density
  -> Roadshow / pitch / training / review modes
       |
IF user provides visual preferences:
  -> Apply brand colors, fonts, style reference
  -> Prioritize user-provided images
       |
IF user provides illustration source:
  -> Use AI-generated / web images / user-uploaded per selection
  -> AI generation capped at 10 images per deck
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

**Common required fields:**
- `topic` or `outline` — Topic or structured outline
- `pages` — Number of pages (default 10, max 30)
- `audience` — Target audience
- `scenario` — Use case (roadshow / training / review / academic)
- `visual_preferences` — Brand colors, fonts, style reference (optional)
- `illustration_source` — AI-generated / web images / user-uploaded (optional)

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
| `PAGES_EXCEEDED` | Cap at 30 pages, notify user |
| `IMAGES_EXCEEDED` | Cap at 10 AI images per deck, notify user |
| Rate limit | Wait as specified, retry |
| Network error | Retry once, then report |
| `CONTENT_FILTERED` | Inform user, suggest revision |

---

## Quick Reference

| Item | Value |
|------|-------|
| Skill Name | ai-slide |
| Mode | API-first |
| Key Required | Yes |
| Image Model | nano_banana_pro |
| Max Pages Per Generation | 30 pages (default 10) |
| Max AI Images Per Deck | 10 images |
| Image Source Priority | User-provided images preferred |
| Output | PPTX (editable) |
| Title Hierarchy | Supported |
| Chart Placeholders | Supported |
| Simple Charts | Supported |
| Speaker Notes | Optional |
| Material List | Optional |
| Out of Scope | Large data viz, complex animations, strict VI, image copyright |
| Scripts | `scripts/main.py`, `scripts/api_client.py` |
| API Reference | `references/api_reference.md` |
