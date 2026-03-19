---
description: Deep Research Agent — An intelligent orchestration agent that analyzes research requests, retrieves and synthesizes information from public sources, and produces structured long-form research reports with citations. All actions are driven by SSE events received from the backend workflow API. Triggers when users want to conduct deep research, market analysis, policy review, or academic surveys.
name: deep-research
---

# Deep Research — Intelligent Research Report Agent

> Research orchestration agent. Plans, retrieves, synthesizes, and writes structured reports — all guided by the API.

---

## Prerequisites — API Key Setup

> Before using this skill, you must register and purchase an API key.

**Step 1: Register and Purchase**
Visit the platform to register your account and purchase an API key:
> `https://your-platform-domain.com/register`

**Step 2: Enter Your API Key**
After purchasing, provide your API key. The system will verify it before enabling research capabilities.

**Step 3: Verify Access**
Once verified, all research capabilities become available immediately.

> Credits / Quota: Each research task consumes credits based on source retrieval and report length. If your balance is insufficient, you will be prompted to purchase additional credits at:
> `https://your-platform-domain.com/pricing`

---

## What Is Deep Research?

Deep Research is an **intelligent research orchestration agent** that transforms a research question or topic into a comprehensive, structured, source-cited report.

1. **Analyzes** the research topic, scope, audience, and style
2. **Retrieves** publicly accessible web pages, papers, and user-provided materials
3. **Synthesizes** findings into structured argumentation with evidence
4. **Writes** a long-form report: summary, key points, analysis, conclusions, and citations
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

## Deep Research Capability Boundaries

> IMPORTANT: The following defines the hard technical limits of the deep research agent. The API enforces these boundaries. The agent MUST respect these limits and inform users when requests exceed them.

### Research Flow

```
Research Topic / Question
    (topic + scope + audience + style)
        |
        v
Public Source Retrieval
    (web pages / papers / user materials — max 30 sources)
        |
        v
Synthesis & Analysis
    (structured argumentation, evidence extraction)
        |
        v
Long-Form Report Writing
    (summary / key points / analysis / conclusions / citations)
        |
        v
Editable Markdown Output
    (with footnote and link citations, revision support)
```

### Input Parameters

| Parameter | Description |
|-----------|-------------|
| **Research Topic / Question** | Core question or research subject |
| **Scope & Constraints** | Region, time period, industry, data caliber / definition |
| **Audience & Style** | Popular science / consulting / investment research / technical |
| **Data Sources** | Public URLs, files, or user-provided materials (optional) |

### Output Specifications

| Deliverable | Description |
|-------------|-------------|
| **Markdown Report** | Editable source document; supports iterative revision |
| **Summary** | Abstract / TL;DR of the research |
| **Key Points** | Bullet-pointed main findings |
| **Analysis & Argumentation** | Structured body with evidence and reasoning |
| **Conclusions** | Findings and implications |
| **Citation List** | Footnotes and source links; all sources attributed |

### Report Structure

| Section | Description |
|---------|-------------|
| **Summary / Abstract** | High-level overview of the research |
| **Key Points** | Main findings in bullet form |
| **Analysis & Discussion** | Structured argumentation with evidence |
| **Conclusions** | Final findings and implications |
| **Citations** | Footnote references and URLs for all sources |

### Data Source Policy

| Rule | Description |
|------|-------------|
| **Public sources only** | Only publicly accessible web pages, papers, and user-uploaded materials |
| **Source citation required** | All sources must be cited with links in the output |
| **Paywall content** | Not guaranteed; inaccessible paid content may reduce completeness |
| **Real-time verification** | Time-sensitive information may require fresh retrieval; not treated as final fact |
| **No long copyright text** | Long direct quotes are avoided; content is summarized and paraphrased |

---

## Generation Limits

| Parameter | Limit |
|-----------|-------|
| External Source Links Per Report | Max 30 sources |
| Text Extraction Per Source | Max 200 KB pure text |
| Report Output Length | 2,000 – 15,000 characters |
| Iterative Revision | Supported — multiple rounds |

---

## Out of Scope

The following are **NOT supported** and the agent will clearly inform users:

| Out of Scope | Reason |
|-------------|--------|
| **Paywalled / Inaccessible Content** | Only publicly accessible information is retrieved; completeness not guaranteed for paid sources |
| **Real-Time Fact Verification** | The agent does not make "final factual rulings"; real-time information should be re-verified independently |
| **Long Copyright Text Output** | Direct copying of long copyrighted passages is avoided; all content is paraphrased or summarized |

---

## Practical Application Scenarios

### Industry & Competitive Research, Market Size & Trend Analysis
Conduct comprehensive market or competitive research with sourced data, trend identification, and structured conclusions.

