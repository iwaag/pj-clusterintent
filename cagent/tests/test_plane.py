"""cagent's Plane policy: one fixed project, one Work per topic, no markers.

The client itself (`agag.plane`) is tested in pyagag. What is pinned here is
only cagent's own decisions — everything lands in `ClusterAdmin` (created on
first use, no `[AUTO]` marker), the external key is channel/topic, and a
Work carries no labels: nothing selects these for automated execution yet.
"""

from __future__ import annotations

import urllib.parse

import pytest
from agag import plane as shared

from cagent_api import plane

CONFIG = shared.PlaneConfig("http://plane.invalid", "key", "ws")
CLUSTERADMIN = {"id": "p-ca", "name": "ClusterAdmin", "identifier": "CA"}
STATES = [
    {"id": "s-backlog", "name": "Backlog", "group": "backlog"},
    {"id": "s-ready", "name": "Ready", "group": "unstarted"},
]


class Plane:
    """A Plane whose whole surface is the calls this policy makes."""

    def __init__(self, projects=(CLUSTERADMIN,)):
        self.projects = list(projects)
        self.issues = {}
        self.calls = []

    def __call__(self, method, url, *, headers, body=None, timeout=30):
        self.calls.append((method, url, body))
        if method == "GET" and "/projects/?" in url:
            return 200, {"results": self.projects}
        if method == "POST" and url.endswith("/projects/"):
            created = {"id": f"p-{len(self.projects) + 1}", **body}
            self.projects.append(created)
            return 201, created
        if method == "GET" and "/states/" in url:
            return 200, {"results": STATES}
        if method == "GET" and "external_id=" in url:
            key = urllib.parse.unquote(url.split("external_id=", 1)[1].split("&", 1)[0])
            found = self.issues.get(key)
            return (200, found) if found else (404, {"detail": "not found"})
        if method == "POST" and url.endswith("/issues/"):
            issue = {"id": f"i-{len(self.issues) + 1}", "sequence_id": 7, **body}
            self.issues[body["external_id"]] = issue
            return 201, issue
        if method == "PATCH":
            return 200, {"id": "patched", **(body or {})}
        raise AssertionError(f"unexpected call: {method} {url}")

    def bodies(self, method, suffix):
        return [b for m, url, b in self.calls if m == method and url.endswith(suffix)]


def wire(monkeypatch, fake):
    monkeypatch.setattr(shared, "_request_json", fake)
    monkeypatch.setattr(plane, "load_plane_config", lambda path=None: CONFIG)


def change_file(tmp_path, text="# Add a VM\n\nOne more guest on aghub.\n"):
    path = tmp_path / "requested_change.md"
    path.write_text(text)
    return path


def test_a_registered_work_carries_the_key_and_no_labels(monkeypatch, tmp_path):
    fake = Plane()
    wire(monkeypatch, fake)
    line = plane.register_change("general", "cagent-x", change_file(tmp_path))
    body = fake.bodies("POST", "/issues/")[0]
    assert (body["external_source"], body["external_id"]) == ("cagent", "general/cagent-x")
    assert "labels" not in body
    assert body["state"] == "s-ready"  # ready before backlog, per the shared rule
    assert line == 'created CA-7 "Add a VM" in ClusterAdmin'


def test_clusteradmin_is_created_on_first_use_without_the_auto_marker(
    monkeypatch, tmp_path
):
    """`[AUTO]` is work-selection vocabulary; these Works are nobody's to
    execute automatically this phase."""
    fake = Plane(projects=[])
    wire(monkeypatch, fake)
    plane.register_change("general", "cagent-x", change_file(tmp_path))
    created = fake.bodies("POST", "/projects/")[0]
    assert created["name"] == "ClusterAdmin"
    assert "[AUTO]" not in created["description"]


def test_serving_the_same_topic_twice_updates_one_work(monkeypatch, tmp_path):
    """The external key is the guard; N climbing must not fork the Work."""
    fake = Plane()
    wire(monkeypatch, fake)
    first = plane.register_change("general", "cagent-x", change_file(tmp_path))
    second = plane.register_change(
        "general", "cagent-x", change_file(tmp_path, "# Two VMs\n\nActually two.\n")
    )
    assert first.startswith("created ")
    assert second.startswith("updated ")
    assert len(fake.bodies("POST", "/issues/")) == 1
    assert fake.bodies("PATCH", "/")[0]["name"] == "Two VMs"


def test_the_external_key_is_the_channel_and_topic():
    assert plane.external_id("general", "cagent-y") == "general/cagent-y"


def test_credentials_default_to_the_repo_local_copy_and_honor_the_env_var(
    monkeypatch, tmp_path
):
    assert plane.PLANE_ENV.name == "plane-credentials.env"
    assert plane.PLANE_ENV.parent.name == ".local"
    override = tmp_path / "elsewhere.env"
    override.write_text(
        "PLANE_URL=http://plane.invalid\nPLANE_API_KEY=k\nPLANE_WORKSPACE_SLUG=ws\n"
    )
    monkeypatch.setenv(plane.PLANE_ENV_VAR, str(override))
    assert plane.load_plane_config().url == "http://plane.invalid"


def test_a_missing_credentials_file_is_reported(tmp_path):
    with pytest.raises(shared.PlaneError):
        plane.load_plane_config(tmp_path / "absent.env")
