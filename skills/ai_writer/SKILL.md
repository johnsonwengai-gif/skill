---
description: AI Writer Agent — An intelligent orchestration agent that analyzes complex document generation requests, plans multi-step workflows, and produces structured documents in Markdown, Word, PDF, or HTML format. All actions are driven by SSE events received from the backend workflow API. Triggers when users want to create, edit, or plan document writing tasks.
name: ai-writer
---

# AI Writer — Intelligent Document Generation Agent

> Document generation orchestrator. Plans, coordinates, and executes document creation workflows — all guided by the API.

---

## Prerequisites — API Key Setup

> Before using this skill, you must register and purchase an API key.

**Step 1: Register and Purchase**
Visit the platform to register your account and purchase an API key:
> `https://your-platform-domain.com/register`

**Step 2: Enter Your API Key**
After purchasing, provide your API key. The system will verify it before enabling document generation capabilities.

**Step 3: Verify Access**
Once verified, all document generation capabilities become available immediately.

> Credits / Quota: Each document generation task consumes credits. If your balance is insufficient, you will be prompted to purchase additional credits at:
> `https://your-platform-domain.com/pricing`

---

## What Is AI Writer?

AI Writer is an **intelligent document generation orchestration agent** that transforms input requirements into structured, professionally formatted documents.

1. **Classifies** the document type and intended use case
2. **Plans** content structure, layout, and conversion pipeline
3. **Generates** Markdown content with full structural markup
4. **Converts** to target format (Word / PDF / HTML) with styled templates
5. **Iterates** based on user feedback for revision rounds

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

## Writer Agent Capability Boundaries

> IMPORTANT: The following defines the hard technical limits of the writer agent. The API enforces these boundaries. The agent MUST respect these limits and inform users when requests exceed them.

### Document Generation Flow

```
Input Requirements
    (type / source / layout preferences)
        |
        v
Markdown Content Generation
    (structured: cover, TOC, title hierarchy, tables, images)
        |
        v
Template-Based Conversion
    (Word / PDF / HTML with styled output)
        |
        v
Final Document Delivery
```

### Input Parameters

| Parameter | Description |
|-----------|-------------|
| **Document Type** | Resume, proposal, PRD, weekly report, monthly report, whitepaper, technical spec, pitch deck, personal statement, project intro, meeting minutes, etc. |
| **Content Source** | User-provided bullet points, outline, reference documents, images, or descriptions |
| **Layout Preferences** | Style: formal / simple; brand colors; table of contents: yes/no; cover page: yes/no |

### Supported Output Formats

| Format | Description |
|--------|-------------|
| **Markdown** | Editable source, multi-version revision support |
| **Word** | DOCX with styled headings, tables, and image placeholders |
| **PDF** | Formatted print-ready PDF with cover, TOC, and styled body |
| **HTML** | Web-ready HTML with full layout styling |

### Document Structure Support

| Element | Supported |
|---------|-----------|
| Cover Page | Yes |
| Table of Contents (TOC) | Yes |
| Title Hierarchy (H1–H6) | Yes |
| Tables | Yes |
| Images / Figures | Yes |
| Code Blocks | Yes |
| Basic Formulas | Basic support (complex LaTeX may degrade) |
| Footnotes / References | Basic support |
| Multi-Version Revision | Yes — iterative rewriting supported |

---

## Generation Limits

| Parameter | Limit |
|-----------|-------|
| Single Generation | Recommended max 20,000 Chinese/English characters |
| Iterative Revision | Supported — multiple revision rounds |
| Output Versions | Multiple editable versions maintained in Markdown |

---

## Out of Scope

The following are **NOT supported** and the agent will clearly inform users when requests fall into these categories:

| Out of Scope | Reason |
|-------------|--------|
| **Ultra-Long Manuscripts** | Single-run generation of book-length content (>50,000 characters / dozens of chapters) is not supported |
| **Mass Batch Generation** | Generating 100+ articles or 1000+ titles in a single batch is not supported |
| **Complex Multi-Column / Floating Objects** | Intricate图文混排 (rich text with floating objects, multi-column layouts) and precise layout consistency across pages are not guaranteed |
| **Complex LaTeX Formulas** | Advanced LaTeX equation rendering degrades; basic formulas supported |
| **High-Risk Legal / Medical / Financial Text** | Legal clauses for direct signing, medical conclusions, or high-stakes financial advice are not promised; consult a professional |

---

## Practical Application Scenarios

