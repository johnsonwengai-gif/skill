---

# Sub-Agent Capabilities & Limits Reference

> This document contains the combined capability boundaries of all 5 sub-agents available to the AI Chat orchestration agent. The main SKILL.md references this file when planning tasks and routing to sub-agents. All sub-agents are API-first and return action-based responses.

---

## Sub-Agent Registry

| Sub-Agent | Skill Name | Description |
|-----------|-----------|-------------|
| `image` | `ai-image` | Text-to-image, image editing, upscale, background removal/replacement |
| `video` | `ai-video` | Text-to-video, image-to-video, video editing |
| `slide` | `ai-slide` | PPT generation via HTML intermediate, PPTX output |
| `writer` | `ai-writer` | Long-form document generation and format conversion |
| `research` | `deep-research` | Deep research, source retrieval, structured report synthesis |

---

## Image Sub-Agent — `ai-image`

### Capability Boundaries

| Parameter | Limit |
|-----------|-------|
| `text2img` | Supported |
| `img2img` | Supported (when both prompt and input_image provided) |
| `upscale` | 1K → 2K, 2K → 4K, 4K → 8K |
| `background_removal` | Supported |
| `background_replacement` | Supported |
| `text_removal` | Supported |
| `text_removal_enhanced` | Supported |
| Output Formats | PNG, JPG |
| Aspect Ratios | 1:1, 4:5, 16:9, 9:16, 3:2 |
| Resolutions | 1K, 2K, 4K, 8K |
| Max Images Per Request | 12 |
| Max Reference Images (img2img) | 10 |
| Max Upscale Resolution | 8K |
| Auto-Retry | 3 attempts on failure |

### Input Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `prompt` | Yes (for text2img/img2img) | Text description |
| `input_image` | No | Reference image for img2img |
| `model` | No | Model identifier |
| `aspect_ratio` | No | Output aspect ratio |
| `resolution` | No | Output resolution |
| `output_format` | No | PNG (default) or JPG |
| `style_preset` | No | Style preset |
| `seed` | No | Random seed |
| `image_count` | No | Number of images (max 12) |

### Output

