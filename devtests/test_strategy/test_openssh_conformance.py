"""Tier A real-tool proof: nctl's SSH policy agrees with installed OpenSSH.

This owns external OpenSSH behavior only. Trust parsing and reconcile sequencing remain in nctl's
focused tests. Positive evidence is a real loopback keyscan, a real `ssh -G` resolution, and nctl
preflight entries produced from the fixture's offered key.
"""

from __future__ import annotations

import os
import shlex
import shutil
import socket
import subprocess
import time
from pathlib import Path

import pytest

from nctl_core.config import Config
from nctl_core.production.composer import ResolvedSshTarget
from nctl_core.reconcile.ssh_preflight import (
    STATUS_MISMATCH,
    STATUS_READY,
    STATUS_UNENROLLED,
    verify_resolved_ssh_targets,
)
from nctl_core.ssh_enroll import (
    SshStoreReadError,
    default_ssh_probe_runner,
    load_managed_ssh_store,
    scan_offered_keys,
)
from nctl_core.ssh_trust import build_ansible_ssh_common_args, derive_host_key_alias


NODE_ID = "27818c12-fe15-4c9f-83d0-7949523f6c33"
SLUG = "p3-openssh-fixture"


def _required_binary(name: str) -> str:
    path = shutil.which(name)
    assert path is not None, f"required Phase 3 OpenSSH prerequisite is missing: {name}"
    return path


def _free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, text=True, capture_output=True, check=True)


def _config(tmp_path: Path, known_hosts: Path) -> Config:
    path = tmp_path / "nctl.toml"
    path.write_text(
        "\n".join(
            [
                "[nautobot]",
                'url = "http://127.0.0.1:9"',
                "",
                "[inventory]",
                f'dumps_dir = "{tmp_path / "dumps"}"',
                "",
                "[events]",
                f'log_dir = "{tmp_path / "events"}"',
                "",
                "[ansible]",
                f'playbook_dir = "{tmp_path / "ansible"}"',
                'inventory = "inventory.yml"',
                "",
                "[repo]",
                f'root = "{tmp_path}"',
                "",
                "[ssh]",
                f'known_hosts_file = "{known_hosts}"',
                f'lock_path = "{tmp_path / "ssh.lock"}"',
            ]
        )
        + "\n"
    )
    return Config.load(path)


