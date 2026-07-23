# Permission Fix Step 2 Report: Update nodeutils Privileged-Probe Execution

Date: 2026-07-23

## Status

**Complete. Committed locally in the `nodeutils` submodule (`9351db9`); not pushed.**

No live host was touched. This step only changes `nodeutils/proxmox_inventory.py`, its tests, and
its README, and runs entirely against local unit tests.

## What changed

### `run_pvesh()` (`proxmox_inventory.py`)

Replaced the single-line `run_command(["pvesh", "get", path, "--output-format", "json"])` call
(which collapsed every non-zero result into `None`, producing only
`"failed to run pvesh get <path>"`) with a dedicated subprocess path:

```python
PVESH_BIN = "/usr/bin/pvesh"
PVESH_HELPER_PATH = "/usr/local/libexec/nodeutils-pvesh-read"
SUDO_BIN = "/usr/bin/sudo"
```

These are the exact paths confirmed root-owned on `aghub` in Step 0 and installed by the
`nodeutils_pvesh_helper` role in Step 1 — hard-coded constants, not read from the host-local probe
YAML (which `nodeutils_user` can write), per the plan's explicit prohibition.

`_pvesh_argv(path)` selects the argv:

- `os.geteuid() == 0` → `[PVESH_BIN, "get", path, "--output-format", "json"]` (direct root
  invocation, unchanged behavior for manual/administrative collection).
- non-root → first checks `Path(PVESH_HELPER_PATH).is_file() and os.access(..., os.X_OK)`; if
  either fails, raises immediately with a specific privileged-helper-unavailable error **without
  invoking `sudo` at all**. Otherwise returns `[SUDO_BIN, "-n", PVESH_HELPER_PATH, path]`.

`run_pvesh()` then runs that argv once via `subprocess.run(..., timeout=timeout)` and classifies
the outcome into distinct, bounded errors:

| Condition | Result |
|---|---|
| helper missing/not executable | `ProxmoxInventoryError("privileged pvesh helper unavailable at ...")`, no subprocess spawned |
| `subprocess.TimeoutExpired` | `ProxmoxInventoryError("pvesh get <path> timed out after Ns")` |
| `OSError` invoking the argv | `ProxmoxInventoryError("failed to invoke pvesh for <path>: <ExcClass>")` |
| stderr contains `"a password is required"` | `ProxmoxInventoryError("passwordless sudo not authorized for pvesh get <path>")` |
| stderr starts with `"nodeutils-pvesh-read:"` | `ProxmoxInventoryError("privileged pvesh helper rejected <path>: ...")` |
| any other non-zero return code | `ProxmoxInventoryError("pvesh get <path> failed (rc=<rc>): <bounded stderr>")` |
| non-zero-but-successful stdout not valid JSON | `ProxmoxInventoryError("invalid JSON from pvesh get <path>: ...")` |

Stderr text embedded in any error message is bounded to 200 characters (`_bounded_stderr()`) so a
runaway or adversarial `pvesh`/helper output cannot dump unbounded content into nctl operation
evidence. Raw Proxmox JSON stdout is never echoed in an error message.

Non-Proxmox `auto` mode is unchanged: `collect_proxmox_inventory()` still returns
`{"enabled": False, "detected": False, "mode": "auto"}` before `run_pvesh` (or any subprocess) is
ever called, now asserted directly with a `subprocess.run` mock.

### README

Documented the helper/sudoers prerequisite and the root-bypass behavior in
`nodeutils/README.md`, right after the existing `pveversion`/`pvesh` command block, with a pointer
to `devdocs/small/permission_fix/plan_pvesh.md` in the superproject.

## Tests

`tests/test_proxmox_inventory.py` — 14 tests in this file (30 in the full suite), all passing:

- `test_auto_mode_skips_non_proxmox_host` — now also asserts `subprocess.run` is never called.
- `test_required_endpoint_failure_stops_collection` — a `run_pvesh` failure on `/cluster/status`
  propagates out of `collect_proxmox_inventory()` rather than being swallowed.
- `test_root_mode_invokes_direct_pvesh_with_exact_argv` — asserts the exact argv
  `["/usr/bin/pvesh", "get", "/cluster/status", "--output-format", "json"]`.
- `test_non_root_mode_invokes_only_sudo_helper` — asserts the exact argv
  `["/usr/bin/sudo", "-n", "/usr/local/libexec/nodeutils-pvesh-read", "/cluster/status"]`.
- `test_missing_helper_raises_specific_error` — asserts `subprocess.run` is never called when the
  helper file is absent.
- `test_denied_sudo_raises_specific_error`, `test_helper_path_rejection_raises_specific_error`,
  `test_pvesh_ipc_failure_is_distinct_from_helper_or_sudo_errors`, `test_timeout_is_distinct_error`,
  `test_invalid_json_is_distinct_error` — each asserts a distinct exception message shape for its
  scenario (via `assertRaisesRegex`), proving the six failure modes required by the plan are not
  collapsed into one generic message.
- `test_error_message_does_not_leak_unbounded_stderr` — feeds a 5000-character stderr and asserts
  the resulting exception message stays under 400 characters.

Existing tests that mock `run_pvesh` directly (`normalize_qemu_vm`/`normalize_lxc_container`
tests) are unaffected since the function's signature and return contract are unchanged.

Full suite and lint from `nodeutils/`:

```text
uv run pytest        -> 30 passed
uv run ruff check .  -> All checks passed!
```

`optional endpoints may degrade only where the existing collector contract already allows it` was
not modified: `/nodes/<node>/storage` and `/nodes/<node>/network` collection in
`collect_proxmox_inventory()` were already wrapped in `try/except ProxmoxInventoryError: pass`
before this change and remain so; `/cluster/status`, `/cluster/resources`, `/nodes`,
`/nodes/<node>/qemu`, and `/nodes/<node>/lxc` were already unwrapped and remain so, so their
failures still stop collection (verified by the new required-endpoint test above). Secret
redaction of Proxmox response keys is handled generically downstream by
`nodeutils_collect.bounded_value()` (`SUSPICIOUS_KEY_PARTS`, already covered by
`tests/test_inventory_report.py::test_suspicious_keys_are_redacted`) and required no change here.

## Not yet done (subsequent steps)

- `run_nodeutils_collect.yml` does not yet install the `nodeutils_pvesh_helper` role before
  collection (Step 3).
- No live `aghub` execution of this code path yet; all verification above is local/unit-level.
- The `nodeutils` submodule commit is not pushed, so `aghub`'s pinned-SHA clone (Step 4) cannot
  yet reach it.
