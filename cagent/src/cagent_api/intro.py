"""Post this cagent instance's introduction to the shared agents board.

    uv run --project cagent python -m cagent_api.intro

appends `params/intro.md` to `#agents` under `intro-<instance>`, with the
generated roster and execution-option blocks. The mechanics are `agag.intro`.

cagent keeps its Zulip credential where this superproject keeps every other
one — `.local/zulip/cagent.env`, `CAGENT_ZULIP_ENV` to move it — rather than
under the agent directory the way a generated agag agent does, so the client
is built here instead of by `agag.agent.intro_main`.
"""

from __future__ import annotations

import os
from pathlib import Path

from agag.agent import roster_for
from agag.intro import AGENTS_CHANNEL, intro_topic, post_intro
from agag.zulip import ZulipClient

from .instance import REPO_ROOT, SPEC, instance_name

DEFAULT_ZULIP_ENV = REPO_ROOT / ".local" / "zulip" / "cagent.env"
ZULIP_ENV_VAR = "CAGENT_ZULIP_ENV"
INTRO_PATH = SPEC.intro_path

__all__ = ["AGENTS_CHANNEL", "INTRO_PATH", "client", "main", "topic"]


def client() -> ZulipClient:
    return ZulipClient.from_env(Path(os.environ.get(ZULIP_ENV_VAR, str(DEFAULT_ZULIP_ENV))))


def topic() -> str:
    return intro_topic(instance_name())


def main() -> str:
    zulip = client()
    text = post_intro(
        zulip,
        instance=instance_name(),
        intro_path=INTRO_PATH,
        root=SPEC.root,
        roster=roster_for(SPEC, zulip),
        options=SPEC.published_options(str(zulip.whoami().get("full_name") or "")),
    )
    print(f"posted {len(text)} characters to {AGENTS_CHANNEL}/{topic()}")
    return text


if __name__ == "__main__":
    main()
