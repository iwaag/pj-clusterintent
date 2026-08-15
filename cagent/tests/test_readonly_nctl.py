"""The shared read-only nctl surface, and the `cagent` CLI over it.

These refusal tests moved here with the allow-list extraction from
`agent_runner`; the surface is defined once, so it is tested once. The CLI
tests then pin only what the CLI adds: that argparse composes exactly the
argv the allow-list admits — nothing the parser accepts may be refused.
"""

from __future__ import annotations

import pytest

from cagent_api import readonly_nctl
from cagent_api.cli import build_parser, compose
from cagent_api.readonly_nctl import nctl_readonly, validate


# --- the allow-list ---------------------------------------------------------


@pytest.mark.parametrize(
    "args",
    [
        "reconcile --yes",
        "desired apply -f x.yaml",
        "prune",
        "lifecycle agpc retired",
        "apply dnsmasq",
        "status; rm -rf /",
        "drift && reconcile",
        "drift; reconcile --yes",
        "ops show 01KX extra",
        "status --output json",
        "",
    ],
)
def test_anything_that_is_not_read_only_is_refused(tmp_path, args):
    result = nctl_readonly(tmp_path, args)
    assert result.startswith("refused:")


def test_a_refusal_names_what_is_available(tmp_path):
    result = nctl_readonly(tmp_path, "reconcile")
    for available in ("status", "drift", "relations", "actual", "ops list", "ops show"):
        assert available in result


def test_an_unavailable_option_is_refused_even_on_an_available_subcommand(tmp_path):
    assert nctl_readonly(tmp_path, "drift --yes").startswith("refused:")
    assert nctl_readonly(tmp_path, "drift --output x").startswith("refused:")


def test_read_only_subcommands_are_accepted(monkeypatch, tmp_path):
    """Accepted means "reaches the argv", checked without running nctl."""
    seen = []

    class Done:
        returncode, stdout, stderr = 0, "{}", ""

    monkeypatch.setattr(
        readonly_nctl.subprocess, "run", lambda argv, **kw: seen.append(argv) or Done()
    )
    for args in ("status", "drift --json", "drift --host agpc", "relations",
                 "actual --json --detail", "ops list --limit 5", "ops show 01KX"):
        assert not nctl_readonly(tmp_path, args).startswith("refused:")
    assert seen[0] == ["uv", "run", "--project", "nctl", "nctl", "status"]
    assert seen[-1] == ["uv", "run", "--project", "nctl", "nctl", "ops", "show", "01KX"]


# --- the CLI over the same surface ------------------------------------------


@pytest.mark.parametrize(
    ("argv", "parts"),
    [
        (["status"], ["status"]),
        (["status", "--json"], ["status", "--json"]),
        (["drift", "--host", "agpc", "--json"], ["drift", "--json", "--host", "agpc"]),
        (["relations"], ["relations"]),
        (["actual", "--json", "--detail"], ["actual", "--json", "--detail"]),
        (["ops", "list", "--limit", "5"], ["ops", "list", "--limit", "5"]),
        (
            ["ops", "show", "01KX", "--after-seq", "3"],
            ["ops", "show", "01KX", "--after-seq", "3"],
        ),
    ],
)
def test_every_cli_form_composes_an_argv_the_allow_list_admits(argv, parts):
    composed = compose(build_parser().parse_args(argv))
    assert composed == parts
    validated, refusal = validate(" ".join(composed))
    assert refusal is None and validated == parts


def test_the_cli_offers_nothing_outside_the_allow_list():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["reconcile"])
    with pytest.raises(SystemExit):
        parser.parse_args(["desired", "export"])
    with pytest.raises(SystemExit):
        parser.parse_args(["drift", "--yes"])