```json
{
  "action": "done",
  "data": {
    "images": [{"url": "<url>", "width": 1024, "height": 1024, "format": "PNG"}],
    "model": "<model>",
    "processing_time_seconds": 12
  }
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `INVALID_API_KEY` | Key invalid or expired |
| `CREDITS_EXHAUSTED` | No credits remaining |
| `CONTENT_FILTERED` | Prompt blocked by policy |
| `IMAGE_TOO_SMALL` | Upscale target below minimum |
| `RESOLUTION_EXCEEDED` | Resolution exceeds 8K |
| `REFERENCE_IMAGES_EXCEEDED` | More than 10 reference images |
| `RATE_LIMIT_EXCEEDED` | Too many requests |

---

## Video Sub-Agent — `ai-video`

### Capability Boundaries

| Parameter | Limit |
|-----------|-------|
| `text2video` | Supported |
| `image2video` | Supported |
| `video_extensions` | Supported |
| `video_merge` | Supported |
| Duration | 6s or 10s |
| Resolution | 768P or 1080P (10s + 1080P → auto-downgrade to 768P) |
| Aspect Ratios | 16:9 (landscape), 9:16 (vertical), 1:1 (square) |
| Video Merge | Up to 5 clips merged per request |
| Text2Video Model | Default: unspecified; configurable |

### Input Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `prompt` | Yes (for text2video) | Text description of the video scene |
| `input_image` | Yes (for image2video) | Source image (min 300px short side) |
| `duration` | No | 6 (default) or 10 seconds |
| `resolution` | No | 768P (default) or 1080P |
| `aspect_ratio` | No | 16:9 / 9:16 / 1:1 |
| `negative_prompt` | No | Elements to avoid |
| `seed` | No | Random seed |
| `video_count` | No | Number of videos (max 5) |
| `reference_type` | No | `first_frame` or `subject` (for image2video) |

### Output

```json
{
  "action": "done",
  "data": {
    "videos": [{"url": "<url>", "duration": 6, "resolution": "768P", "format": "MP4"}],
    "processing_time_seconds": 45
  }
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `INVALID_API_KEY` | Key invalid or expired |
| `CREDITS_EXHAUSTED` | No credits remaining |
| `CONTENT_FILTERED` | Prompt or image blocked by policy |
| `IMAGE_TOO_SMALL` | Input image below 300px minimum |
| `DURATION_CONFLICT` | 10s + 1080P combination triggers auto-downgrade |
| `MERGE_CLIPS_EXCEEDED` | More than 5 clips in merge request |
| `RATE_LIMIT_EXCEEDED` | Too many requests |

---

## Slide Sub-Agent — `ai-slide`

### Capability Boundaries

| Parameter | Limit |
|-----------|-------|
| Input Formats | docx, txt, html, markdown, notion, feishu-doc, url, image |
| Output Formats | PPTX (editable), HTML |
| Pages Per Generation | Max 30 pages (default: 10) |
| AI Images Per Deck | Max 10 (nano_banana_pro model) |
| Image Source Priority | User-provided images preferred over AI generation |
| Max Decks Per Request | 10 |
| Max Slides Per PPT | 200 slides |
| Image Model | nano_banana_pro |
| Template Gallery | Supported |
| Online PPT | Supported |
| Style Presets | 12 presets |
| Page / Illustration / Chart Themes | 5 each |
| Translation Languages | 12 languages |
| Max Translation Per Request | 10 PPTs |
| Translation Output | PPTX only |

### Out of Scope

| Item | Reason |
|------|--------|
| Large data visualizations | Multi-dimensional interactive charts not supported |
| Complex custom animations / transitions | Not supported |
| Strict Brand VI compliance | Font, color, component accuracy not guaranteed |
| Image copyright / availability | User responsibility |

### Input Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `topic` or `outline` | Yes | Topic or structured outline |
| `pages` | No | Number of pages (default: 10, max: 30) |
| `audience` | No | investor / client / employee / academic / general |
| `scenario` | No | roadshow / pitch / training / review / academic / event |
| `visual_preferences` | No | Brand colors, fonts, style reference |
| `illustration_source` | No | `ai_generated` / `web_images` / `user_uploaded` |
| `image_count` | No | Number of AI images to generate (max: 10) |
| `image_model` | No | Default: nano_banana_pro |
| `speaker_notes` | No | Generate per-page speaker notes (default: false) |
| `material_list` | No | Generate image source reference (default: false) |
| `output_format` | No | PPTX (default) or HTML |

### Output

```json
{
  "action": "done",
  "data": {
    "outputs": {
      "pptx_url": "<url>",
      "html_url": "<url>",
      "speaker_notes_url": "<url_or_null>",
      "material_list_url": "<url_or_null>"
    },
    "pages_generated": 10,
    "images_generated": 5,
    "image_model": "nano_banana_pro"
  }
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `INVALID_API_KEY` | Key invalid or expired |
| `CREDITS_EXHAUSTED` | No credits remaining |
| `PAGES_EXCEEDED` | Pages exceed 30 |
| `IMAGES_EXCEEDED` | AI images exceed 10 |
| `UNSUPPORTED_FORMAT` | Input format not supported |
| `UNSUPPORTED_SCENARIO` | Scenario not in supported list |
| `CONTENT_FILTERED` | Content blocked by policy |
| `RATE_LIMIT_EXCEEDED` | Too many requests |

---

## Writer Sub-Agent — `ai-writer`

### Capability Boundaries

| Parameter | Limit |
|-----------|-------|
| Output Formats | Markdown, Word (DOCX), PDF, HTML |
| Max Single Generation | Recommended max 20,000 characters |
| Iterative Revision | Supported — multiple rounds |
| Cover Page | Optional |
| Table of Contents | Optional |
| Title Hierarchy | H1–H6 |
| Tables | Supported |
| Images | Supported |
| Basic Formulas | Basic support (complex LaTeX may degrade) |
| Footnotes / References | Basic support |

### Document Types Supported

| Type | Description |
|------|-------------|
| `resume` | Professional resume / CV |
| `personal_statement` | Personal statement / cover letter |
| `proposal` | Business proposal / bid document |
| `prd` | Product Requirements Document |
| `technical_spec` | Technical specification |
| `weekly_report` | Weekly work report |
| `monthly_report` | Monthly progress report |
| `review_report` | Project / period review report |
| `meeting_minutes` | Meeting minutes and action items |
| `whitepaper` | Industry / technical whitepaper |
| `product_manual` | Product user manual |
| `project_intro` | Project introduction |
| `other` | Other document types |

### Out of Scope

| Item | Reason |
|------|--------|
| Ultra-long manuscripts | >50,000 characters / dozens of chapters — single-run not supported |
| Mass batch generation | >100 articles or >1000 titles per request — not supported |
| Complex rich layouts | Multi-column / floating objects; precise consistency not guaranteed |
| Complex LaTeX formulas | Basic formulas only; advanced LaTeX degrades |
| High-risk legal / medical / financial text | Legal clauses for signing, medical conclusions, financial advice — not promised |

### Input Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `document_type` | Yes | Document category (see table above) |
| `content` | Yes | Content source: bullet points, outline, or reference description |
| `target_format` | Yes | `markdown` / `word` / `pdf` / `html` |
| `style` | No | Layout style: `formal` (default) / `simple` |
| `include_toc` | No | Include table of contents (default: true) |
| `include_cover` | No | Include cover page (default: true) |
| `brand_colors` | No | Brand color codes or descriptions |
| `language` | No | Document language (default: auto-detected) |
| `max_length` | No | Max character target (default: 20000, recommended max) |

### Output

```json
{
  "action": "done",
  "data": {
    "outputs": {
      "markdown_url": "<url>",
      "word_url": "<url>",
      "pdf_url": "<url>",
      "html_url": "<url>"
    },
    "document_type": "prd",
    "character_count": 12500,
    "version": 1,
    "formats_delivered": ["markdown", "word"]
  }
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `INVALID_API_KEY` | Key invalid or expired |
| `CREDITS_EXHAUSTED` | No credits remaining |
| `LENGTH_EXCEEDED` | Content exceeds 20,000 characters |
| `MANUSCRIPT_TOO_LONG` | Book-length or >50,000 characters requested |
| `BATCH_TOO_LARGE` | >100 articles or >1000 titles requested |
| `UNSUPPORTED_DOC_TYPE` | Document type not in supported list |
| `CONVERSION_FAILED` | Markdown to target format conversion failed |
| `CONTENT_FILTERED` | Content blocked by policy |
| `RATE_LIMIT_EXCEEDED` | Too many requests |

---

## Research Sub-Agent — `deep-research`

### Capability Boundaries

| Parameter | Limit |
|-----------|-------|
| Output | Markdown report (editable, revision supported) |
| Report Length | 2,000 – 15,000 characters |
| Max External Source Links | 30 per report |
| Max Text Per Source | 200 KB pure text |
| Iterative Revision | Supported — multiple rounds |
| Data Source Types | Public web, papers, user-uploaded materials |
| Citations | Footnotes + source links; all sources attributed |

### Input Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `topic` or `research_question` | Yes | Core research subject or question |
| `scope` | No | Region, time period, industry, data caliber / definition |
| `audience` | Yes | `general` / `consulting` / `investor` / `technical` |
| `style` | Yes | `popular_science` / `consulting` / `investment` / `technical` |
| `sources` | No | List of public URLs, file references, or user materials |
| `min_length` | No | Minimum character target (default: 2000) |
| `max_length` | No | Maximum character target (default: 15000) |

### Out of Scope

| Item | Reason |
|------|--------|
| Paywalled / inaccessible content | Completeness not guaranteed for paid sources |
| Real-time fact verification | Not a final factual authority; re-verification needed |
| Long copyrighted text output | Content paraphrased or summarized; no direct copying |

### Output

```json
{
  "action": "done",
  "data": {
    "outputs": {
      "markdown_url": "<url>",
      "summary": "<abstract_text>",
      "key_points": ["<bullet1>", "<bullet2>"],
      "character_count": 8500,
      "source_count": 18,
      "citation_count": 18
    },
    "report_structure": ["summary", "key_points", "analysis", "conclusions", "citations"],
    "style": "consulting",
    "sources_used": 18,
    "sources_limit": 30
  }
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `INVALID_API_KEY` | Key invalid or expired |
| `CREDITS_EXHAUSTED` | No credits remaining |
| `SOURCES_EXCEEDED` | More than 30 sources requested |
| `SOURCE_TOO_LARGE` | Source exceeds 200 KB pure text |
| `LENGTH_OUT_OF_RANGE` | Report length outside 2,000–15,000 range |
| `PAYWALL_DETECTED` | Source behind paywall; note and skip |
| `RETRIEVAL_FAILED` | Source retrieval failed; skip and continue |
| `CONTENT_FILTERED` | Content blocked by policy |
| `RATE_LIMIT_EXCEEDED` | Too many requests |

---

## Cross-Modal Reuse Routing Table

> When a sub-agent completes, the AI Chat agent checks whether downstream sub-tasks exist and automatically routes output as input to the next sub-agent.

| Upstream Output | Downstream Target | Routing Trigger |
|----------------|-------------------|-----------------|
| Research report (Markdown) | `slide` | User requests PPT from report |
| Research report (Markdown) | `video` | User requests video summary of report |
| Slide deck (PPTX) | `video` | User requests video walkthrough of PPT |
| Images (any) | `slide` | User requests cover / illustration images |
| Images (any) | `video` | User requests video using generated images |
| Writer output (Markdown) | `slide` | User requests slides from document |
| Writer output (Markdown) | `video` | User requests video narration of document |
| PPTX | `image` | User requests cover or asset images |

---

## Sub-Agent Selection Quick Reference

| Task Hint in User Request | Primary Sub-Agent |
|--------------------------|-------------------|
| Generate / create image | `image` |
| Create video / animate | `video` |
| Create slides / PPT / presentation | `slide` |
| Write document / report / resume | `writer` |
| Research / investigate / analyze | `research` |
| Make PPT from report | `research` → `slide` (chain) |
| Video from slides | `slide` → `video` (chain) |
| Cover image for report | `image` |
| Video summary of report | `research` → `video` (chain) |
| Multiple tasks simultaneously | Parallel `call_agent` to relevant sub-agents |
