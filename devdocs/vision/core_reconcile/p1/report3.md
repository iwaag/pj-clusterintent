# Phase 1 Report — Step 3 (`nctl render dnsmasq` + parity gate)

Date: 2026-07-14. Implements [p1/plan.md](plan.md) Step 3. Continues from
[report2.md](report2.md) (the pinned GraphQL fetch layer).

## What was built

- New module `nctl/src/nctl_core/dnsmasq_render.py`:
  - `build_dnsmasq_render(cfg) -> Envelope[DnsmasqRenderData]` — resolves the Nautobot token, calls
    Step 2's `fetch_dnsmasq_inputs`, feeds the result through Step 1's `export_dnsmasq_records` /
    `render_dnsmasq_records_conf` / `dnsmasq_export_payload`, and wraps it in the
    `nctl.render.dnsmasq.v1` envelope. `DnsmasqRenderData` carries `schema_version`, `summary`,
    `dns_records`, `dhcp_reservations`, `dhcp_ranges`, `skipped`, and `conf` — exactly the payload
    shape the plan specified (and, per the plan's note, deliberately the shape Phase 2's drift
    engine will read as the "desired side").
    - Degrades the same way `status.py` does: a token-resolution or fetch failure returns `ok=False`
      with a coded `EnvelopeError` (`nautobot_token_error` / `nautobot_fetch_failed`) instead of
      raising, so the CLI always gets an envelope to render.
    - No operation ID, no event log — per the plan, render is a single synchronous GraphQL round
      trip plus a pure computation; `apply` (Step 6) is where long-running-operation conventions
      apply.
  - `render_dnsmasq_conf_text` / `render_dnsmasq_summary_text` — the two text renderings the CLI
    needs (raw conf for the pipeable default; a four-line count summary for the `--out` case),
    both falling back to `error [code]: message` lines when the envelope isn't ok.
- `nctl/src/nctl_core/cli/main.py`: added a `render` sub-app (`app.add_typer(render_app,
  name="render")`) with `nctl render dnsmasq [--out PATH] [--json] [--config PATH]`:
  - `--json` prints the envelope, full stop.
  - Plain default prints the conf to stdout (pipeable) or error text.
  - `--out` writes the conf to the given path and prints the four-line summary instead — but only
    on success; a failed envelope with `--out` set still prints the error text and does not touch
    the file (verified by test, see below).
  - Exit code 0 on `ok`, 1 otherwise, matching `status`'s convention.
- Tests: `tests/test_dnsmasq_render.py` (6 cases — one-endpoint happy path incl. header/format
  checks, empty-desired-state, Nautobot-failure degradation, error-text rendering, summary-text
  rendering, and an envelope JSON key-shape check) and `tests/test_cli_render_dnsmasq.py` (4 cases
  covering the three output modes plus the failure/no-file-written case), following the
  monkeypatched-CLI and respx-mocked-client patterns already used for `status`.

## Parity gate (live, per the plan)

Ran the actual gate the plan calls for, against the dev Nautobot instance from
`.local/localenv_memo.md`:

1. Triggered the live `Export dnsmasq Records` Job via `POST /api/extras/jobs/{id}/run/`, polled
   `/api/extras/job-results/{id}/` to `SUCCESS`, and downloaded both file-proxy artifacts
   (`dnsmasq-records.conf`, `dnsmasq-export.json`) via `/api/extras/file-proxies/.../download/`.
2. Ran `nctl render dnsmasq --out ... --config nctl.toml` and separately `nctl render dnsmasq
   --json` against the same live data (no writes happened in between).
3. Compared:
   - **Record lines**: `diff` of both `.conf` files with headers stripped (`tail -n +5` /
     `tail -n +4`, since the Job's file has one extra `job_result_id` header line nctl's doesn't) —
     **zero diff**, all 5 `host-record` lines, 3 `dhcp-host` lines, and the 1 `dhcp-range` line
     byte-identical.
   - **Summary counts**: the Job's `dnsmasq-export.json` `summary` object vs. `nctl render dnsmasq
     --json`'s `data.summary` — identical key-for-key (`dns_records: 5`, `dhcp_reservations: 3`,
     `dhcp_ranges: 1`, `total_endpoints: 5`, `total_ranges: 3`, `skipped.details: 4`, etc.).
   - **Skip reasons**: both skipped-detail lists (2 `dhcp_reservation` entries, 2 `dhcp_range`
     entries) carry identical `reasons` arrays, e.g. `['endpoint_evaluation_not_dhcp_ready',
     'ip_policy_not_dhcp_reserved', 'missing_actual_node', 'missing_mac_address']` for the
     `agdnsmasq` static endpoint on both sides.
4. Saved all four artifacts as fixtures in `devdocs/vision/core_reconcile/p1/parity/`:
   `job-dnsmasq-records.conf`, `job-dnsmasq-export.json` (from the Job), `nctl-dnsmasq-records.conf`,
   `nctl-dnsmasq-render.json` (from `nctl render dnsmasq`).

No mismatch found — Step 1/2's port was correct on live data, first try.

## Verification

- `uv run pytest -q` (full nctl suite) — 77 passed, 0 failures.
- The parity gate above, run against live dev Nautobot (not mocked).

## Deviations from plan

None. Built exactly the CLI surface, envelope schema, and parity-gate procedure the plan
specified, including saving both artifact pairs into the report directory.

## Commit boundary

Clean, self-contained: `dnsmasq_render.py`, the `render dnsmasq` CLI wiring, their tests (all
green), plus the parity fixtures under `p1/parity/`. This completes commit 1 of 5 from the plan's
suggested order ("nctl: renderer port + GraphQL fetch + `render dnsmasq` + tests; parity gate run
against live before proceeding") — the parity gate the plan required before Step 4 touches
anything in nintent has now run and passed.

**Not done yet, deliberately left for the next commit(s):**
- Step 4 — delete `ExportDnsmasqRecords`, `dnsmasq.py`, and `test_dnsmasq.py` from nintent, bump
  its version, and go through the single push/rebuild cycle (needs the user to push, per
  `.local/localenv_memo.md`).
- Step 5 — rewrite the `ansible_agdev` playbook to deploy-only.
- Step 6 — `nctl apply dnsmasq` (the first long-running command: operation ID + JSON Lines events
  + `[ansible]` config table).
- Step 7 — CLI docs and final phase report.

## Exit criteria status

- [x] `nctl render dnsmasq` output matches the last Job export on live data (record lines, summary
  counts, skip reasons — parity artifacts saved in `p1/parity/`).
- [ ] `nctl apply dnsmasq` — pending Step 6.
- [ ] `nintent` contains no dnsmasq rendering — pending Step 4.
- [ ] The dnsmasq playbook is deploy-only — pending Step 5.
- [x] `uv run pytest` passes in nctl, including the ported dnsmasq vocabulary tests (77 passed).

Next: Step 4 — delete the Job-export path in nintent (needs the user to push once nintent's commit
lands, then rebuild/restart the dev Nautobot container).