@pytest.fixture
def sshd_fixture(tmp_path: Path):
    ssh = _required_binary("ssh")
    sshd = _required_binary("sshd")
    ssh_keygen = _required_binary("ssh-keygen")
    _required_binary("ssh-keyscan")
    port = _free_loopback_port()
    host_key = tmp_path / "host_ed25519"
    client_key = tmp_path / "client_ed25519"
    authorized_keys = tmp_path / "authorized_keys"
    _run([ssh_keygen, "-q", "-t", "ed25519", "-N", "", "-f", str(host_key)])
    _run([ssh_keygen, "-q", "-t", "ed25519", "-N", "", "-f", str(client_key)])
    authorized_keys.write_text((client_key.with_suffix(".pub")).read_text())
    os.chmod(authorized_keys, 0o600)
    config = tmp_path / "sshd_config"
    config.write_text(
        "\n".join(
            [
                "ListenAddress 127.0.0.1",
                f"Port {port}",
                f"HostKey {host_key}",
                f"PidFile {tmp_path / 'sshd.pid'}",
                f"AuthorizedKeysFile {authorized_keys}",
                "PasswordAuthentication no",
                "KbdInteractiveAuthentication no",
                "ChallengeResponseAuthentication no",
                "PubkeyAuthentication yes",
                "UsePAM no",
                "LogLevel ERROR",
            ]
        )
        + "\n"
    )
    _run([sshd, "-t", "-f", str(config)])
    process = subprocess.Popen(
        [sshd, "-D", "-e", "-f", str(config)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        probe = default_ssh_probe_runner()
        deadline = time.monotonic() + 10
        while True:
            try:
                offered = scan_offered_keys(probe, "127.0.0.1", port, 2)
            except Exception:
                offered = []
            if offered:
                break
            if process.poll() is not None or time.monotonic() >= deadline:
                stderr = process.stderr.read() if process.stderr else ""
                pytest.fail(f"fixture sshd did not offer a host key: {stderr}")
            time.sleep(0.05)
        yield {"ssh": ssh, "port": port, "offered": offered}
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as check:
            assert check.connect_ex(("127.0.0.1", port)) != 0, "fixture sshd port remained open after teardown"


def _target(port: int) -> ResolvedSshTarget:
    return ResolvedSshTarget(
        slug=SLUG,
        desired_node_id=NODE_ID,
        alias=derive_host_key_alias(NODE_ID),
        route="127.0.0.1",
        port=port,
        generation_id="p3-fixture-generation",
    )


def _write_store(path: Path, *, alias: str, key_type: str, key_blob: str) -> None:
    path.write_text(f"{alias} {key_type} {key_blob}\n")
    os.chmod(path, 0o600)


def test_real_openssh_alias_port_store_and_effective_options(sshd_fixture, tmp_path: Path):
    """Tier A: exact alias/store/port succeeds; endpoint and legacy port names do not."""
    key = sshd_fixture["offered"][0]
    known_hosts = tmp_path / "managed_known_hosts"
    target = _target(sshd_fixture["port"])
    cfg = _config(tmp_path, known_hosts)
    _write_store(known_hosts, alias=target.alias, key_type=key.key_type, key_blob=key.key_blob_b64)

    [entry] = verify_resolved_ssh_targets(
        cfg, [SLUG], {SLUG: target}, default_ssh_probe_runner(), round_index=1
    )
    assert entry.status == STATUS_READY
    assert entry.route == "127.0.0.1" and entry.port == sshd_fixture["port"]
    assert entry.managed_fingerprints == entry.offered_fingerprints
    assert entry.managed_fingerprints and all(value.startswith("SHA256:") for value in entry.managed_fingerprints)

    # A syntactically valid historical bracketed alias is recognized as obsolete but cannot enroll.
    _write_store(known_hosts, alias=f"[{target.alias}]:{target.port}", key_type=key.key_type, key_blob=key.key_blob_b64)
    [legacy_only] = verify_resolved_ssh_targets(cfg, [SLUG], {SLUG: target}, default_ssh_probe_runner())
    assert legacy_only.status == STATUS_UNENROLLED

    # Endpoint naming is not a permitted managed-store identity: fail closed rather than allowing a
    # route name to satisfy the stable DesiredNode alias.
    _write_store(known_hosts, alias="127.0.0.1", key_type=key.key_type, key_blob=key.key_blob_b64)
    with pytest.raises(SshStoreReadError):
        verify_resolved_ssh_targets(cfg, [SLUG], {SLUG: target}, default_ssh_probe_runner())

    _write_store(known_hosts, alias=target.alias, key_type=key.key_type, key_blob=key.key_blob_b64)
    args = build_ansible_ssh_common_args(target.alias, str(known_hosts))
    completed = _run(
        [sshd_fixture["ssh"], "-G", "-F", "/dev/null", "-p", str(target.port), *shlex.split(args), target.route]
    )
    effective = dict(line.split(" ", 1) for line in completed.stdout.splitlines() if " " in line)
    assert effective["hostname"] == target.route
    assert effective["port"] == str(target.port)
    assert effective["hostkeyalias"] == target.alias
    assert effective["userknownhostsfile"] == str(known_hosts)
    # OpenSSH normalizes the nctl-supplied `StrictHostKeyChecking=yes` to its
    # effective boolean spelling in `ssh -G` output.
    assert effective["stricthostkeychecking"] == "true"
    assert effective["checkhostip"] == "no"
    assert effective["updatehostkeys"] == "false"


def test_real_openssh_offered_mismatch_and_store_failures(sshd_fixture, tmp_path: Path):
    """Tier A: mismatch and corrupt stores fail before any non-fixture target can be considered."""
    key = sshd_fixture["offered"][0]
    known_hosts = tmp_path / "managed_known_hosts"
    target = _target(sshd_fixture["port"])
    cfg = _config(tmp_path, known_hosts)
    ssh_keygen = _required_binary("ssh-keygen")
    other = tmp_path / "other_ed25519"
    _run([ssh_keygen, "-q", "-t", "ed25519", "-N", "", "-f", str(other)])
    other_type, other_blob = other.with_suffix(".pub").read_text().split()[:2]
    _write_store(known_hosts, alias=target.alias, key_type=other_type, key_blob=other_blob)
    [mismatch] = verify_resolved_ssh_targets(cfg, [SLUG], {SLUG: target}, default_ssh_probe_runner())
    assert mismatch.status == STATUS_MISMATCH
    assert mismatch.managed_fingerprints != mismatch.offered_fingerprints

    known_hosts.write_text("not-a-managed-known-hosts-line\n")
    with pytest.raises(SshStoreReadError):
        load_managed_ssh_store(known_hosts)
    known_hosts.write_bytes(b"\xff\xfe\x00")
    with pytest.raises(SshStoreReadError):
        verify_resolved_ssh_targets(cfg, [SLUG], {SLUG: target}, default_ssh_probe_runner())

    # Raw key blobs must not enter an nctl result; the public preflight model exposes fingerprints.
    assert key.key_blob_b64 not in str(mismatch.model_dump())
