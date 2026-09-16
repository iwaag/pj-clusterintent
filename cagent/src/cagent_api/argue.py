"""cagent in an argue (`argue` p1): a contribution when named, nothing else.

The mention route of cagent's topic listener exists for exactly one thing:
an argue (`agag.argue`), the conversation in `#argue` where a human develops
a desire with every agent. Named there, cagent answers in the same topic
from what it knows about the cluster — through the read-only `cagent` CLI
its operator role already uses — and names nobody. Its ordinary doors (its
own channel, `cagent-`/`change-` topics, the DM window) are untouched: a
mention anywhere else is logged and left, as it always was.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from agag.argue import ROLE as ARGUE_ROLE, is_argue_topic, participate, role_context_path
from agag.topics import next_record_path
from agag.zulip import ZulipClient, log

from .instance import CAGENT_ROOT, SPEC
from .role_run import run_role
from .topics_serve import RECORDS_ROOT, TOOLS_DIR, TOOLSET_NCTL, is_ack

ARGUE_TIMEOUT_SECONDS = 600
TOOLS_SOURCE = CAGENT_ROOT / "agent" / "tools"

__all__ = ["ARGUE_ROLE", "ARGUE_TIMEOUT_SECONDS", "handle_mention", "role_context", "run_argue"]


def role_context() -> str:
    return role_context_path(CAGENT_ROOT, ARGUE_ROLE).read_text(encoding="utf-8")


def run_argue(prompt: str, cwd: Path, invitation) -> str:
    """One `argue` run in the topic workspace, with the read-only cluster
    toolset beside the chatlog (`tools/`), recorded like every cagent run."""
    tools = cwd / TOOLS_DIR
    tools.mkdir(parents=True, exist_ok=True)
    source = TOOLS_SOURCE / TOOLSET_NCTL
    if source.is_file():
        shutil.copy(source, tools / TOOLSET_NCTL)
    output, _, exit_code = run_role(
        ARGUE_ROLE, prompt, cwd=cwd, timeout=ARGUE_TIMEOUT_SECONDS,
        record=next_record_path(RECORDS_ROOT / ARGUE_ROLE), transcript=cwd / "transcript.jsonl",
    )
    if exit_code != 0:
        raise RuntimeError(f"{ARGUE_ROLE} run exited {exit_code}: {output.strip()[:500]}")
    return output.strip()


def handle_mention(client: ZulipClient, channel: str, topic: str) -> None:
    if not is_argue_topic(channel, topic):
        log(f"mention in {channel!r}/{topic!r} is not an argue; ignoring")
        return
    log(f"argue invitation in {channel!r}/{topic!r}")
    participate(client, channel, topic, spec=SPEC, role_context=role_context(), run=run_argue,
                drop=is_ack, log=log)
