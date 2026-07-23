# Permission Fix Step 5 Report: Automated Verification

Date: 2026-07-23

## Status

**Complete. New integration test committed locally in `nodeutils` (`36e1c57`); not yet pushed.**

No live host was touched. This step runs the plan's full automated verification checklist and
adds the "highest-practical integration test for this boundary" it requires.

## Automated checklist (all from the plan)

```bash
cd nodeutils
uv run pytest        # 31 passed
uv run ruff check .  # All checks passed!

cd ../nctl
uv run pytest        # 964 passed, 1 warning (pre-existing Starlette/httpx deprecation)

cd ../ansible_agdev
ansible-playbook --syntax-check playbooks/nautobot/run_nodeutils_collect.yml
# -> playbook: playbooks/nautobot/run_nodeutils_collect.yml (no errors)
```

Also:

```bash
git diff --check          # clean in pj-clusterintent, nodeutils, ansible_agdev, and nctl
python -m compileall nodeutils/proxmox_inventory.py nodeutils/tests/test_proxmox_inventory.py \
  nodeutils/tests/test_pvesh_helper_integration.py \
  ansible_agdev/roles/nodeutils_pvesh_helper/tests/test_nodeutils_pvesh_read.py
# compileall does not compile extensionless files by default; the helper itself
# (roles/nodeutils_pvesh_helper/files/nodeutils-pvesh-read) was separately verified with
# py_compile.compile(..., doraise=True) -> no SyntaxError
```

All of the above passed with no errors on the first attempt after Steps 0-4's changes; the nctl
suite in particular is unchanged in count and warning from `report1.md`'s `963 passed` baseline
plus the one new `report2.md`-era test.

## The highest-practical integration test

Added `nodeutils/tests/test_pvesh_helper_integration.py`
(`PveshHelperBoundaryIntegrationTest.test_non_root_collection_through_real_helper_produces_readable_v2_report`),
exercising the exact chain the plan specifies:

```text
non-root collector
  -> exact sudo helper argv
  -> allowlisted fake pvesh JSON
  -> schema-v2 report written by non-root
  -> report remains readable by the normal retrieval path
```

Because the real, fixed `/usr/bin/pvesh` and the real sudoers grant only exist on `aghub` (covered
live in Step 6), this test substitutes:

- a **fake pvesh** (a small generated Python script) that only answers the 7 endpoint paths the
  collector actually calls (`/cluster/status`, `/cluster/resources`, `/nodes`,
  `/nodes/aghub/{qemu,lxc,storage,network}`) and logs every `get <path>` call it receives to a file;
- a **fake sudo** that strips `-n` and `os.execv`s the remaining argv directly (standing in for a
  granted, working sudoers rule — the point under test is the argv shape and the helper's own
  logic, not sudo's authorization mechanics, which are exercised live in Step 6); and
- a **byte-for-byte copy of the real helper source**
  (`ansible_agdev/roles/nodeutils_pvesh_helper/files/nodeutils-pvesh-read`), with only its shebang
  and its `PVESH_BIN` constant substituted (verified via an `assert` that the exact line
  `PVESH_BIN = "/usr/bin/pvesh"` is present before substituting, so the test breaks loudly if the
  helper's source shape ever changes instead of silently testing stale logic).

`nodeutils_collect.main(["collect", "--proxmox", "enabled", ...])` is invoked end-to-end (real
`collect_inventory()`, real `build_inventory_report()`, real `write_output()`) with only
`proxmox_inventory.os.geteuid`, `SUDO_BIN`, `PVESH_HELPER_PATH`, `is_proxmox_host`, and
`shutil.which` patched to point at the fakes and force the non-root/Proxmox-detected branch.

Assertions:

- `rc == 0`;
- the fake-pvesh call log exists and contains `get /cluster/status`, `get /cluster/resources`, and
  `get /nodes` — **positive evidence of execution**, so a silently short-circuited Proxmox-detection
  path (e.g. `is_proxmox_host()` returning `False`) cannot pass;
- the written report is mode `0600`;
- `report["schema_version"] == "nodeutils.inventory.v2"` and `report["facts"]["proxmox"]` shows
  `enabled=True, detected=True, cluster.nodes=["aghub"]` — proving the fake pvesh data round-tripped
  through the real helper's `os.execve` dispatch into the final report;
- the report satisfies `nctl_core.dumps.NodeDump`'s required-field contract (`schema_version`,
  `identity.hostname`, ISO `collected_at`, `facts`, `self_reported`), checked directly against the
  JSON rather than by importing `nctl_core` — nctl's virtualenv (`pydantic`, `yaml`) is not
  installed inside nodeutils' own `uv` environment, so a cross-venv import would fail for reasons
  unrelated to the boundary under test.

The test is `unittest.skipUnless(_HELPER_SRC.is_file(), ...)`-gated on the `ansible_agdev` sibling
directory being present, since `nodeutils` is also clonable standalone (as `aghub` does). This is
an environment-layout skip, not the "skipped Proxmox path" the plan says must not count as a pass
— when the sibling directory is present (as it is in this pj-clusterintent checkout and any CI
that checks out the full superproject), the test runs for real with no internal skip path.

## Deviation from a literal reading

The plan's illustrative snippet says the boundary test is one item in a general list; it does not
mandate a specific home repository. Placing it in `nodeutils/tests/` (rather than `nctl` or
`ansible_agdev`) was chosen because both `proxmox_inventory.py` and `nodeutils_collect.py` — the
code under test on the caller side — live there, and nodeutils already has one precedent
(`test_cross_repository_dnsmasq_v5_golden_digest`) for tests that reach toward shared/cross-repo
artifacts.

## Not yet done (subsequent steps)

- The new `nodeutils` commit (`36e1c57`) is local-only. Before Step 6's live run, it should be
  pushed (same as the Step 4 push) so the superproject gitlink can be re-pinned if desired --
  though this commit only adds a test file and does not change `aghub`'s runtime behavior.
- No live `aghub` execution yet. Step 6 (live security-boundary verification) is next and is the
  first step in this plan that installs anything on real infrastructure.