### PRD / Technical Spec / Bid Proposal Drafts
Generate structured product requirement documents, technical specifications, or bidding proposal drafts from outlines and reference materials.

**Example:** User provides a PRD outline or feature list -> API generates structured Markdown -> Converts to Word or PDF -> Returns formatted document ready for review.

### Meeting Minutes, Weekly / Monthly Reports, Review Reports
Rapidly produce structured reports from bullet points, meeting notes, or data summaries.

**Example:** User provides meeting notes or weekly bullet points -> API generates formatted Markdown with title hierarchy and tables -> Converts to Word or PDF -> Ready to distribute.

### Resume, Personal Statement, Project Introduction
Create professional personal documents with clean layout, formal style, and brand-consistent formatting.

**Example:** User provides personal background and achievement bullet points -> API generates structured resume or personal statement in Markdown -> Converts to Word -> Delivered in editable format for further tuning.

### External Whitepapers / Product Manuals
Produce long-form explanatory documents such as whitepapers and product manuals with cover pages, TOC, and styled sections.

**Example:** User describes the topic and target audience -> API generates structured whitepaper in Markdown -> Converts to HTML or PDF -> Ready for publication or distribution.

---

## API-First Execution Flow

Every action is determined by the API response. The agent follows the `action` field exactly.

### Standard Workflow

```
1. User submits request (type, source, layout preferences, target format)
       |
2. API returns task_plan
   -> Document type classification
   -> Content structure planning
   -> Markdown generation
   -> Template conversion to target format
       |
3. Agent executes each step as instructed
       |
4. API returns done -> Present final document
```

### Action Routing

| Action | Behavior |
|--------|----------|
| `task_plan` | Execute planned steps in order |
| `call_agent` | Call writer or converter agent with exact params |
| `call_api` | Call API with provided parameters |
| `request_parameter` | Ask user for required fields |
| `wait_user_confirm` | Show preview, wait for confirmation |
| `done` | Deliver final output |
| `revision` | Execute revision round, produce new version |
| `credit_warning` | Inform user, let them decide |
| `credit_exhausted` | Stop, prompt purchase |
| `error` | Report to user |

---

## Capability Routing Rules

The API automatically routes based on task parameters:

```
IF user specifies document type:
  -> Apply relevant template and structure
  -> Resume / PRD / whitepaper / report / proposal / etc.
       |
IF user provides content source:
  -> Generate from: bullet points / outline / reference docs / images
       |
IF user specifies layout preferences:
  -> Apply: formal / simple style
  -> Brand colors if provided
  -> TOC and cover page per preference
       |
IF user requests iterative revision:
  -> Markdown multi-version editing mode
  -> Each round produces new editable version
       |
IF user requests specific output format:
  -> Markdown: direct output, editable
  -> Word: DOCX conversion with styled template
  -> PDF: formatted PDF with cover, TOC, styled body
  -> HTML: styled web-ready HTML
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
- `document_type` — Document category (resume / proposal / PRD / report / whitepaper / etc.)
- `content` — Content source: bullet points, outline, or reference description
- `target_format` — Output format: Markdown / Word / PDF / HTML
- `style` — Layout style: formal / simple (optional)
- `include_toc` — Whether to include table of contents (optional, default: true)
- `include_cover` — Whether to include cover page (optional, default: true)
- `brand_colors` — Brand color codes (optional)

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
| `LENGTH_EXCEEDED` | Cap at 20,000 characters, suggest splitting or shortening |
| `REVISION_LIMIT` | Notify user revision limit reached |
| Rate limit | Wait as specified, retry |
| Network error | Retry once, then report |
| `CONTENT_FILTERED` | Inform user, suggest revision |
| `UNSUPPORTED_DOC_TYPE` | List supported document types |

---

## Quick Reference

| Item | Value |
|------|-------|
| Skill Name | ai-writer |
| Mode | API-first |
| Key Required | Yes |
| Input | Document type + content source + layout preferences |
| Output Formats | Markdown, Word (DOCX), PDF, HTML |
| Max Single Generation | Recommended max 20,000 characters |
| Iterative Revision | Supported |
| Cover Page | Optional |
| Table of Contents | Optional |
| Title Hierarchy | H1–H6 |
| Tables | Yes |
| Images | Yes |
| Basic Formulas | Basic support |
| Footnotes / References | Basic support |
| Out of Scope | Ultra-long books (>50k chars), mass batch, complex rich layouts, LaTeX, legal/medical/financial high-risk text |
| Scripts | `scripts/main.py`, `scripts/api_client.py` |
| API Reference | `references/api_reference.md` |
