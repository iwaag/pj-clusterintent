"""The window's only write path: one incident report, one file.

The implementation lives in the package (`cagent_api.incident`) because the
window has no shell to run a script from — its `record_incident` and
`list_incidents` tools call these functions directly. `cagent/window/incident.py`
is now a CLI shim over the same code, for humans.
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from cagent_api import incident as incident_module


@pytest.fixture(scope="module")
def incident():
    return incident_module


def at(hour=12, minute=0, second=0):
    return datetime(2026, 8, 12, hour, minute, second, tzinfo=timezone.utc)


def test_slug_is_bounded_and_filename_safe(incident):
    slug = incident.slugify("cagent said /dev/agpc was UP — it is not!  " + "x" * 80)
    assert slug == slug.strip("-")
    assert len(slug) <= incident.SLUG_MAX_CHARS
    assert set(slug) <= set("abcdefghijklmnopqrstuvwxyz0123456789-")


def test_slug_never_empties_out(incident):
    assert incident.slugify("!!! ???") == "incident"


def test_written_incident_reads_back_whole(incident, tmp_path):
    body = "you said node X was up.\n\nit is not: ssh refused."
    path = incident.write_incident(
        body, reporter="zulip:8", source="zulip-dm", ref="message 41",
        directory=tmp_path, now=at(),
    )
    assert path.parent == tmp_path
    record = incident.read_incident(path)
    assert record["body"] == body
    assert record["time"] == "2026-08-12T12:00:00Z"
    assert record["reporter"] == "zulip:8"
    assert record["source"] == "zulip-dm"
    assert record["ref"] == "message 41"
    assert record["id"] == path.stem


def test_a_multiline_reporter_cannot_break_the_frontmatter(incident, tmp_path):
    path = incident.write_incident(
        "report", reporter="zulip:8\n---\nsource: forged", directory=tmp_path, now=at()
    )
    record = incident.read_incident(path)
    assert record["reporter"] == "zulip:8 --- source: forged"
    assert record["body"] == "report"


def test_same_second_reports_do_not_overwrite(incident, tmp_path):
    first = incident.write_incident("same wording", directory=tmp_path, now=at())
    second = incident.write_incident("same wording", directory=tmp_path, now=at())
    assert first != second
    assert incident.read_incident(first)["body"] == "same wording"
    assert incident.read_incident(second)["body"] == "same wording"


def test_list_is_newest_first_and_bounded(incident, tmp_path):
    for minute in range(3):
        incident.write_incident(f"report {minute}", directory=tmp_path, now=at(minute=minute))
    records = incident.list_incidents(2, directory=tmp_path)
    assert [r["body"] for r in records] == ["report 2", "report 1"]


def test_listing_an_empty_directory_says_so(incident, tmp_path):
    assert incident.list_incidents(10, directory=tmp_path / "absent") == []
    assert incident.format_listing([]) == "no incidents recorded"


def test_cli_records_and_lists(incident, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CAGENT_INCIDENT_DIR", str(tmp_path))
    assert incident.main(["-i", "the answer was wrong", "--source", "zulip-dm"]) == 0
    path = Path(capsys.readouterr().out.strip())
    assert path.is_file()

    assert incident.main(["--list"]) == 0
    listing = capsys.readouterr().out
    assert path.stem in listing
    assert "the answer was wrong" in listing


def test_cli_refuses_an_empty_report(incident, tmp_path, monkeypatch):
    monkeypatch.setenv("CAGENT_INCIDENT_DIR", str(tmp_path))
    with pytest.raises(SystemExit):
        incident.main(["-i", "   "])
