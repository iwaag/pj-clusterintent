#!/usr/bin/env python3
"""executor — thin harness that runs one plan artifact through a local LLM.

Phase 2 of devdocs/vision/workflow_agent/roadmap.md. Consumes the frozen
plan contract (devdocs/vision/workflow_agent/plan_contract.md): reads one
plan.md, static-lints it, then drives an ollama chat session with the fixed
rule prompt (rule_prompt.md, system) plus the plan body (user) and a single
declared tool `run_command`. Each tool call is executed via subprocess from
the repo root; the raw transcript and the model's final message are written
next to the plan as transcript.json and report.md.

Usage:
    python3 executor/executor.py <plan-file-or-plan-id> [--lint-only]

A plan ID resolves to .local/evidence/workflow-plans/<plan-id>/plan.md.
Output always goes to the directory containing the plan file.

Environment overrides (defaults suit the local setup):
    EXECUTOR_OLLAMA_URL   default http://localhost:11434
    EXECUTOR_MODEL        default qwen3.6:35b-a3b-coding-nvfp4
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RULE_PROMPT_PATH = Path(__file__).resolve().parent / "rule_prompt.md"
PLANS_ROOT = REPO_ROOT / ".local" / "evidence" / "workflow-plans"

OLLAMA_URL = os.environ.get("EXECUTOR_OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("EXECUTOR_MODEL", "qwen3.6:35b-a3b-coding-nvfp4")

MAX_TURNS = 30
WALL_CLOCK_CAP_S = 30 * 60
COMMAND_TIMEOUT_S = 180
CHAT_TIMEOUT_S = 10 * 60

REQUIRED_SECTIONS = ["goal", "steps", "stop conditions", "success evidence"]
APPROVAL_MARKER = "**approval required**"
GATED_FLAGS = ("--yes", "--allow-destroy")

RUN_COMMAND_TOOL = {
    "type": "function",
    "function": {
        "name": "run_command",
        "description": (
            "Run one shell command from the repository root and return its "
            "stdout, stderr and exit code. A non-zero exit code is data, "
            "not a crash."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The exact shell command to run.",
                }
            },
            "required": ["command"],
        },
    },
}


# ---------------------------------------------------------------- lint

def lint_plan(text):
    """Static lint per contract §1 (four sections, in order) and §2
    (gated flags require the literal approval marker in the same step).
    Returns a list of error strings; empty list means the plan passes."""
    errors = []

    sections = re.findall(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
    normalized = [s.strip().lower() for s in sections]
    if normalized != REQUIRED_SECTIONS:
        errors.append(
            "contract §1: expected exactly the four sections "
            f"{REQUIRED_SECTIONS} in order, found {normalized}"
        )

    steps_match = re.search(
        r"^##\s+steps\s*$(.*?)(?=^##\s|\Z)", text, flags=re.MULTILINE | re.DOTALL
    )
    steps_text = steps_match.group(1) if steps_match else ""

    # Split the steps section into per-step blocks on numbered headings.
    blocks = re.split(r"^(?=\s{0,3}\d+\.\s)", steps_text, flags=re.MULTILINE)
    for block in blocks:
        if not block.strip():
            continue
        has_flag = any(flag in block for flag in GATED_FLAGS)
        has_marker = any(
            line.strip() == APPROVAL_MARKER for line in block.splitlines()
        )
        if has_flag and not has_marker:
            head = block.strip().splitlines()[0][:80]
            errors.append(
                "contract §2: step contains --yes/--allow-destroy without a "
                f"literal '{APPROVAL_MARKER}' line: {head!r}"
            )

    # Gated flags outside the steps section entirely are just as unmarked.
    outside = text.replace(steps_text, "")
    for flag in GATED_FLAGS:
        # Ignore mentions inside this linter's own error vocabulary is not
        # needed: plans do not contain lint output. Plain grep.
        if flag in outside:
            errors.append(
                f"contract §2: {flag} appears outside the steps section; "
                "gated flags may only appear inside a marked step"
            )

    return errors


def plan_has_marker(text):
    return any(line.strip() == APPROVAL_MARKER for line in text.splitlines())


# ---------------------------------------------------------------- ollama

def chat(messages):
    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": [RUN_COMMAND_TOOL],
        "stream": False,
        "options": {"temperature": 0.1, "num_ctx": 32768},
    }
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=CHAT_TIMEOUT_S) as resp:
        return json.loads(resp.read())


# ---------------------------------------------------------------- commands

def run_command(command):
    """Execute one tool-call command. Returns a dict fed back to the model
    verbatim and recorded in the transcript."""
    started = time.time()
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_S,
        )
        return {
            "command": command,
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "duration_s": round(time.time() - started, 2),
        }
    except subprocess.TimeoutExpired:
        return {
            "command": command,
            "exit_code": None,
            "stdout": "",
            "stderr": f"harness: command timed out after {COMMAND_TIMEOUT_S}s",
            "duration_s": round(time.time() - started, 2),
        }


# ---------------------------------------------------------------- main loop

def write_transcript(plan_dir, meta, messages):
    (plan_dir / "transcript.json").write_text(
        json.dumps({"meta": meta, "messages": messages}, indent=2, ensure_ascii=False)
        + "\n"
    )


def write_report(plan_dir, meta, final_text):
    header = "\n".join(
        [
            "<!-- harness header: ground truth as the harness saw it -->",
            f"- plan_id: {meta['plan_id']}",
            f"- model: {meta['model']}",
            f"- started: {meta['started']}",
            f"- ended: {meta['ended']}",
            f"- turns: {meta['turns']}",
            f"- commands_executed: {meta['commands_executed']}",
            f"- harness_outcome: {meta['harness_outcome']}",
        ]
    )
    (plan_dir / "report.md").write_text(header + "\n\n---\n\n" + final_text + "\n")


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    lint_only = "--lint-only" in argv
    if len(args) != 1:
        print(__doc__)
        return 2

    plan_arg = Path(args[0])
    plan_path = plan_arg if plan_arg.exists() else PLANS_ROOT / args[0] / "plan.md"
    if plan_path.is_dir():
        plan_path = plan_path / "plan.md"
    if not plan_path.exists():
        print(f"executor: plan not found: {args[0]}")
        return 2
    plan_path = plan_path.resolve()
    plan_dir = plan_path.parent
    plan_id = plan_dir.name
    plan_text = plan_path.read_text()

    errors = lint_plan(plan_text)
    if errors:
        print(f"executor: lint FAILED for {plan_path}:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"executor: lint passed for {plan_path}")
    if lint_only:
        return 0

    # v1 policy: approval-marked plans are refused, not supported yet.
    if plan_has_marker(plan_text):
        print(
            "executor: plan contains an '**approval required**' step; "
            "v1 does not support marked plans — refusing to run."
        )
        return 1

    rule_prompt = RULE_PROMPT_PATH.read_text()
    messages = [
        {"role": "system", "content": rule_prompt},
        {"role": "user", "content": f"PLAN ARTIFACT (plan_id: {plan_id}):\n\n{plan_text}"},
    ]

    meta = {
        "plan_id": plan_id,
        "model": MODEL,
        "ollama_url": OLLAMA_URL,
        "started": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ended": None,
        "turns": 0,
        "commands_executed": 0,
        "harness_outcome": "running",
    }

    started_at = time.time()
    final_text = None
    while True:
        if meta["turns"] >= MAX_TURNS:
            meta["harness_outcome"] = "turn-cap-hit"
            break
        if time.time() - started_at > WALL_CLOCK_CAP_S:
            meta["harness_outcome"] = "time-cap-hit"
            break

        try:
            response = chat(messages)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            meta["harness_outcome"] = f"chat-error: {exc}"
            break

        meta["turns"] += 1
        msg = response.get("message", {})
        messages.append(msg)
        write_transcript(plan_dir, meta, messages)

        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            final_text = msg.get("content", "")
            meta["harness_outcome"] = "model-finished"
            break

        for call in tool_calls:
            fn = call.get("function", {})
            raw_args = fn.get("arguments", {})
            if isinstance(raw_args, str):
                try:
                    raw_args = json.loads(raw_args)
                except json.JSONDecodeError:
                    raw_args = {}
            command = raw_args.get("command", "")

            # Mirror of the lint at runtime: an unmarked plan may never
            # grow a gated flag through the model's own command text.
            if any(flag in command for flag in GATED_FLAGS) and not plan_has_marker(
                plan_text
            ):
                result = {
                    "command": command,
                    "exit_code": None,
                    "stdout": "",
                    "stderr": (
                        "harness: REFUSED — command contains --yes/"
                        "--allow-destroy but the plan has no approval-marked "
                        "step. This is a stop condition; report it."
                    ),
                    "duration_s": 0,
                }
            else:
                print(f"executor: turn {meta['turns']}: run_command: {command}")
                result = run_command(command)
                meta["commands_executed"] += 1

            messages.append(
                {
                    "role": "tool",
                    "tool_name": "run_command",
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )
        write_transcript(plan_dir, meta, messages)

    meta["ended"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    write_transcript(plan_dir, meta, messages)
    if final_text is None:
        final_text = (
            f"(no final model message — harness outcome: {meta['harness_outcome']})"
        )
    write_report(plan_dir, meta, final_text)
    print(
        f"executor: done — outcome={meta['harness_outcome']} turns={meta['turns']} "
        f"commands={meta['commands_executed']}"
    )
    print(f"executor: wrote {plan_dir / 'transcript.json'} and {plan_dir / 'report.md'}")
    return 0 if meta["harness_outcome"] == "model-finished" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
