#!/usr/bin/env python3
"""Run trigger evaluation for a skill description.

Tests whether a skill's description causes Claude to trigger (read the skill)
for a set of queries. Outputs results as JSON.
"""

import argparse
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import urllib.error
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from concurrent.futures import ProcessPoolExecutor, as_completed

from scripts.utils import parse_skill_md


def check_environment():
    """Verify prerequisites before running eval and select active evaluation tier."""
    import shutil
    import os
    import sys
    
    # 1. Check Python Interpreter Stub
    from pathlib import Path
    executable_path = Path(sys.executable)
    stub_detected = False
    if "WindowsApps" in executable_path.parts:
        stub_detected = True
    else:
        for cmd in ["python", "python3"]:
            which_path = shutil.which(cmd)
            if which_path and "WindowsApps" in Path(which_path).parts:
                stub_detected = True
                break
    
    if stub_detected:
        print(
            "WARNING: Active Python interpreter or PATH command seems to be the Microsoft Store stub.\n"
            "[AGENT GUIDANCE — PYTHON STUB DETECTED]\n"
            "This can cause execution failures or open the App Store. Troubleshooting:\n"
            "1. Install Python from python.org or via winget: `winget install Python.Python.3.11`\n"
            "2. Disable App Execution Aliases: Search Windows for 'Manage app execution aliases' and toggle off 'Python' and 'Python3'.",
            file=sys.stderr
        )
        
    # 2. Check and announce active evaluation tier
    if shutil.which("claude"):
        return None
    elif os.environ.get("OPENAI_API_KEY"):
        base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE") or "https://api.openai.com/v1"
        model_name = os.environ.get("OPENAI_MODEL_NAME") or "gpt-4o"
        print(
            "[AGENT GUIDANCE — FALLBACK STRATEGY]\n"
            f"Claude CLI not found/failed. Using OpenAI-Compatible API fallback (Tier 2).\n"
            f"Endpoint: {base_url}\n"
            f"Model: {model_name}",
            file=sys.stderr
        )
        return None
    else:
        print(
            "[AGENT GUIDANCE — FALLBACK STRATEGY]\n"
            "Claude CLI not found and OPENAI_API_KEY is not set. Using local Heuristic Matcher (Tier 3).\n"
            "For more accurate evaluations, please either:\n"
            "  a) Install the Claude CLI (`npm install -g @anthropic-ai/claude-cli`)\n"
            "  b) Set OPENAI_API_KEY, and optionally OPENAI_BASE_URL/OPENAI_MODEL_NAME.",
            file=sys.stderr
        )
        return None


def find_project_root() -> Path:
    """Find the project root by walking up from cwd looking for .claude/.

    Mimics how Claude Code discovers its project root, so the command file
    we create ends up where claude -p will look for it.
    """
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".claude").is_dir():
            return parent
    return current


