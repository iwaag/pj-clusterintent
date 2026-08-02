# Step 3 report — Auth ledger + CLI surface

## What was done

- `cagent/src/cagent_api/ledger.py`: `Ledger` over a single append-only
  JSONL event log (`register`/`revoke`/`reactivate` events), current state
  per certificate serial derived by folding the log on every read. Row
  shape (`LedgerEntry`): `uuid`, `serial`, `fingerprint`, `issued_at`,
  `not_after`, `state` (`active`/`revoked`), `revoked_at`. Public
  identifiers only, matching the roadmap rule.
- **Cross-process consistency was the main design constraint**: the ledger
  file is written by one-shot `cagent-ledger` CLI invocations and read by
  the long-running `cagent-api` server (Step 4) on every request per
  contract.md, so there is deliberately **no in-memory cache carried
  between calls** — every `get`/`list`/`is_active` re-reads the file from
  disk, and every mutation appends under an advisory `fcntl.flock` so a
  concurrent CLI write and a server read/write can't interleave a torn
  line. This is what makes "revoke via CLI, next request rejected
  immediately" (Step 5b's test) actually true rather than dependent on
  server restart.
- Added `is_expired(serial, now=...)` as a ledger-side convenience even
  though TLS already enforces cert validity windows at the handshake layer
  (Step 0 finding) — kept for Step 4's evidence/diagnostics, not as a
  substitute for the TLS check.
- `cagent/src/cagent_api/ledger_cli.py`: the `cagent-ledger` console script
  (added to `pyproject.toml`), subcommands `list`, `show <serial>`,
  `register --uuid --serial --fingerprint --not-after` (the exact flags
  `cagent-ca sign-node` already prints as its suggested next command),
  `revoke <serial>`, and `reactivate <serial>` (needed for Step 5b's
  "revoke, confirm rejection, re-activate, confirm it works again" cycle —
  the plan only named `revoke` explicitly but implied reactivation was
  needed for that step). Default ledger path
  `~/.local/state/cagent/ledger/ledger.jsonl`, matching the existing
  evidence-directory convention (`~/.local/state/cagent/evidence/`).
- `cagent/tests/test_ledger.py` (7 tests) and `cagent/tests/test_ledger_cli.py`
  (4 tests): register/revoke/reactivate round trip, unregistered-serial
  rejection on revoke/reactivate, `list` ordering, `is_expired`, and —
  the one that actually matters most here — a **cross-instance test**
  proving a second `Ledger(path)` opened against the same file (simulating
  a separate process) sees writes made by the first.

## Deviations from the plan

None. Storage stayed a single JSONL file as suggested, no database. CLI
covers `list`/`show`/`register`/`revoke` as required by the plan, plus
`reactivate` (needed by Step 5b, not explicitly named by the plan but
implied by its re-enrollment/re-activation requirement).

## State

`uv run pytest -q` in `cagent/`: **49 passed** (was 37 at end of Step 2;
+7 `test_ledger.py`, +4 `test_ledger_cli.py`). No live ledger file created
under `.local/`/`~/.local/state/cagent/ledger/` — only `tmp_path`-scoped
test fixtures.

## Next

Step 4 — wire mTLS into the API server and add the connect-time checks
(ledger + DesiredNode validity) from `p2/contract.md`.