**Example:** User provides a research topic and target industry -> API retrieves publicly available reports and articles -> Synthesizes findings into a structured report with citations -> Returns Markdown with summary, key points, and footnote references.

### Policy / Regulation / Standard Interpretation (with Source Citations)
Analyze and interpret policies, regulations, or technical standards with proper source attribution.

**Example:** User describes a policy topic and relevant jurisdiction -> API retrieves official documents and commentary -> Writes a structured report with section-by-section interpretation and source links.

### Academic / Technical Survey (Comparison Tables + Citations)
Produce academic literature or technical surveys with comparison tables and properly cited references.

**Example:** User provides a technical topic and scope -> API retrieves relevant papers and technical articles -> Writes a survey with comparison tables and numbered citations.

### Solution / Vendor / Approach Evaluation (Pros, Cons, Risks, Recommendations)
Compare solutions or approaches with structured pros/cons analysis and risk assessment.

**Example:** User describes evaluation criteria and candidate solutions -> API researches each option from public sources -> Produces a structured comparison report with risk analysis and recommendations.

---

## API-First Execution Flow

Every action is determined by the API response. The agent follows the `action` field exactly.

### Standard Workflow

```
1. User submits request (topic, scope, audience, style, sources)
       |
2. API returns task_plan
   -> Source retrieval planning (max 30 public sources)
   -> Text extraction (max 200 KB per source)
   -> Synthesis and analysis
   -> Report writing (2k–15k chars)
   -> Citation generation
       |
3. Agent executes each step as instructed
       |
4. API returns done -> Present final report with citations
```

### Action Routing

| Action | Behavior |
|--------|----------|
| `task_plan` | Execute planned steps in order |
| `call_agent` | Call research, retrieval, or writing agent with exact params |
| `call_api` | Call API with provided parameters |
| `request_parameter` | Ask user for required fields |
| `wait_user_confirm` | Show preview, wait for confirmation |
| `revision` | Execute revision round, produce new version |
| `done` | Deliver final output |
| `credit_warning` | Inform user, let them decide |
| `credit_exhausted` | Stop, prompt purchase |
| `error` | Report to user |

---

## Capability Routing Rules

The API automatically routes based on task parameters:

```
IF user provides research topic:
  -> Define scope: region / time / industry / caliber
  -> Plan retrieval strategy
       |
IF user specifies audience and style:
  -> Apply writing tone: popular science / consulting / investment research / technical
       |
IF user provides data sources (URLs / files):
  -> Retrieve from provided sources first
  -> Supplement with public web retrieval
       |
IF no sources provided:
  -> Public web search and paper retrieval
  -> Max 30 external sources per report
  -> Max 200 KB text extraction per source
       |
IF user requests iterative revision:
  -> Markdown editing mode
  -> Each round produces a new editable version
       |
Report output: 2,000–15,000 characters in Markdown
  -> Summary, key points, analysis, conclusions, citations
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
- `topic` or `research_question` — Core research subject
- `scope` — Region, time period, industry, caliber (optional but recommended)
- `audience` — Target reader: general / consulting / investor / technical
- `style` — Writing style: popular_science / consulting / investment / technical
- `sources` — URLs, files, or user materials (optional)
- `min_length` — Minimum character target (optional, default: 2000)
- `max_length` — Maximum character target (optional, default: 15000)

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
| `SOURCES_EXCEEDED` | Cap at 30 sources, notify user |
| `SOURCE_TOO_LARGE` | Truncate at 200 KB per source, notify user |
| `LENGTH_OUT_OF_RANGE` | Adjust to 2k–15k range, notify user |
| `PAYWALL_DETECTED` | Note limitation, proceed with accessible sources |
| Rate limit | Wait as specified, retry |
| Network error | Retry once, then report |
| `CONTENT_FILTERED` | Inform user, suggest revision |

---

## Quick Reference

| Item | Value |
|------|-------|
| Skill Name | deep-research |
| Mode | API-first |
| Key Required | Yes |
| Input | Research topic + scope + audience + style + optional sources |
| Output | Markdown report (editable, revision support) |
| Report Length | 2,000 – 15,000 characters |
| Max Sources Per Report | 30 external links |
| Max Text Per Source | 200 KB pure text |
| Source Types | Public web, papers, user-uploaded materials |
| Citations | Footnotes + links, all sources attributed |
| Iterative Revision | Supported |
| Out of Scope | Paywall/ inaccessible content completeness, real-time fact verification, long copyright text |
| Scripts | `scripts/main.py`, `scripts/api_client.py` |
| API Reference | `references/api_reference.md` |