def run_tier1_claude_cli(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
) -> bool:
    """Evaluate triggering using Claude CLI (Tier 1)."""
    unique_id = uuid.uuid4().hex[:8]
    clean_name = f"{skill_name}-skill-{unique_id}"
    project_commands_dir = Path(project_root) / ".claude" / "commands"
    command_file = project_commands_dir / f"{clean_name}.md"

    try:
        project_commands_dir.mkdir(parents=True, exist_ok=True)
        # Use YAML block scalar to avoid breaking on quotes in description
        indented_desc = "\n  ".join(skill_description.split("\n"))
        command_content = (
            f"---\n"
            f"description: |\n"
            f"  {indented_desc}\n"
            f"---\n\n"
            f"# {skill_name}\n\n"
            f"This skill handles: {skill_description}\n"
        )
        command_file.write_text(command_content, encoding="utf-8")

        cmd = [
            "claude",
            "-p", query,
            "--output-format", "stream-json",
            "--verbose",
            "--include-partial-messages",
        ]
        if model:
            cmd.extend(["--model", model])

        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=project_root,
            env=env,
        )

        triggered = False
        start_time = time.time()
        buffer = ""
        pending_tool_name = None
        accumulated_json = ""

        # Cross-platform I/O: use a daemon thread + queue instead of select()
        line_queue: queue.Queue[str | None] = queue.Queue()

        def _reader_thread(stdout, q):
            try:
                for raw_line in iter(stdout.readline, b""):
                    q.put(raw_line.decode("utf-8", errors="replace"))
            finally:
                q.put(None)  # sentinel

        reader = threading.Thread(
            target=_reader_thread, args=(process.stdout, line_queue), daemon=True
        )
        reader.start()

        try:
            while time.time() - start_time < timeout:
                try:
                    raw_line = line_queue.get(timeout=1.0)
                except queue.Empty:
                    if process.poll() is not None:
                        break
                    continue

                if raw_line is None:
                    break
                buffer += raw_line

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Early detection via stream events
                    if event.get("type") == "stream_event":
                        se = event.get("event", {})
                        se_type = se.get("type", "")

                        if se_type == "content_block_start":
                            cb = se.get("content_block", {})
                            if cb.get("type") == "tool_use":
                                tool_name = cb.get("name", "")
                                if tool_name in ("Skill", "Read"):
                                    pending_tool_name = tool_name
                                    accumulated_json = ""
                                else:
                                    return False

                        elif se_type == "content_block_delta" and pending_tool_name:
                            delta = se.get("delta", {})
                            if delta.get("type") == "input_json_delta":
                                accumulated_json += delta.get("partial_json", "")
                                if clean_name in accumulated_json:
                                    return True

                        elif se_type in ("content_block_stop", "message_stop"):
                            if pending_tool_name:
                                return clean_name in accumulated_json
                            if se_type == "message_stop":
                                return False

                    # Fallback: full assistant message
                    elif event.get("type") == "assistant":
                        message = event.get("message", {})
                        for content_item in message.get("content", []):
                            if content_item.get("type") != "tool_use":
                                continue
                            tool_name = content_item.get("name", "")
                            tool_input = content_item.get("input", {})
                            if tool_name == "Skill" and clean_name in tool_input.get("skill", ""):
                                triggered = True
                            elif tool_name == "Read" and clean_name in tool_input.get("file_path", ""):
                                triggered = True
                            return triggered

                    elif event.get("type") == "result":
                        return triggered
        finally:
            # Clean up process on any exit path (return, exception, timeout)
            if process.poll() is None:
                process.kill()
                process.wait()

        return triggered
    finally:
        if command_file.exists():
            command_file.unlink()


def run_tier2_openai_api(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
) -> bool:
    """Evaluate triggering using an OpenAI-Compatible Chat Completions API (Tier 2)."""
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE") or "https://api.openai.com/v1"
    model_name = os.environ.get("OPENAI_MODEL_NAME") or "gpt-4o"

    system_prompt = (
        "You are a system classifier deciding if a custom command/skill should be executed "
        "to handle a user query. Respond with exactly 'YES' or 'NO' (no other text, explanation, or punctuation)."
    )
    user_prompt = (
        f"Skill Name: {skill_name}\n"
        f"Skill Description:\n{skill_description}\n\n"
        f"User Query:\n{query}\n\n"
        f"Should this skill be triggered to handle the user's query?"
    )

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.0,
        "max_tokens": 5
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=timeout) as response:
        resp_data = json.loads(response.read().decode("utf-8"))
        ans = resp_data["choices"][0]["message"]["content"].strip().upper()
        return "YES" in ans


def run_tier3_heuristics(query: str, skill_name: str, skill_description: str) -> bool:
    """Local keyword containment heuristic check to see if the skill triggers (Tier 3)."""
    stop_words = {
        "a", "an", "the", "and", "or", "but", "if", "then", "else", "when", 
        "at", "by", "for", "from", "in", "into", "of", "off", "on", "onto", 
        "out", "over", "to", "up", "with", "is", "was", "were", "be", "been",
        "has", "have", "had", "do", "does", "did", "can", "could", "should",
        "would", "will", "i", "you", "he", "she", "it", "we", "they", "me",
        "him", "her", "us", "them", "my", "your", "his", "their", "our"
    }

    def tokenize(text: str) -> set[str]:
        words = re.findall(r'[a-zA-Z0-9-]+', text.lower())
        return {w for w in words if len(w) > 2 and w not in stop_words}

    query_tokens = tokenize(query)
    skill_tokens = tokenize(skill_name) | tokenize(skill_description)

    name_tokens = tokenize(skill_name)
    if query_tokens & name_tokens:
        return True

    overlap = query_tokens & skill_tokens
    return len(overlap) >= 2


