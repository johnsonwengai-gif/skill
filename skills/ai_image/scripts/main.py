#!/usr/bin/env python3
"""
AI Image -- Main orchestration script.
Routes image generation and editing requests through the API loop until done/error.
Usage:
  # Text-to-image generation
  python3 main.py --prompt "futuristic city" --ratio 16:9 --res 2K [--key KEY]

  # Batch generation (up to 12 images)
  python3 main.py --prompt "futuristic city" --ratio 16:9 --res 2K --count 12 [--key KEY]

  # Upscale (up to 8K)
  python3 main.py --mode upscale --input_image <url> --target_res 8K [--key KEY]

  # Background removal
  python3 main.py --mode background_removal --input_image <url> [--key KEY]

  # Background replacement
  python3 main.py --mode background_replacement --input_image <url> --bg_prompt "sunset beach" [--key KEY]

  # Text/watermark removal
  python3 main.py --mode text_removal --input_image <url> [--key KEY]
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_client import create_chat, verify_key

# Capability limits
MAX_IMAGES_PER_REQUEST = 12
MAX_REFERENCE_IMAGES = 10
MAX_UPSCALE_RESOLUTION = "8K"
AUTO_RETRY_MAX = 3

SUPPORTED_RATIOS = ["1:1", "4:5", "16:9", "9:16", "3:2"]
SUPPORTED_RESOLUTIONS = ["1K", "2K", "4K", "8K"]
SUPPORTED_FORMATS = ["PNG", "JPG"]
SUPPORTED_MODES = [
    "text2img", "upscale", "expand",
    "background_removal", "background_replacement", "text_removal"
]


def validate_params(mode: str, params: dict) -> tuple:
    """Validate request against capability limits. Returns (valid, message)."""
    issues = []

    # Check reference images limit
    ref_images = params.get("reference_images", [])
    if isinstance(ref_images, list) and len(ref_images) > MAX_REFERENCE_IMAGES:
        issues.append(
            f"Reference images ({len(ref_images)}) exceed maximum ({MAX_REFERENCE_IMAGES}). "
            f"Please reduce to {MAX_REFERENCE_IMAGES} or fewer."
        )

    # Check upscale resolution limit
    if mode == "upscale":
        target_res = params.get("target_resolution", "1K")
        res_order = {"1K": 1, "2K": 2, "4K": 4, "8K": 8}
        if res_order.get(target_res, 0) > res_order.get(MAX_UPSCALE_RESOLUTION, 0):
            issues.append(
                f"Upscale resolution ({target_res}) exceeds maximum ({MAX_UPSCALE_RESOLUTION}). "
                f"Please select 8K or lower."
            )

    if issues:
        return False, " ".join(issues)
    return True, "OK"


def run_loop(client: APIClient, user_message: str):
    messages = [{"role": "user", "content": user_message}]
    step = 0
    retry_count = {}

    while True:
        step += 1
        context = {"step": step}
        resp = client.chat(messages, context=context)
        action = resp.get("action")
        msg = resp.get("message", "")

        print(f"[Step {step}] Action: {action} - {msg}")

        if action == "done":
            outputs = resp.get("data", {}).get("outputs", {})
            meta = resp.get("data", {})
            images = outputs.get("images", [])
            print(f"\n[DONE] Task completed successfully!")
            if outputs.get("image_url"):
                print(f"[OUTPUT] Image: {outputs['image_url']}")
            if images:
                print(f"[OUTPUT] Images ({len(images)}):")
                for img in images:
                    print(f"  [{img.get('index')}] {img.get('url')}")
            print(f"[CREDITS] Consumed: {resp.get('meta', {}).get('total_credits_consumed', 'N/A')}")
            break

        elif action == "call_agent":
            d = resp["data"]
            params = d.get("params", {})
            agent = d.get("agent", "image")
            mode = params.get("mode", "text2img")

            # Validate against capability limits
            valid, hint = validate_params(mode, params)
            if not valid:
                print(f"[WARN] Request exceeds capability limits: {hint}")
                messages.append({"role": "user", "content": f"The request exceeds capability limits: {hint}"})
                continue

            # Track retry count
            task_key = f"{agent}:{mode}"
            retry_count[task_key] = 0

            if agent == "image_editing":
                edit_mode = params.get("mode", "")
                print(f"[INFO] Calling image editing agent: mode={edit_mode}")
                if edit_mode == "background_replacement":
                    bg = params.get("background_prompt", "N/A")
                    print(f"[INFO] Background: {str(bg)[:80]}...")
                elif edit_mode == "text_removal":
                    areas = params.get("remove_areas", [])
                    print(f"[INFO] Remove areas: {len(areas)} region(s)")
                if params.get("input_image"):
                    print(f"[INFO] Input image provided")
                if params.get("target_resolution"):
                    print(f"[INFO] Target resolution: {params.get('target_resolution')}")
            elif params.get("mode") == "img2img":
                # img2img generation
                gen_mode = params.get("mode", "text2img")
                prompt = params.get("prompt", "N/A")
                ratio = params.get("aspect_ratio", "N/A")
                res = params.get("resolution", "N/A")
                fmt = params.get("output_format", "N/A")
                count = params.get("count", 1)
                ref_count = len(params.get("reference_images", []))
                has_input = bool(params.get("input_image"))
                print(f"[INFO] Calling image agent: mode={gen_mode}, input_image={has_input}, "
                      f"ratio={ratio}, res={res}, format={fmt}, count={count}")
                if ref_count > 0:
                    print(f"[INFO] Reference images: {ref_count}/{MAX_REFERENCE_IMAGES}")
                print(f"[INFO] Prompt: {str(prompt)[:80]}...")
            else:
                # text2img generation
                gen_mode = params.get("mode", "text2img")
                prompt = params.get("prompt", "N/A")
                ratio = params.get("aspect_ratio", "N/A")
                res = params.get("resolution", "N/A")
                fmt = params.get("output_format", "N/A")
                count = params.get("count", 1)
                ref_count = len(params.get("reference_images", []))
                print(f"[INFO] Calling image agent: mode={gen_mode}, ratio={ratio}, "
                      f"res={res}, format={fmt}, count={count}")
                if ref_count > 0:
                    print(f"[INFO] Reference images: {ref_count}/{MAX_REFERENCE_IMAGES}")
                print(f"[INFO] Prompt: {str(prompt)[:80]}...")

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

            # Auto-retry logic (up to 3 times)
            task_key = "last_task"
            if recoverable:
                retry_count[task_key] = retry_count.get(task_key, 0) + 1
                if retry_count[task_key] <= AUTO_RETRY_MAX:
                    print(f"[INFO] Auto-retry {retry_count[task_key]}/{AUTO_RETRY_MAX}")
                    user_input = "retry"
                    messages.append({"role": "user", "content": user_input})
                else:
                    print(f"[WARN] Max retries ({AUTO_RETRY_MAX}) reached.")
                    break
            else:
                break

        else:
            print(f"[WARN] Unknown action '{action}'.")
            print(json.dumps(resp, ensure_ascii=False, indent=2))
            break


def main():
    parser = argparse.ArgumentParser(
        description="AI Image -- Multi-Modal Image Generation and Editing Agent")
    parser.add_argument("--key", default=os.getenv("API_KEY", ""))
    parser.add_argument("--url", default=os.getenv("API_URL", "https://api.your-platform-domain.com"))

    # Generation mode
    parser.add_argument("--prompt", help="Image prompt (for generation modes)")
    parser.add_argument("--ratio", "--aspect_ratio", dest="ratio", default="16:9",
                        choices=SUPPORTED_RATIOS, help="Aspect ratio")
    parser.add_argument("--res", "--resolution", dest="res", default="2K",
                        choices=SUPPORTED_RESOLUTIONS, help="Resolution")
    parser.add_argument("--format", default="PNG", choices=SUPPORTED_FORMATS, help="Output format")
    parser.add_argument("--count", type=int, default=1,
                        help=f"Number of images to generate (max {MAX_IMAGES_PER_REQUEST})")

    # Mode selection
    parser.add_argument("--mode", default="text2img", choices=SUPPORTED_MODES,
                        help="Operation mode")

    # Editing mode inputs
    parser.add_argument("--input", "--input_image", dest="input_image",
                        default="", help="Input image URL or base64 (for editing modes)")
    parser.add_argument("--bg_prompt", "--background_prompt", dest="bg_prompt",
                        default="", help="Background description (for background_replacement)")
    parser.add_argument("--target_res", "--target_resolution", dest="target_res",
                        default="8K", choices=SUPPORTED_RESOLUTIONS,
                        help=f"Target resolution for upscale (max {MAX_UPSCALE_RESOLUTION})")
    parser.add_argument("--ref", "--reference_images", dest="ref", default="", nargs="*",
                        help=f"Reference image URLs (max {MAX_REFERENCE_IMAGES})")

    args = parser.parse_args()

    if not args.key:
        print("ERROR: --key or API_KEY env required")
        print("Register at: https://your-platform-domain.com/register")
        sys.exit(1)

    # 1. Create chat session (tRPC)
    chat = create_chat(
        title=args.topic or "untitled",
        bot_id=0,
        agent_type="image",
        extra_data={"model": "flash", "prompt": prompt, "aspect_ratio": aspect_ratio,
                    "resolution": resolution, "output_format": output_format}
    )
    chat_id = chat.get("id","")
    if not chat_id:
        print("ERROR: Failed to create chat session."); sys.exit(1)
    print(f"[SESSION] chatId: {chat_id}")

    # 2. Verify session
    if not verify_key(chat_id):
        print("ERROR: Session not verified."); sys.exit(1)

    # 3. Run SSE event loop
    for step in run_loop(chat_id, user_msg):
        ev_type = (step or {}).get("action", "done")
        if ev_type == "done":
            outputs = (step or {}).get("data", {}).get("outputs", {})
            print(f"
[DONE] Image(s) generated:")
            for img in outputs.get("images", []):
                print(f"  {img.get('url')}")
            print(f"  Credits used: {step.get('meta',{}).get('credits_consumed','N/A')}")
            break
        elif ev_type == "credit_warning":
            bal = (step or {}).get("data",{}).get("remaining_credits",0)
            print(f"[WARN] Low credits: {bal}")
        elif ev_type == "error":
            print(f"[ERROR] {step.get('data',{}).get('code','UNKNOWN')}")
            break
            sys.exit(1)    sys.exit(1)

    # Build user message based on mode
    if args.mode in ["upscale", "expand", "background_removal",
                     "background_replacement", "text_removal"]:
        user_msg = f"Edit an image using mode: {args.mode}."
        if args.input_image:
            user_msg += f" Input image: {args.input_image}."
        if args.mode == "upscale":
            user_msg += f" Target resolution: {args.target_res} (max {MAX_UPSCALE_RESOLUTION})."
        if args.mode == "background_replacement" and args.bg_prompt:
            user_msg += f" New background: {args.bg_prompt}."
        if args.mode == "text_removal":
            user_msg += " Remove text or watermarks from the image."
    elif args.mode == "img2img":
        user_msg = f"Transform or generate image using mode: img2img."
        if args.input_image:
            user_msg += f" Input image: {args.input_image}."
        if args.prompt:
            user_msg += f" Prompt: {args.prompt}."
        user_msg += f" Aspect ratio: {args.ratio}."
        user_msg += f" Resolution: {args.res}."
        user_msg += f" Format: {args.format}."
        if args.count > 1:
            if args.count > MAX_IMAGES_PER_REQUEST:
                args.count = MAX_IMAGES_PER_REQUEST
            user_msg += f" Generate {args.count} images."
        if args.ref:
            ref_list = args.ref if isinstance(args.ref, list) else [args.ref]
            if len(ref_list) > MAX_REFERENCE_IMAGES:
                ref_list = ref_list[:MAX_REFERENCE_IMAGES]
            user_msg += f" Reference images ({len(ref_list)}): {', '.join(ref_list)}."
    else:
        # text2img (default)
        user_msg = args.prompt or ""
        user_msg += f" Aspect ratio: {args.ratio}."
        user_msg += f" Resolution: {args.res}."
        user_msg += f" Format: {args.format}."
        user_msg += f" Mode: {args.mode}."
        if args.count > 1:
            if args.count > MAX_IMAGES_PER_REQUEST:
                args.count = MAX_IMAGES_PER_REQUEST
            user_msg += f" Generate {args.count} images."
        if args.ref:
            ref_list = args.ref if isinstance(args.ref, list) else [args.ref]
            if len(ref_list) > MAX_REFERENCE_IMAGES:
                ref_list = ref_list[:MAX_REFERENCE_IMAGES]
            user_msg += f" Reference images ({len(ref_list)}): {', '.join(ref_list)}."

    run_loop(client, user_msg)


if __name__ == "__main__":
    main()
