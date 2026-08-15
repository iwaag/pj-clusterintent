"""Where cagent's topic change requests land in Plane.

The client itself is `agag.plane`, shared with agforge and agautolab. What
lives here is only cagent's policy on top of it: every `requested_change.md`
becomes a Work in the fixed `ClusterAdmin` project (created on first use),
keyed on `external_source="cagent"` + `"<channel>/<topic>"` so one topic is
one Work and a re-serve updates it. No labels and no description markers
this phase: nothing selects cagent's Works for automated execution yet, and
a Work indistinguishable from a hand-made one is the point.
"""

from __future__ import annotations

import os
from pathlib import Path

from agag.plane import (
    PlaneError,
    create_project,
    description_html,
    ensure_issue,
    find_issue_by_external,
    find_project,
    issue_label,
    load_plane_config as load_shared_plane_config,
    split_document,
    starting_state_id,
    update_issue,
)

from .role_run import REPO_ROOT

# The credentials are a git-ignored copy of `pj-agdev/.local/plane-credentials.env`
# (both agent families talk to the same Plane); the env var points elsewhere
# when a deployment keeps them elsewhere.
PLANE_ENV = REPO_ROOT / ".local" / "plane-credentials.env"
PLANE_ENV_VAR = "CAGENT_PLANE_ENV"

EXTERNAL_SOURCE = "cagent"
PROJECT_NAME = "ClusterAdmin"
PROJECT_DESCRIPTION = "Change requests for the cluster, registered by cagent."

__all__ = [
    "PLANE_ENV",
    "PLANE_ENV_VAR",
    "PlaneError",
    "ensure_project",
    "external_id",
    "load_plane_config",
    "register_change",
]


def load_plane_config(path: Path | None = None):
    if path is None:
        override = os.environ.get(PLANE_ENV_VAR)
        path = Path(override) if override else PLANE_ENV
    return load_shared_plane_config(path)


def external_id(channel: str, topic: str) -> str:
    """One topic, one key — however far the generation number climbs."""
    return f"{channel}/{topic}"


def ensure_project(config) -> dict:
    """The `ClusterAdmin` project, created on first use.

    Its description deliberately carries no `[AUTO]` marker: that is the
    vocabulary work *selection* scans, and nothing is meant to pick these
    Works up automatically this phase.
    """
    if project := find_project(config, PROJECT_NAME):
        return project
    return create_project(config, PROJECT_NAME, PROJECT_DESCRIPTION)


def register_change(channel: str, topic: str, change: Path) -> str:
    """Register one front `requested_change.md` as this topic's Plane Work.

    The file's first `#` heading is the title and the rest the description —
    the contract the front guide already spells. Returns the report line for
    the topic. Updating through the same external key is what keeps one
    topic to one Work.
    """
    title, description = split_document(change.read_text(encoding="utf-8"))
    config = load_plane_config()
    project = ensure_project(config)
    project_id = str(project["id"])
    key = external_id(channel, topic)
    if existing := find_issue_by_external(config, project_id, EXTERNAL_SOURCE, key):
        update_issue(
            config, project_id, str(existing["id"]),
            {"name": title.strip(), "description_html": description_html(description)},
        )
        line = f'updated {issue_label(project, existing)} "{title}"'
    else:
        issue, _ = ensure_issue(
            config,
            project_id,
            name=title,
            description=description,
            state=starting_state_id(config, project_id),
            external_source=EXTERNAL_SOURCE,
            external_id=key,
        )
        line = f'created {issue_label(project, issue)} "{title}"'
    return f"{line} in {project.get('name', '?')}"