def run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
) -> bool:
    """Run a single query and check if the skill was triggered using Tier 1, 2, or 3."""
    # Tier 1: Claude CLI
    if shutil.which("claude"):
        try:
            return run_tier1_claude_cli(query, skill_name, skill_description, timeout, project_root, model)
        except Exception:
            pass

    # Tier 2: OpenAI-Compatible API
    if os.environ.get("OPENAI_API_KEY"):
        try:
            return run_tier2_openai_api(query, skill_name, skill_description, timeout)
        except Exception:
            pass

    # Tier 3: Heuristic Matcher
    return run_tier3_heuristics(query, skill_name, skill_description)



def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    num_workers: int,
    timeout: int,
    project_root: Path,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    model: str | None = None,
) -> dict:
    """Run the full eval set and return results."""
    results = []

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_info = {}
        for item in eval_set:
            for run_idx in range(runs_per_query):
                future = executor.submit(
                    run_single_query,
                    item["query"],
                    skill_name,
                    description,
                    timeout,
                    str(project_root),
                    model,
                )
                future_to_info[future] = (item, run_idx)

        query_triggers: dict[str, list[bool]] = {}
        query_items: dict[str, dict] = {}
        for future in as_completed(future_to_info):
            item, _ = future_to_info[future]
            query = item["query"]
            query_items[query] = item
            if query not in query_triggers:
                query_triggers[query] = []
            try:
                query_triggers[query].append(future.result())
            except Exception as e:
                print(f"Warning: query failed: {e}", file=sys.stderr)
                query_triggers[query].append(False)

    for query, triggers in query_triggers.items():
        item = query_items[query]
        trigger_rate = sum(triggers) / len(triggers)
        should_trigger = item["should_trigger"]
        if should_trigger:
            did_pass = trigger_rate >= trigger_threshold
        else:
            did_pass = trigger_rate < trigger_threshold
        results.append({
            "query": query,
            "should_trigger": should_trigger,
            "trigger_rate": trigger_rate,
            "triggers": sum(triggers),
            "runs": len(triggers),
            "pass": did_pass,
        })

    passed = sum(1 for r in results if r["pass"])
    total = len(results)

    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
        },
    }


def main():
    # Pre-check: ensure claude CLI is available
    env_error = check_environment()
    if env_error:
        print(env_error["guidance"], file=sys.stderr)
        print(json.dumps(env_error))
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Run trigger evaluation for a skill description")
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--description", default=None, help="Override description to test")
    parser.add_argument("--num-workers", type=int, default=10, help="Number of parallel workers")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout per query in seconds")
    parser.add_argument("--runs-per-query", type=int, default=3, help="Number of runs per query")
    parser.add_argument("--trigger-threshold", type=float, default=0.5, help="Trigger rate threshold")
    parser.add_argument("--model", default=None, help="Model to use for claude -p (default: user's configured model)")
    parser.add_argument("--verbose", action="store_true", help="Print progress to stderr")
    args = parser.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text(encoding="utf-8"))
    skill_path = Path(args.skill_path)

    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    name, original_description, content = parse_skill_md(skill_path)
    description = args.description or original_description
    project_root = find_project_root()

    if args.verbose:
        print(f"Evaluating: {description}", file=sys.stderr)

    output = run_eval(
        eval_set=eval_set,
        skill_name=name,
        description=description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        project_root=project_root,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        model=args.model,
    )

    if args.verbose:
        summary = output["summary"]
        print(f"Results: {summary['passed']}/{summary['total']} passed", file=sys.stderr)
        for r in output["results"]:
            status = "PASS" if r["pass"] else "FAIL"
            rate_str = f"{r['triggers']}/{r['runs']}"
            print(f"  [{status}] rate={rate_str} expected={r['should_trigger']}: {r['query'][:70]}", file=sys.stderr)

    # Add agent guidance to output
    guidance = (
        "[AGENT GUIDANCE]\n"
        "1. Review the pass/fail results above.\n"
        "2. If failures exist, run improve_description.py to generate an improved description.\n"
        "3. Use run_loop.py for automated iterative optimization."
    )
    output["guidance"] = guidance
    print(guidance, file=sys.stderr)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
