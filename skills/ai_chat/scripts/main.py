#!/usr/bin/env python3
"""
AI Chat — Multi-Modal General Orchestration Agent main script.
Routes complex multi-modal tasks through the General Agent SSE protocol,
coordinating sub-agents (image, video, slide, writer, research) with support
for sequential chains and parallel execution.

Usage:
  # General multi-modal request (auto-classified)
  python3 main.py --task "帮我做个PPT讲一下这份报告" --key KEY

  # Direct sub-agent task
  python3 main.py --agent slide --topic "Q1 report" --pages 10 --key KEY

  # Chain: research -> slide
  python3 main.py --chain research,slide --topic "China EV market" --key KEY

  # Parallel: image + writer simultaneously
  python3 main.py --parallel --image_prompt "cover photo" --doc_content "outline" --key KEY
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_client import (
    create_chat, delete_chat, send_message, cancel_task,
    get_session, get_messages, memory_list, memory_read,
    archive_download_url, verify_session, run_loop,
)

# Registered sub-agents
SUB_AGENTS = ["image", "video", "slide", "writer", "research"]


def classify_task(task: str) -> list:
    """Infer required sub-agents from natural language task description."""
    task_lower = task.lower()
    agents = set()

    if any(k in task_lower for k in ["图片", "图像", "生成图", "image", "生成一张"]):
        agents.add("image")
    if any(k in task_lower for k in ["视频", "录像", "video", "做视频"]):
        agents.add("video")
    if any(k in task_lower for k in ["ppt", "slides", "幻灯", "演示", "做ppt"]):
        agents.add("slide")
    if any(k in task_lower for k in ["写", "文档", "报告", "方案", "resume", "write", "doc"]):
        agents.add("writer")
    if any(k in task_lower for k in ["调研", "研究", "research", "行业研究"]):
        agents.add("research")

    # Cross-modal inference
    if "报告" in task or "report" in task_lower:
        if "ppt" in task_lower or "演示" in task_lower or "幻灯" in task_lower:
            agents = {"research", "slide"}
        elif "视频" in task_lower or "video" in task_lower:
            agents = {"research", "video"}

    return list(agents) if agents else ["writer"]


def build_user_message(args, inferred_agents: list) -> str:
    """Build a structured user message from CLI arguments."""
    parts = []
    if args.task:
        parts.append(args.task)
    if getattr(args, "topic", None):
        parts.append(f"Topic: {args.topic}")
    if getattr(args, "content", None):
        parts.append(f"Content: {args.content}")
    if inferred_agents:
        parts.append(f"Requested agents: {', '.join(inferred_agents)}")
    if getattr(args, "pages", None):
        parts.append(f"Pages: {args.pages}")
    if getattr(args, "audience", None):
        parts.append(f"Audience: {args.audience}")
    if getattr(args, "style", None):
        parts.append(f"Style: {args.style}")
    return " | ".join(parts)


def run(args):
    # ── Step 1: Create session ──────────────────────────────────────────────
    chat = create_chat(
        title=args.topic or args.task or "multi-modal task",
        bot_id=0,
        agent_type="GENERAL_AGENT",
        extra_data={},
    )
    chat_id = chat.get("id", "")
    if not chat_id:
        print("ERROR: Failed to create chat session.")
        sys.exit(1)
    print(f"[SESSION] chatId: {chat_id}  |  title: {chat.get('title','?')}")

    # ── Step 2: Build user message ─────────────────────────────────────────
    inferred = classify_task(args.task or "")
    user_msg = build_user_message(args, inferred)
    print(f"[INFO] Auto-classified -> sub-agents: {inferred}")
    print(f"[MSG] {user_msg[:120]}{'...' if len(user_msg) > 120 else ''}")

    # ── Step 3: Run SSE event loop ─────────────────────────────────────────
    last_event_id = None
    active_tool = None
    step_outputs = {}  # {tool_name: output}

    try:
        for ev in run_loop(chat_id, text=user_msg):
            t = ev["type"]
            d = ev["data"]

            if t == "RUN_STARTED":
                run_id = ev.get("run_id", "")
                print(f"\n[RUN] Started: run_id={run_id}")

            elif t == "TEXT_MESSAGE_CONTENT":
                # Incremental text — already printed by run_loop, just yield
                yield {"type": "text", "data": d}

            elif t == "TOOL_CALL_START":
                active_tool = (d or {}).get("tool", "unknown") if isinstance(d, dict) else str(d)
                tool_input  = (d or {}).get("input", {})       if isinstance(d, dict) else {}
                print(f"\n[TOOL] START: {active_tool}")
                print(f"  Input: {json.dumps(tool_input, ensure_ascii=False)[:200]}")
                yield {"type": "tool_start", "tool": active_tool, "input": tool_input}

            elif t == "TOOL_CALL_END":
                tool_name = (d or {}).get("tool", active_tool or "unknown") if isinstance(d, dict) else str(d)
                tool_out  = (d or {}).get("output", {})       if isinstance(d, dict) else d
                print(f"[TOOL] END: {tool_name}")
                print(f"  Output: {json.dumps(tool_out, ensure_ascii=False)[:200]}")
                step_outputs[tool_name] = tool_out
                yield {"type": "tool_end", "tool": tool_name, "output": tool_out}
                active_tool = None

            elif t == "RUN_FINISHED":
                summary = d or {}
                print(f"\n[RUN] Finished: {json.dumps(summary, ensure_ascii=False)[:300]}")
                yield {"type": "run_finished", "data": summary, "outputs": dict(step_outputs)}

            elif t == "DONE":
                print(f"\n[DONE] Stream ended.")
                break

            elif t == "ERROR":
                err_msg = (d or {}).get("message", str(d)) if isinstance(d, dict) else str(d)
                print(f"\n[ERROR] {err_msg}")
                yield {"type": "error", "data": d}
                break

            elif t == "PLAYBACK_HISTORY_REFRESH":
                print(f"[PLAYBACK] History refreshed: {json.dumps(d, ensure_ascii=False)[:200]}")
                yield {"type": "playback", "data": d}

            else:
                print(f"\n[EVENT] {t}: {str(d)[:200]}")
                yield ev

    except KeyboardInterrupt:
        print("\n[INTERRUPT] User cancelled. Attempting to cancel active run...")
        try:
            result = cancel_task(chat_id)
            print(f"[CANCEL] Result: {result}")
        except Exception as e:
            print(f"[WARN] Cancel failed: {e}")

    # ── Step 4: Retrieve output files ───────────────────────────────────────
    print("\n[MEMORY] Listing output files...")
    try:
        mem = memory_list(chat_id)
        files = mem.get("files", [])
        if files:
            print(f"  {len(files)} file(s):")
            for f in files:
                print(f"    {f['path']}  ({f['size']} bytes)")
                # Get download URL
                url_resp = memory_read(f["path"], chat_id=chat_id)
                url = url_resp.get("url", "")
                if url:
                    print(f"    -> {url[:100]}")
                yield {"type": "file", "path": f["path"], "size": f["size"], "url": url}
        else:
            print("  (no files)")
    except Exception as e:
        print(f"[WARN] memory_list failed: {e}")

    print("\n[CREDITS] Check dashboard: https://your-platform-domain.com/dashboard")


def main():
    parser = argparse.ArgumentParser(
        description="AI Chat — Multi-Modal General Orchestration Agent")
    parser.add_argument("--key", default=os.getenv("API_KEY", ""))
    parser.add_argument("--url", default=os.getenv("API_URL", "https://api.your-platform-domain.com"))

    # Core
    parser.add_argument("--task",
                        help="Natural language task description (auto-classified into sub-agents)")
    parser.add_argument("--chain",
                        help="Comma-separated sub-agent chain, e.g. research,slide")
    parser.add_argument("--parallel", action="store_true",
                        help="Run multiple sub-agents in parallel")

    # Sub-agent selection (override auto-classification)
    parser.add_argument("--agent", choices=SUB_AGENTS,
                        help="Direct sub-agent selection")

    # Shared params
    parser.add_argument("--topic",
                        help="Topic or research question")
    parser.add_argument("--content",
                        help="Content / outline / bullet points")

    # Image params
    parser.add_argument("--image_prompt",
                        help="Image generation prompt (for image sub-agent)")

    # Video params
    parser.add_argument("--video_prompt",
                        help="Video generation prompt")
    parser.add_argument("--duration", type=int, choices=[6, 10], default=6,
                        help="Video duration in seconds (default: 6)")

    # Slide params
    parser.add_argument("--pages", type=int, default=10,
                        help="Number of slides (default: 10, max: 30)")

    # Writer params
    parser.add_argument("--doc_type",
                        help="Document type: resume / proposal / prd / report / whitepaper / etc.")
    parser.add_argument("--format", dest="fmt",
                        choices=["markdown", "word", "pdf", "html"],
                        default="markdown",
                        help="Output format")

    # Research params
    parser.add_argument("--audience",
                        choices=["general", "consulting", "investor", "technical"],
                        default="general",
                        help="Target audience")
    parser.add_argument("--style",
                        choices=["popular_science", "consulting", "investment", "technical"],
                        default="consulting",
                        help="Research / writing style")

    args = parser.parse_args()

    if not args.key:
        print("ERROR: --key or API_KEY env required")
        print("Register at: https://your-platform-domain.com/register")
        sys.exit(1)

    if not args.task and not args.chain and not args.agent:
        print("ERROR: --task, --chain, or --agent is required")
        sys.exit(1)

    for ev in run(args):
        pass


if __name__ == "__main__":
    main()
