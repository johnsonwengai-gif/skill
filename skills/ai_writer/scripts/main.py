#!/usr/bin/env python3
"""
AI Writer — Main orchestration script.
Routes document generation and conversion requests through the API loop until done/error/revision.
Usage:
  # Generate a PRD in Word format
  python3 main.py --type prd --content "Feature: user dashboard..." --format word --key KEY

  # Generate a resume in Markdown with revision
  python3 main.py --type resume --content "Name:... Experience:..." --format markdown --key KEY

  # Generate and convert to multiple formats
  python3 main.py --type whitepaper --content "..." --format pdf --style formal --toc --cover --key KEY
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_client import create_chat, verify_key

# Capability limits
MAX_CHARS_PER_GENERATION = 20000
RECOMMENDED_MAX_CHARS = 20000
MAX_MANUSCRIPT_CHARS = 50000

SUPPORTED_DOC_TYPES = [
    "resume", "personal_statement", "proposal", "prd",
    "technical_spec", "weekly_report", "monthly_report",
    "review_report", "meeting_minutes", "whitepaper",
    "product_manual", "project_intro", "other"
]
SUPPORTED_OUTPUT_FORMATS = ["markdown", "word", "pdf", "html"]
SUPPORTED_STYLES = ["formal", "simple"]

OUT_OF_SCOPE = [
    "Ultra-long book manuscripts (>50,000 characters / dozens of chapters)",
    "Mass batch generation (>100 articles or >1000 titles in one request)",
    "Complex multi-column / floating object layouts (precise consistency not guaranteed)",
    "Complex LaTeX formula rendering (basic formulas supported only)",
    "High-risk legal clauses, medical conclusions, or financial advice (not promised)",
]


def validate_params(params: dict) -> tuple:
    """Validate request against capability limits. Returns (valid, message, out_of_scope_flags)."""
    issues = []
    oos_flags = []

    content = params.get("content", "")
    char_count = len(content)
    max_len = params.get("max_length", RECOMMENDED_MAX_CHARS)

    if char_count > MAX_MANUSCRIPT_CHARS:
        oos_flags.append(f"Content length ({char_count}) exceeds ultra-long manuscript threshold ({MAX_MANUSCRIPT_CHARS}).")
        issues.append(f"Content is too long for a single generation. Please split into multiple parts.")

    doc_type = params.get("document_type", "")
    batch = params.get("batch", False)
    if batch:
        oos_flags.append("Batch generation requested.")
        issues.append("Batch generation (>100 articles or >1000 titles) is not supported.")

    style = params.get("style", "formal")
    if style not in SUPPORTED_STYLES:
        issues.append(f"Style '{style}' not supported. Use: {', '.join(SUPPORTED_STYLES)}.")

    fmt = params.get("target_format", "markdown")
    if fmt not in SUPPORTED_OUTPUT_FORMATS:
        issues.append(f"Format '{fmt}' not supported. Use: {', '.join(SUPPORTED_OUTPUT_FORMATS)}.")

    return (False, " ".join(issues), oos_flags) if issues else (True, "OK", oos_flags)


def run_loop(client: APIClient, user_message: str):
    messages = [{"role": "user", "content": user_message}]
    step = 0
    version = 1

    while True:
        step += 1
        context = {"step": step, "version": version}
        resp = client.chat(messages, context=context)
        action = resp.get("action")
        msg = resp.get("message", "")

        print(f"[Step {step}] Action: {action} - {msg}")

        if action == "done":
            outputs = resp.get("data", {}).get("outputs", {})
            print(f"\n[DONE] Document generated successfully!")
            for fmt_key, url in outputs.items():
                if url:
                    print(f"[OUTPUT] {fmt_key.upper()}: {url}")
            print(f"[INFO] Document type: {resp.get('data', {}).get('document_type', 'N/A')}")
            print(f"[INFO] Character count: {resp.get('data', {}).get('character_count', 'N/A')}")
            print(f"[INFO] Version: {resp.get('data', {}).get('version', version)}")
            print(f"[CREDITS] Consumed: {resp.get('meta', {}).get('total_credits_consumed', 'N/A')}")
            break

        elif action == "call_agent":
            d = resp["data"]
            params = d.get("params", {})
            agent = d.get("agent", "writer")

            if agent in ("writer", "document"):
                valid, hint, oos_flags = validate_params(params)
                if not valid:
                    print(f"[WARN] {hint}")
                    if oos_flags:
                        print(f"[INFO] Out-of-scope items detected:")
                        for item in oos_flags: print(f"  - {item}")
                    messages.append({"role": "user", "content": f"Adjusted: {hint}"})
                    continue

                doc_type = params.get("document_type", "N/A")
                target_fmt = params.get("target_format", "markdown")
                style = params.get("style", "formal")
                toc = params.get("include_toc", True)
                cover = params.get("include_cover", True)
                content_preview = str(params.get("content", ""))[:80]

                print(f"[INFO] Calling writer agent:")
                print(f"  Document type: {doc_type}")
                print(f"  Target format: {target_fmt}")
                print(f"  Style: {style} | TOC: {toc} | Cover: {cover}")
                print(f"  Content: {content_preview}...")

            elif agent == "converter":
                src_fmt = params.get("source_format", "markdown")
                target_fmt = params.get("target_format", "N/A")
                print(f"[INFO] Calling converter agent: {src_fmt} -> {target_fmt}")

            sub_resp = client.call_agent(agent, params)
            messages.append({"role": "assistant", "content": json.dumps(sub_resp)})

        elif action == "revision":
            version = resp.get("data", {}).get("version", version + 1)
            changes = resp.get("data", {}).get("changes_summary", "")
            markdown_url = resp.get("data", {}).get("markdown_url", "")
            revision_count = resp.get("data", {}).get("revision_count", 0)
            print(f"[REVISION] Version {version} ready (revision #{revision_count}).")
            print(f"[INFO] Changes: {changes}")
            print(f"[OUTPUT] Markdown: {markdown_url}")
            user_confirm = input("  Accept this revision? (yes/no/revise): ").strip().lower()
            messages.append({"role": "user", "content": user_confirm})

        elif action == "request_parameter":
            fields = resp["data"].get("required_fields", [])
            print(f"[INFO] Required fields: {[f['name'] for f in fields]}")
            answers = {}
            for f in fields:
                val = input(f"  {f['label']}: ").strip()
                if val: answers[f["name"]] = val
            messages.append({"role": "user", "content": f"Additional info: {json.dumps(answers)}"})

        elif action == "wait_user_confirm":
            preview = resp["data"].get("preview", "")
            confirm_prompt = resp["data"].get("confirm_prompt", "Approve this version? (yes/no/revise)")
            print(f"[PREVIEW] {str(preview)[:200]}")
            user_input = input(f"  {confirm_prompt} ").strip().lower()
            messages.append({"role": "user", "content": user_input})

        elif action == "credit_warning":
            bal = resp["data"].get("remaining_credits", 0)
            est = resp["data"].get("estimated_credits_for_completion", 0)
            print(f"[WARN] Low credits ({bal}). Estimated for task: {est}")
            proceed = input("  Continue anyway? (yes/no): ").strip().lower()
            messages.append({"role": "user", "content": proceed})

        elif action == "credit_exhausted":
            partial = resp["data"].get("partial_output", {})
            print(f"[ERROR] Credits exhausted. Partial results: {partial}")
            print(f"[INFO] Purchase credits: https://your-platform-domain.com/pricing")
            break

        elif action == "error":
            err = resp.get("error", {})
            code = err.get("code", "UNKNOWN")
            details = err.get("details", "")
            recoverable = resp.get("data", {}).get("recoverable", False)
            print(f"[ERROR] {code}: {details}")
            if recoverable:
                user_input = input("  Provide correction: ").strip()
                messages.append({"role": "user", "content": user_input})
            else:
                break

        else:
            print(f"[WARN] Unknown action '{action}'.")
            print(json.dumps(resp, ensure_ascii=False, indent=2))
            break


def main():
    parser = argparse.ArgumentParser(
        description="AI Writer — Intelligent Document Generation Agent")
    parser.add_argument("--key", default=os.getenv("API_KEY", ""))
    parser.add_argument("--url", default=os.getenv("API_URL", "https://api.your-platform-domain.com"))

    # Core params
    parser.add_argument("--type", "--document_type", dest="doc_type",
                        default="other",
                        choices=SUPPORTED_DOC_TYPES,
                        help="Document type")
    parser.add_argument("--content", required=True,
                        help="Content source: bullet points, outline, or description")
    parser.add_argument("--format", "--target_format", dest="fmt",
                        default="markdown",
                        choices=SUPPORTED_OUTPUT_FORMATS,
                        help="Output format")

    # Layout preferences
    parser.add_argument("--style", default="formal",
                        choices=SUPPORTED_STYLES,
                        help="Layout style: formal (default) / simple")
    parser.add_argument("--toc", "--include_toc", dest="include_toc",
                        action="store_true", default=True,
                        help="Include table of contents")
    parser.add_argument("--no-toc", dest="include_toc",
                        action="store_false", default=True,
                        help="Exclude table of contents")
    parser.add_argument("--cover", "--include_cover", dest="include_cover",
                        action="store_true", default=True,
                        help="Include cover page")
    parser.add_argument("--no-cover", dest="include_cover",
                        action="store_false", default=True,
                        help="Exclude cover page")
    parser.add_argument("--brand_colors", default="",
                        help="Brand color codes (optional)")

    # Length control
    parser.add_argument("--max_length", type=int, default=RECOMMENDED_MAX_CHARS,
                        help=f"Max character target (default: {RECOMMENDED_MAX_CHARS})")

    args = parser.parse_args()

    if not args.key:
        print("ERROR: --key or API_KEY env required")
        print("Register at: https://your-platform-domain.com/register")
        sys.exit(1)

    # 1. Create chat session
    chat = create_chat(
        title=args.topic or "untitled",
        bot_id=0,
        agent_type="writer",
        extra_data={"document_type": args.doc_type, "content": args.content,
                    "target_format": args.fmt, "style": args.style}
    )
    chat_id = chat.get("id","")
    if not chat_id:
        print("ERROR: Failed to create chat session."); sys.exit(1)
    print(f"[SESSION] chatId: {chat_id}")

    if not verify_key(chat_id):
        print("ERROR: Session not verified."); sys.exit(1)

    for step in run_loop(chat_id, user_msg):
        ev_type = (step or {}).get("action", "done")
        if ev_type == "done":
            outs = (step or {}).get("data",{}).get("outputs",{})
            for k,v in outs.items():
                if v: print(f"  {k}: {v}")
            print(f"  Credits: {step.get('meta',{}).get('credits_consumed','N/A')}")
            break
        elif ev_type == "credit_warning":
            print(f"[WARN] Low credits: {(step or {}).get('data',{}).get('remaining_credits',0)}")
        elif ev_type == "error":
            print(f"[ERROR] {(step or {}).get('data',{}).get('code','UNKNOWN')}")
            break
            sys.exit(1)    sys.exit(1)

    # Check content length and warn if needed
    content_len = len(args.content)
    if content_len > RECOMMENDED_MAX_CHARS:
        print(f"[WARN] Content length ({content_len}) exceeds recommended max ({RECOMMENDED_MAX_CHARS}).")
        print(f"[WARN] Consider splitting into multiple documents.")
    if content_len > MAX_MANUSCRIPT_CHARS:
        print(f"[ERROR] Content length ({content_len}) exceeds ultra-long manuscript threshold ({MAX_MANUSCRIPT_CHARS}).")
        print("ERROR: Single-generation of book-length content is not supported.")
        sys.exit(1)

    # Build user message
    user_msg = f"Document type: {args.doc_type}."
    user_msg += f" Content: {args.content}."
    user_msg += f" Target format: {args.fmt}."
    user_msg += f" Style: {args.style}."
    user_msg += f" Include TOC: {args.include_toc}."
    user_msg += f" Include cover: {args.include_cover}."
    if args.brand_colors:
        user_msg += f" Brand colors: {args.brand_colors}."
    user_msg += f" Max length: {args.max_length} characters."

    run_loop(client, user_msg)


if __name__ == "__main__":
    main()
