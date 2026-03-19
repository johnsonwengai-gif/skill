#!/usr/bin/env python3
"""
Deep Research — Main orchestration script.
Routes deep research tasks through the API loop until done/error/revision.
Usage:
  # Basic research
  python3 main.py --topic "China EV market trends 2025" --audience consulting --style consulting --key KEY

  # Research with provided sources
  python3 main.py --topic "AI policy regulation analysis" --scope "China, 2023-2025" --audience investor --style investment --sources "https://example.com/policy1.pdf" --key KEY

  # Research with custom length
  python3 main.py --topic "Semiconductor supply chain" --audience technical --style technical --min_length 3000 --max_length 12000 --key KEY
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_client import create_chat, verify_key

# Capability limits
MIN_REPORT_CHARS = 2000
MAX_REPORT_CHARS = 15000
MAX_SOURCES = 30
MAX_CHARS_PER_SOURCE = 204800  # 200 KB

SUPPORTED_AUDIENCES = ["general", "consulting", "investor", "technical"]
SUPPORTED_STYLES = ["popular_science", "consulting", "investment", "technical"]

OUT_OF_SCOPE = [
    "Paywalled or inaccessible content — completeness not guaranteed",
    "Real-time fact verification — research is not a final factual authority",
    "Long copyright text output — content is paraphrased or summarized only",
]


def validate_params(params: dict) -> tuple:
    """Validate request against capability limits. Returns (valid, message, oos_flags)."""
    issues = []
    oos_flags = []

    sources = params.get("provided_sources", []) or []
    if len(sources) > MAX_SOURCES:
        oos_flags.append(f"Sources ({len(sources)}) exceed maximum ({MAX_SOURCES}).")
        issues.append(f"Source count capped to {MAX_SOURCES}.")
        params["provided_sources"] = sources[:MAX_SOURCES]

    max_len = params.get("max_length", MAX_REPORT_CHARS)
    min_len = params.get("min_length", MIN_REPORT_CHARS)
    if max_len > MAX_REPORT_CHARS:
        oos_flags.append(f"Max length ({max_len}) exceeds limit ({MAX_REPORT_CHARS}).")
        params["max_length"] = MAX_REPORT_CHARS
    if min_len < MIN_REPORT_CHARS:
        oos_flags.append(f"Min length ({min_len}) below minimum ({MIN_REPORT_CHARS}).")
        params["min_length"] = MIN_REPORT_CHARS

    audience = params.get("audience", "")
    if audience and audience not in SUPPORTED_AUDIENCES:
        issues.append(f"Audience '{audience}' not supported. Use: {', '.join(SUPPORTED_AUDIENCES)}.")

    style = params.get("style", "")
    if style and style not in SUPPORTED_STYLES:
        issues.append(f"Style '{style}' not supported. Use: {', '.join(SUPPORTED_STYLES)}.")

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
            print(f"\n[DONE] Research report completed!")
            if outputs.get("markdown_url"):
                print(f"[OUTPUT] Markdown: {outputs['markdown_url']}")
            if outputs.get("summary"):
                print(f"[SUMMARY] {str(outputs['summary'])[:200]}")
            print(f"[INFO] Sources used: {outputs.get('source_count', 'N/A')} (max {MAX_SOURCES})")
            print(f"[INFO] Citations: {outputs.get('citation_count', 'N/A')}")
            print(f"[INFO] Characters: {outputs.get('character_count', 'N/A')}")
            print(f"[INFO] Style: {resp.get('data', {}).get('style', 'N/A')} | Audience: {resp.get('data', {}).get('audience', 'N/A')}")
            print(f"[CREDITS] Consumed: {resp.get('meta', {}).get('total_credits_consumed', 'N/A')}")
            break

        elif action == "call_agent":
            d = resp["data"]
            params = d.get("params", {})
            agent = d.get("agent", "research")

            if agent == "retrieve":
                topic = params.get("topic", "N/A")
                scope = params.get("scope", "N/A")
                src_count = len(params.get("provided_sources", []))
                print(f"[INFO] Calling retrieve agent:")
                print(f"  Topic: {str(topic)[:60]}...")
                print(f"  Scope: {scope}")
                print(f"  Provided sources: {src_count} | Max total: {MAX_SOURCES}")

            elif agent == "research":
                topic = params.get("topic", "N/A")
                audience = params.get("audience", "N/A")
                style = params.get("style", "N/A")
                min_len = params.get("min_length", MIN_REPORT_CHARS)
                max_len = params.get("max_length", MAX_REPORT_CHARS)
                print(f"[INFO] Calling research synthesis agent:")
                print(f"  Topic: {str(topic)[:60]}...")
                print(f"  Audience: {audience} | Style: {style}")
                print(f"  Target length: {min_len}–{max_len} chars")

            elif agent == "write":
                topic = params.get("topic", "N/A")
                audience = params.get("audience", "N/A")
                style = params.get("style", "N/A")
                cites = params.get("include_citations", True)
                print(f"[INFO] Calling write agent:")
                print(f"  Topic: {str(topic)[:60]}...")
                print(f"  Style: {style} | Citations: {cites}")

            else:
                print(f"[INFO] Calling agent: {agent}")
                print(f"[INFO] Params: {str(params)[:120]}")

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
            confirm_prompt = resp["data"].get("confirm_prompt", "Approve this report? (yes/no/revise)")
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
        description="Deep Research — Intelligent Research Report Agent")
    parser.add_argument("--key", default=os.getenv("API_KEY", ""))
    parser.add_argument("--url", default=os.getenv("API_URL", "https://api.your-platform-domain.com"))

    # Core params
    parser.add_argument("--topic", required=True,
                        help="Research topic or question (required)")
    parser.add_argument("--scope",
                        help="Scope constraints: region, time period, industry, caliber (optional)")

    # Audience & style
    parser.add_argument("--audience", required=True,
                        choices=SUPPORTED_AUDIENCES,
                        help="Target audience: general / consulting / investor / technical")
    parser.add_argument("--style", required=True,
                        choices=SUPPORTED_STYLES,
                        help="Writing style: popular_science / consulting / investment / technical")

    # Sources
    parser.add_argument("--sources", nargs="*",
                        help="Public source URLs or file paths (optional). Max 30 total.")

    # Length control
    parser.add_argument("--min_length", type=int, default=MIN_REPORT_CHARS,
                        help=f"Minimum character target (default: {MIN_REPORT_CHARS})")
    parser.add_argument("--max_length", type=int, default=MAX_REPORT_CHARS,
                        help=f"Maximum character target (default: {MAX_REPORT_CHARS})")

    args = parser.parse_args()

    if not args.key:
        print("ERROR: --key or API_KEY env required")
        print("Register at: https://your-platform-domain.com/register")
        sys.exit(1)

    # 1. Create chat session
    chat = create_chat(
        title=args.topic or "untitled",
        bot_id=0,
        agent_type="research",
        extra_data={"topic": args.topic, "audience": args.audience,
                    "style": args.style, "max_length": args.max_length}
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
            print(f"  Sources: {outs.get('source_count','N/A')}")
            print(f"  Credits: {step.get('meta',{}).get('credits_consumed','N/A')}")
            break
        elif ev_type == "credit_warning":
            print(f"[WARN] Low credits: {(step or {}).get('data',{}).get('remaining_credits',0)}")
        elif ev_type == "error":
            print(f"[ERROR] {(step or {}).get('data',{}).get('code','UNKNOWN')}")
            break
            sys.exit(1)    sys.exit(1)

    # Validate length range
    if args.min_length < MIN_REPORT_CHARS:
        print(f"[WARN] min_length ({args.min_length}) below minimum ({MIN_REPORT_CHARS}). Adjusting.")
        args.min_length = MIN_REPORT_CHARS
    if args.max_length > MAX_REPORT_CHARS:
        print(f"[WARN] max_length ({args.max_length}) exceeds limit ({MAX_REPORT_CHARS}). Adjusting.")
        args.max_length = MAX_REPORT_CHARS
    if args.min_length > args.max_length:
        print(f"[ERROR] min_length ({args.min_length}) > max_length ({args.max_length}).")
        sys.exit(1)

    # Validate source count
    provided = args.sources or []
    if len(provided) > MAX_SOURCES:
        print(f"[WARN] Sources ({len(provided)}) exceed maximum ({MAX_SOURCES}). Truncating.")
        provided = provided[:MAX_SOURCES]

    # Build user message
    user_msg = f"Research topic: {args.topic}."
    if args.scope:
        user_msg += f" Scope: {args.scope}."
    user_msg += f" Audience: {args.audience}."
    user_msg += f" Style: {args.style}."
    user_msg += f" Report length: {args.min_length}–{args.max_length} characters."
    if provided:
        user_msg += f" Provided sources ({len(provided)}): {'; '.join(provided[:5])}{'...' if len(provided) > 5 else ''}."
    else:
        user_msg += " No sources provided; retrieve from public web."

    run_loop(client, user_msg)


if __name__ == "__main__":
    main()
