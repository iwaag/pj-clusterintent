"""This cagent instance's own name, and the spec the shared skeleton reads it by.

`cagent` is the agent; `cagent-agstudio1` is *this running instance of it*
(`<agent>-<instance label><N>`, the label being the host). The name carries
host information, so it lives in the ignored `.local/instance.toml`
(`instance.example.toml` shows the shape) and `CAGENT_INSTANCE_NAME`
overrides it.

The instance name is also the name of **cagent's own channel** — the channel
where its change records live and every topic is cagent's to answer. That is
the same convention agforge and agautolab follow, and it is why the name is
read from one place rather than spelled out at each use site.

cagent is not generated from the agag skeleton, so `SPEC` is used for what a
spec is actually good for here — the instance name, the sweep prefixes and
the roster block its introduction publishes — and not for the paths, which
this repository arranges its own way (credentials under the superproject's
`.local/zulip/`, not under the agent directory).
"""

from __future__ import annotations

from pathlib import Path

from agag.agent import AgentSpec

CAGENT_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CAGENT_ROOT.parent
FALLBACK_NAME = "cagent"

#: Request topics per the zulip_channel_topic workflow, in any subscribed
#: channel. A resolved topic is renamed "✔ cagent-…" and stops matching.
TOPIC_PREFIX = "cagent-"
#: Change records (`change_record.py`). They live in cagent's own channel, so
#: the prefix is what finds them again when somebody continues one from
#: elsewhere; in the channel every topic is cagent's anyway.
CHANGE_TOPIC_PREFIX = "change-"

SPEC = AgentSpec(
    FALLBACK_NAME, CAGENT_ROOT,
    plan_prefix=TOPIC_PREFIX, extra_prefixes=(CHANGE_TOPIC_PREFIX,),
)
INSTANCE_TOML = SPEC.instance_toml
INSTANCE_ENV_VAR = SPEC.instance_env_var

__all__ = [
    "CAGENT_ROOT",
    "CHANGE_TOPIC_PREFIX",
    "FALLBACK_NAME",
    "INSTANCE_ENV_VAR",
    "INSTANCE_TOML",
    "REPO_ROOT",
    "SPEC",
    "TOPIC_PREFIX",
    "instance_name",
    "own_channel",
]


def instance_name(path: Path | None = None) -> str:
    """This instance's name, from `CAGENT_INSTANCE_NAME` or `instance.toml`."""
    if path is None:
        return SPEC.instance_name()
    from agag.instance import instance_name as read

    return read(path, fallback=FALLBACK_NAME, env_var=INSTANCE_ENV_VAR)


def own_channel(path: Path | None = None) -> str:
    """The channel cagent owns — its instance name, by the shared convention."""
    return instance_name(path)
