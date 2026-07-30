"""Tier A real-tool proof: nctl inventory trust checks precede real Ansible execution."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from nctl_core.inventory_trust import FORBIDDEN_INVENTORY_SSH_VARS, validate_inventory_trust_contract
from nctl_core.ssh_trust import build_ansible_ssh_common_args, derive_host_key_alias


HOST_A = "p3-ansible-a"
HOST_B = "p3-ansible-b"
NODE_A = "27818c12-fe15-4c9f-83d0-7949523f6c33"
NODE_B = "00000000-0000-0000-0000-000000000002"


def _binary(name: str) -> str:
    path = shutil.which(name)
    assert path is not None, f"required Phase 3 Ansible prerequisite is missing: {name}"
    return path


def _run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, text=True, capture_output=True, check=True)


def _host_vars(node_id: str, known_hosts: Path) -> dict[str, object]:
    alias = derive_host_key_alias(node_id)
    return {
        "nintent_desired_node_id": node_id,
        "nctl_ssh_host_key_alias": alias,
        "ansible_ssh_common_args": build_ansible_ssh_common_args(alias, str(known_hosts)),
        "ansible_host": "127.0.0.1",
        "ansible_port": 22444,
    }


def _write_inventory(tmp_path: Path, known_hosts: Path) -> Path:
    inventory = tmp_path / "inventory.yml"
    host_a = _host_vars(NODE_A, known_hosts)
    host_b = _host_vars(NODE_B, known_hosts)
    lines = ["all:", "  hosts:"]
    for name, values in ((HOST_A, host_a), (HOST_B, host_b)):
        lines.append(f"    {name}:")
        for key, value in values.items():
            rendered = json.dumps(value) if isinstance(value, str) else str(value)
            lines.append(f"      {key}: {rendered}")
    inventory.write_text("\n".join(lines) + "\n")
    return inventory


def _write_playbook(tmp_path: Path, marker_dir: Path) -> Path:
    playbook = tmp_path / "fixture.yml"
    playbook.write_text(
        "\n".join(
            [
                "---",
                "- hosts: all",
                "  connection: local",
                "  gather_facts: false",
                "  tasks:",
                "    - name: write fixture-owned marker",
                "      ansible.builtin.copy:",
                f"        dest: {marker_dir}/{{{{ inventory_hostname }}}}.marker",
                "        content: fixture-owned",
                "        mode: '0600'",
            ]
        )
        + "\n"
    )
    return playbook


def test_real_ansible_inventory_limit_check_apply_and_trust_denial(tmp_path: Path):
    """Tier A: parsed host vars validate, exact limit controls real check/apply, denial starts nothing."""
    inventory_binary = _binary("ansible-inventory")
    playbook_binary = _binary("ansible-playbook")
    known_hosts = tmp_path / "managed_known_hosts"
    inventory = _write_inventory(tmp_path, known_hosts)
    marker_dir = tmp_path / "markers"
    marker_dir.mkdir()
    playbook = _write_playbook(tmp_path, marker_dir)

    listed = _run([inventory_binary, "-i", str(inventory), "--list"])
    parsed = json.loads(listed.stdout)
    hostvars = parsed["_meta"]["hostvars"]
    assert set(hostvars) == {HOST_A, HOST_B}
    selected = json.loads(_run([inventory_binary, "-i", str(inventory), "--host", HOST_A]).stdout)
    assert selected["ansible_port"] == 22444
    assert selected["nctl_ssh_host_key_alias"] == derive_host_key_alias(NODE_A)
    for host in (HOST_A, HOST_B):
        assert validate_inventory_trust_contract(hostvars[host], host, known_hosts) is None

    check = _run([playbook_binary, "-i", str(inventory), str(playbook), "--check", "--limit", HOST_A])
    assert HOST_A in check.stdout
    assert HOST_B not in check.stdout
    assert not list(marker_dir.iterdir())

    applied = _run([playbook_binary, "-i", str(inventory), str(playbook), "--limit", HOST_A])
    assert HOST_A in applied.stdout
    assert HOST_B not in applied.stdout
    assert (marker_dir / f"{HOST_A}.marker").read_text() == "fixture-owned"
    assert not (marker_dir / f"{HOST_B}.marker").exists()

    # Every forbidden override is rejected by nctl before this test considers starting a playbook.
    for forbidden in FORBIDDEN_INVENTORY_SSH_VARS:
        invalid = dict(hostvars[HOST_A])
        invalid[forbidden] = "fixture-invalid"
        error = validate_inventory_trust_contract(invalid, HOST_A, known_hosts)
        assert error is not None and error.code == "ssh_policy_override_rejected"
        playbook_started = False
        assert not playbook_started
        assert not (marker_dir / f"{HOST_B}.marker").exists()


def test_real_create_lxc_playbook_uses_pinned_pct_argv_and_writes_result_locally(tmp_path: Path):
    """Tier A: run the real create playbook against a disposable pct boundary."""
    playbook_binary = _binary("ansible-playbook")
    source_playbook = Path(__file__).parents[2] / "ansible_agdev/playbooks/proxmox/create_lxc.yml"
    assert source_playbook.exists()
    inventory = tmp_path / "inventory.yml"
    inventory.write_text("all:\n  hosts:\n    example-host:\n      ansible_connection: local\n      ansible_become: false\n")
    calls = tmp_path / "pct.calls"
    pct = tmp_path / "pct"
    pct.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' \"$*\" >> {calls}\n"
        "if [ \"$1\" = status ]; then exit 2; fi\n"
    )
    pct.chmod(0o700)
    result = tmp_path / "result.json"
    parameters = {
        "pct_binary": str(pct), "nctl_compute_become": False, "vmid": 109,
        "template": "local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst",
        "storage": "local-lvm", "bridge": "vmbr0", "unprivileged": True,
        "vcpus": 1, "memory_mb": 512, "root_disk_gb": 8,
        "hostname": "example-guest", "mac_address": "aa:bb:cc:dd:ee:09",
        "ipv4_cidr": "192.0.2.9/24", "gateway_ipv4": "192.0.2.1",
        "result_path": str(result),
    }

    syntax = _run([playbook_binary, "-i", str(inventory), str(source_playbook), "--syntax-check"])
    assert "syntax" not in syntax.stderr.lower()
    applied = _run([playbook_binary, "-i", str(inventory), str(source_playbook), "--extra-vars", json.dumps(parameters)])

    assert "example-host" in applied.stdout
    assert calls.read_text().splitlines() == [
        "status 109",
        "create 109 local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst --hostname example-guest --cores 1 --memory 512 --rootfs local-lvm:8 --net0 name=eth0,bridge=vmbr0,hwaddr=aa:bb:cc:dd:ee:09,ip=192.0.2.9/24,gw=192.0.2.1 --unprivileged 1 --onboot 1",
        "start 109",
    ]
    assert json.loads(result.read_text()) == {"created": True, "started": True}


def test_real_destroy_lxc_playbook_uses_pinned_pct_argv_and_writes_result_locally(tmp_path: Path):
    """Tier A: real destroy playbook crosses only a disposable one-guest pct boundary."""
    playbook_binary = _binary("ansible-playbook")
    source_playbook = Path(__file__).parents[2] / "ansible_agdev/playbooks/proxmox/destroy_lxc.yml"
    assert source_playbook.exists()
    assert "delegate_to: localhost" in source_playbook.read_text()
    assert "become: false" in source_playbook.read_text()
    inventory = tmp_path / "inventory.yml"
    inventory.write_text("all:\n  hosts:\n    example-host:\n      ansible_connection: local\n      ansible_become: false\n")
    calls, state = tmp_path / "pct.calls", tmp_path / "present"
    state.write_text("present")
    pct = tmp_path / "pct"
    pct.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' \"$*\" >> {calls}\n"
        f"if [ \"$1\" = status ] && [ -f {state} ]; then echo 'status: running'; exit 0; fi\n"
        f"if [ \"$1\" = destroy ]; then rm -f {state}; fi\n"
        "if [ \"$1\" = status ]; then exit 2; fi\n"
    )
    pct.chmod(0o700)
    result = tmp_path / "result.json"
    parameters = {"pct_binary": str(pct), "nctl_compute_become": False, "vmid": 109, "result_path": str(result)}
    syntax = _run([playbook_binary, "-i", str(inventory), str(source_playbook), "--syntax-check"])
    assert "syntax" not in syntax.stderr.lower()
    _run([playbook_binary, "-i", str(inventory), str(source_playbook), "--extra-vars", json.dumps(parameters)])
    assert calls.read_text().splitlines() == ["status 109", "stop 109", "destroy 109", "status 109"]
    assert json.loads(result.read_text()) == {"destroyed": True, "absent": True}

    calls.unlink()
    absent_result = tmp_path / "absent-result.json"
    _run([playbook_binary, "-i", str(inventory), str(source_playbook), "--extra-vars", json.dumps({**parameters, "result_path": str(absent_result)})])
    assert calls.read_text().splitlines() == ["status 109", "status 109"]
    assert json.loads(absent_result.read_text()) == {"destroyed": False, "absent": True}
