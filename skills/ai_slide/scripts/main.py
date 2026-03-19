#!/usr/bin/env python3
"""
AI Slide -- Main orchestration script.
Routes slide generation requests through the API loop until done/error.
Usage:
  # Generate slides from topic
  python3 main.py --topic "AI product pitch" --pages 10 --audience investor --scenario roadshow [--key KEY]

  # Generate with speaker notes and material list
  python3 main.py --topic "Q1 training" --pages 20 --audience employee --scenario training --speaker_notes --material_list [--key KEY]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_client import create_chat, verify_key

# Capability limits
MAX_PAGES_PER_GENERATION = 30
DEFAULT_PAGES = 10
MAX_AI_IMAGES_PER_DECK = 10

SUPPORTED_AUDIENCES = ["investor", "client", "employee", "academic", "general"]
SUPPORTED_SCENARIOS = ["roadshow", "pitch", "training", "review", "academic", "event"]
SUPPORTED_ILLUSTRATION_SOURCES = ["ai_generated", "web_images", "user_uploaded"]
SUPPORTED_OUTPUT_FORMATS = ["PPTX"]


def validate_params(params: dict) -> tuple:
    """Validate request against capability limits. Returns (valid, message)."""
    issues = []

    pages = params.get("pages", DEFAULT_PAGES)
    if pages > MAX_PAGES_PER_GENERATION:
        issues.append(
            f"Pages ({pages}) exceed maximum ({MAX_PAGES_PER_GENERATION}). "
            f"Capping to {MAX_PAGES_PER_GENERATION}."
        )
        params["pages"] = MAX_PAGES_PER_GENERATION

    image_count = params.get("image_count", 0)
    if image_count > MAX_AI_IMAGES_PER_DECK:
        issues.append(
            f"AI images ({image_count}) exceed maximum ({MAX_AI_IMAGES_PER_DECK}). "
            f"Capping to {MAX_AI_IMAGES_PER_DECK}."
        )
        params["image_count"] = MAX_AI_IMAGES_PER_DECK

    scenario = params.get("scenario", "")
    if scenario and scenario not in SUPPORTED_SCENARIOS:
        issues.append(
            f"Scenario '{scenario}' not supported. "
            f"Use one of: {', '.join(SUPPORTED_SCENARIOS)}."
        )

    audience = params.get("audience", "")
    if audience and audience not in SUPPORTED_AUDIENCES:
        issues.append(
            f"Audience '{audience}' not supported. "
            f"Use one of: {', '.join(SUPPORTED_AUDIENCES)}."
        )

    out_of_scope = [
        "Large data visualizations (multi-dimensional interactive charts)",
        "Complex custom animations or transition effects",
        "Strict brand VI compliance (exact fonts/colors/components)",
        "Image copyright and availability verification",
    ]

    return (False, " ".join(issues)) if issues else (True, "OK", out_of_scope)


def run_loop(client: APIClient, user_message: str):
    messages = [{"role": "user", "content": user_message}]
    step = 0

    while True:
        step += 1
        context = {"step": step}
        resp = client.chat(messages, context=context)
        action = resp.get("action")
        msg = resp.get("message", "")

        print(f"[Step {step}] Action: {action} - {msg}")

        if action == "done":
            outputs = resp.get("data", {}).get("outputs", {})
            print(f"\n[DONE] Presentation generated successfully!")
            if outputs.get("pptx_url"):
                print(f"[OUTPUT] PPTX: {outputs['pptx_url']}")
            if outputs.get("html_url"):
                print(f"[OUTPUT] HTML: {outputs['html_url']}")
            if outputs.get("speaker_notes_url"):
                print(f"[OUTPUT] Speaker Notes: {outputs['speaker_notes_url']}")
            if outputs.get("material_list_url"):
                print(f"[OUTPUT] Material List: {outputs['material_list_url']}")
            print(f"[INFO] Pages: {outputs.get('pages_generated', 'N/A')}")
            print(f"[INFO] AI Images: {outputs.get('images_generated', 'N/A')}")
            print(f"[INFO] Image Model: {outputs.get('image_model', 'nano_banana_pro')}")
            print(f"[CREDITS] Consumed: {resp.get('meta', {}).get('total_credits_consumed', 'N/A')}")
            break

        elif action == "call_agent":
            d = resp["data"]
            params = d.get("params", {})
            agent = d.get("agent", "slide")

            if agent == "image":
                page_idx = params.get("page_index", "?")
                model = params.get("model", "nano_banana_pro")
                print(f"[INFO] Calling image agent: page={page_idx}, model={model}")
            else:
                valid, hint, out_of_scope = validate_params(params)
                if not valid:
                    print(f"[WARN] {hint}")
                    messages.append({"role": "user", "content": f"Request adjusted: {hint}"})
                    continue

                topic = params.get("topic", "N/A")
                pages = params.get("pages", DEFAULT_PAGES)
                audience = params.get("audience", "N/A")
                scenario = params.get("scenario", "N/A")
                img_src = params.get("illustration_source", "ai_generated")
                img_count = params.get("image_count", 0)
                speaker = params.get("speaker_notes", False)
                material = params.get("material_list", False)
                model = params.get("image_model", "nano_banana_pro")
                print(f"[INFO] Calling slide agent:")
                print(f"  Topic: {str(topic)[:60]}...")
                print(f"  Pages: {pages}/{MAX_PAGES_PER_GENERATION}")
                print(f"  Audience: {audience} | Scenario: {scenario}")
                print(f"  Illustration: {img_src}, images: {img_count}/{MAX_AI_IMAGES_PER_DECK}")
                print(f"  Image Model: {model}")
                print(f"  Speaker Notes: {speaker} | Material List: {material}")

            sub_resp = client.call_agent(agent, params)
            messages.append({"role": "assistant", "content": json.dumps(sub_resp)})

        elif action == "request_parameter":
            fields = resp["data"].get("required_fields", [])
            print(f"[INFO] Required fields: {[f['name'] for f in fields]}")
            answers = {}
            for f in fields:
                val = input(f"  {f['label']}: ").strip()
                if val:
                    answers[f["name"]] = val
            messages.append({"role": "user", "content": f"Additional info: {json.dumps(answers)}"})

        elif action == "wait_user_confirm":
            preview = resp["data"].get("preview", "")
            confirm_prompt = resp["data"].get("confirm_prompt", "Continue? (yes/no)")
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
        description="AI Slide -- Multi-Modal Slide Generation Agent")
    parser.add_argument("--key", default=os.getenv("API_KEY", ""))
    parser.add_argument("--url", default=os.getenv("API_URL", "https://api.your-platform-domain.com"))

    # Core params
    parser.add_argument("--topic", help="Topic or outline description (required)")
    parser.add_argument("--pages", type=int, default=DEFAULT_PAGES,
                        help=f"Number of pages (default: {DEFAULT_PAGES}, max: {MAX_PAGES_PER_GENERATION})")
    parser.add_argument("--audience", default="general",
                        choices=SUPPORTED_AUDIENCES,
                        help="Target audience")
    parser.add_argument("--scenario", default="pitch",
                        choices=SUPPORTED_SCENARIOS,
                        help="Use case scenario")

    # Visual preferences
    parser.add_argument("--style", default="",
                        help="Visual style reference or description")
    parser.add_argument("--brand_colors", default="",
                        help="Brand color codes or descriptions (optional)")

    # Illustration
    parser.add_argument("--illustration_source", default="ai_generated",
                        choices=SUPPORTED_ILLUSTRATION_SOURCES,
                        help="Illustration source: ai_generated / web_images / user_uploaded")
    parser.add_argument("--image_count", type=int, default=0,
                        help=f"Number of AI images to generate (max: {MAX_AI_IMAGES_PER_DECK})")
    parser.add_argument("--image_model", default="nano_banana_pro",
                        help="Image generation model (default: nano_banana_pro)")

    # Output options
    parser.add_argument("--speaker_notes", action="store_true",
                        help="Include per-page speaker notes")
    parser.add_argument("--material_list", action="store_true",
                        help="Include image source and reference list")

    args = parser.parse_args()

    if not args.key:
        print("ERROR: --key or API_KEY env required")
        print("Register at: https://your-platform-domain.com/register")
        sys.exit(1)

    if not args.topic:
        print("ERROR: --topic is required")
        sys.exit(1)

    # 1. Create chat session
    chat = create_chat(
        title=args.topic or "untitled",
        bot_id=0,
        agent_type="slide",
        extra_data={"topic": args.topic, "pages": args.pages, "format": args.fmt,
                    "style": args.style, "scenario": args.scenario}
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

    # Cap pages at limit
    if args.pages > MAX_PAGES_PER_GENERATION:
        print(f"[WARN] Pages ({args.pages}) capped to {MAX_PAGES_PER_GENERATION}")
        args.pages = MAX_PAGES_PER_GENERATION

    # Cap AI images at limit
    if args.image_count > MAX_AI_IMAGES_PER_DECK:
        print(f"[WARN] AI images ({args.image_count}) capped to {MAX_AI_IMAGES_PER_DECK}")
        args.image_count = MAX_AI_IMAGES_PER_DECK

    # Build user message
    user_msg = f"Topic: {args.topic}."
    user_msg += f" Pages: {args.pages} (max {MAX_PAGES_PER_GENERATION})."
    user_msg += f" Audience: {args.audience}."
    user_msg += f" Scenario: {args.scenario}."
    user_msg += f" Illustration source: {args.illustration_source}."
    if args.image_count > 0:
        user_msg += f" AI images: {args.image_count} (max {MAX_AI_IMAGES_PER_DECK})."
    user_msg += f" Image model: {args.image_model}."
    if args.speaker_notes:
        user_msg += " Include speaker notes."
    if args.material_list:
        user_msg += " Include material list."
    if args.style:
        user_msg += f" Style: {args.style}."
    if args.brand_colors:
        user_msg += f" Brand colors: {args.brand_colors}."

    run_loop(client, user_msg)


if __name__ == "__main__":
    main()
