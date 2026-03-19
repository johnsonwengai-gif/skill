#!/usr/bin/env python3
"""
AI Video -- Main orchestration script.
Routes video generation requests through the API loop until done/error.
Usage: python3 main.py --message "Create a 10-second video of a city at sunset" [--key KEY]
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_client import create_chat, verify_key

CAPABILITY_LIMITS = {
    "short_clip_max_duration": 15,
    "short_film_max_duration": 120,
    "max_keyframes": 2,
    "max_reference_images": 3,
}

SUPPORTED_MODES = [
    "text2video",
    "image2video",
    "first_frame",
    "last_frame",
    "first_last_frame",
    "reference_images",
]


def validate_request(params: dict) -> tuple:
    """Validate request against capability limits. Returns (valid, message)."""
    duration = params.get("duration", 0)
    mode = params.get("mode", "text2video")

    if duration > CAPABILITY_LIMITS["short_film_max_duration"]:
        return False, (
            f"Duration ({duration}s) exceeds maximum supported length "
            f"({CAPABILITY_LIMITS['short_film_max_duration']}s). "
            f"Please reduce duration or split into multiple clips."
        )

    keyframes = len(params.get("keyframes", []))
    if keyframes > CAPABILITY_LIMITS["max_keyframes"]:
        return False, (
            f"Keyframes ({keyframes}) exceed maximum "
            f"({CAPABILITY_LIMITS['max_keyframes']})."
        )

    ref_images = len(params.get("reference_images", []))
    if ref_images > CAPABILITY_LIMITS["max_reference_images"]:
        return False, (
            f"Reference images ({ref_images}) exceed maximum "
            f"({CAPABILITY_LIMITS['max_reference_images']})."
        )

    return True, "OK"


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
            print(f"\n[DONE] Video generated successfully!")
            if outputs.get("video_file"):
                print(f"[OUTPUT] Video: {outputs['video_file']}")
            if outputs.get("cover_image"):
                print(f"[OUTPUT] Cover: {outputs['cover_image']}")
            if outputs.get("keyframes"):
                print(f"[OUTPUT] Keyframes: {outputs['keyframes']}")
            print(f"[CREDITS] Consumed: {resp.get('meta', {}).get('total_credits_consumed', 'N/A')}")
            break

        elif action == "call_agent":
            d = resp["data"]
            params = d.get("params", {})

            valid, hint = validate_request(params)
            if not valid:
                print(f"[WARN] Request exceeds capability limits: {hint}")
                messages.append({"role": "user", "content": f"The request exceeds capability limits: {hint}"})
                continue

            dur = params.get("duration", "N/A")
            res = params.get("resolution", "N/A")
            mode = params.get("mode", "text2video")
            print(f"[INFO] Calling video agent: mode={mode}, duration={dur}s, resolution={res}")
            sub_resp = client.call_agent(d["agent"], params)
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
            print(f"[PREVIEW] {preview[:200]}")
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

            if code == "DURATION_EXCEEDED":
                print(f"[HINT] Maximum supported duration is {CAPABILITY_LIMITS['short_film_max_duration']} seconds.")

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
        description="AI Video -- Multi-Modal Video Generation Agent")
    parser.add_argument("--key", default=os.getenv("API_KEY", ""))
    parser.add_argument("--url", default=os.getenv("API_URL", "https://api.your-platform-domain.com"))
    parser.add_argument("--message", required=True, help="Video generation request")
    parser.add_argument("--duration", type=int, default=10, help="Video duration in seconds (max 120)")
    parser.add_argument("--ratio", "--aspect_ratio", dest="ratio", default="16:9",
                        choices=["16:9", "9:16"])
    parser.add_argument("--res", "--resolution", dest="res", default="1080p",
                        choices=["720p", "1080p"])
    parser.add_argument("--mode", default="text2video",
                        choices=["text2video", "image2video", "first_frame", "last_frame", "first_last_frame"],
                        help="Video generation mode")
    parser.add_argument("--first_frame", default="", help="First frame image URL or base64")
    parser.add_argument("--last_frame", default="", help="Last frame image URL or base64")
    args = parser.parse_args()

    if not args.key:
        print("ERROR: --key or API_KEY env required")
        print("Register at: https://your-platform-domain.com/register")
        sys.exit(1)

    # 1. Create chat session
    chat = create_chat(
        title=args.topic or "untitled",
        bot_id=0,
        agent_type="video",
        extra_data={"prompt": args.prompt, "duration": args.duration,
                    "resolution": args.resolution, "aspect_ratio": args.aspect_ratio}
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

    user_msg = args.message
    user_msg += f" Duration: {args.duration}s."
    user_msg += f" Aspect ratio: {args.ratio}."
    user_msg += f" Resolution: {args.res}."
    user_msg += f" Mode: {args.mode}."
    if args.first_frame:
        user_msg += f" First frame: {args.first_frame}."
    if args.last_frame:
        user_msg += f" Last frame: {args.last_frame}."

    run_loop(client, user_msg)


if __name__ == "__main__":
    main()
