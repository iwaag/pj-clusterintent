# Step 6 — Make desired MAC a safe dnsmasq consumer

Status: `complete`.

## Note on how this step was found

This report is written retroactively. The code for Step 6 was already fully implemented in
`nctl` commit `cb655c698312d864c311277e904c457213ae8d89` ("s4", 2026-07-25 12:20:59, landed
between the Step 5 commit `fa4b561` and the unrelated `remove_unused_surfaces` Phase 0-4 work),
but no `report3.6.md` was ever written and the parent plan/roadmap/handoff state still said
"Step 6 has not started." This report is the missing record for already-committed, already-tested
work, plus one small fix found while verifying it (see §4).

## 1. `src/nctl_core/dnsmasq.py`

- `DHCP_BLOCKING_SKIP_CODES = {"ambiguous_interface", "desired_mac_mismatch"}`: on an endpoint
  that is otherwise DHCP-eligible (`_dhcp_skip_reasons()` empty), either code is promoted from an
  ordinary per-line skip to a `blocking` finding that voids the whole shared dnsmasq file.
- `resolve_dhcp_reservation()`: when the endpoint carries a canonical desired MAC and the base
  completeness contract holds, `_resolve_desired_mac_reservation()` takes over — it emits a
  reservation from desired MAC alone with `actual_ref=None`/`confidence=deterministic_desired`
  when there is no actual evidence at all (rule 1), agrees and records both provenances when
  actual matches (rule 2), and returns a `blocking` result with zero `line`/`conf` contribution
  when actual disagrees (rule 3) or the actual interface picture is ambiguous (rule 5). When no
  desired MAC is present, the function is byte-identical to pre-Step-6 behavior (rule 4).
- `_blocking_finding()`/`export_dnsmasq_records()`: every `blocking` reservation becomes one
  structured finding (code, desired endpoint/node identity, desired MAC, actual candidates) in a
  new `DnsmasqExport.blocking_findings` list.

## 2. `src/nctl_core/dnsmasq_render.py`

- `RENDER_DNSMASQ_SCHEMA` bumped `nctl.render.dnsmasq.v2` -> `v3` (breaking, no dual-read, per
  repo convention).
- `compute_dnsmasq_render()`: if `export.blocking_findings` is non-empty, returns
  `DnsmasqRenderResult(blocked=True, conf="", content_sha256="")` — never a partial artifact.
- `build_dnsmasq_render()`: a blocked result produces `envelope.ok=False`, one `EnvelopeError` per
  finding, and `DnsmasqRenderData.partial_conf_preview` — a diagnostic-only field, structurally
  distinct from `conf`, so no caller can mistake it for deployable bytes.

## 3. Wiring into drift, reconcile, and apply

- `drift/evaluation.py`: `evaluate_endpoint_intent()` compares `DesiredEndpoint.mac_address`
  against the same interface-derived `mac_candidates` computation already used for the actual
  evaluation, adding `desired_mac_status` (`desired_only|agree|mismatch|ambiguous_actual`) to the
  deterministic summary and, on `mismatch`, a `desired_mac_mismatch` conflict gap. One shared
  computation feeds both drift and the dnsmasq renderer, so they cannot disagree.
- `drift/comparators.py` / `endpoint_intent_matching`: the new gap reaches structured JSON drift
  and human-readable CLI drift output for free (generic gap iteration, no comparator-specific
  code).
- `reconcile/classify.py`: `desired_mac_mismatch` added to `_MANUAL_REVIEW_CODES` — never an
  automatic action (`test_desired_mac_mismatch_is_manual_review_never_an_automatic_action`).
- `drift/evaluation_snapshot.py`: `_content_spec_by_service_id()` calls `compute_dnsmasq_render()`
  at most once per round; a blocked render suppresses the dnsmasq `ContentSpec` entirely (digest
  suppression), so no `service_config_mismatch`/`service_config_observation_missing` fires from a
  non-authoritative digest — the endpoint-level `desired_mac_mismatch` gap is the real signal.
- `dnsmasq_apply.py` / `reconcile/executor.py`'s `dnsmasq_config` action: both call
  `build_dnsmasq_render()` fresh and stop on `ok=False` before artifact write, SSH preflight, or
  `ansible-playbook` — proven for dry-run and apply mode with hard `AssertionError` traps on the
  Ansible/SSH call sites (`test_blocked_render_stops_before_any_write_or_ansible_call`,
  `test_dnsmasq_config_action_with_blocked_render_never_invokes_ansible`), i.e. zero SSH/Ansible
  calls, satisfying the plan's "direct-apply and planner rechecks" requirement.

## 4. One fix made while verifying this step

`cli/main.py`'s `RenderJsonOption` help string still read
`"Print the nctl.render.dnsmasq.v2 envelope as JSON."` after the schema was bumped to `v3` in the
same commit — a stale copy-paste the original commit missed. Fixed to say `v3` (see Step 7 commit;
this is a one-line doc-string correction, not a behavior change, so it is folded into the Step 7
review commit rather than given its own commit).

`docs/output-format.md` has no `nctl.render.dnsmasq.v2`/`v3` section at all (only
`nctl.apply.dnsmasq.v2`, a different/unrelated schema, is documented there); this gap predates
Step 6 — grepping the file finds no prior `render.dnsmasq` entry to have gone stale — and is left
unchanged as out of this step's scope.

## 5. Test evidence

`uv run pytest -q` (nctl): **954 passed** (re-run after the Step 7 doc-string fix below; count
matches the post-`remove_unused_surfaces`-Phase-1/2 baseline nctl is now on — Step 6's own tests
were part of that count both before and after this report).

Scenario coverage confirmed present and passing, mapped to the plan's Step 6 procedure:

1. rule 1 (no actual evidence at all) — `test_desired_mac_reservation_emitted_with_no_actual_evidence_at_all`,
   through the real `SourceSnapshot -> compute_dnsmasq_render()` path with mocked GraphQL (`respx`),
   not dict literals.
2. rules 2/4 (agree / desired-absent unchanged) — `test_no_mac_fixture_render_is_byte_identical_regression`.
3. rule 3 (mismatch blocks) — `test_desired_mac_mismatch_blocks_the_whole_render`,
   `test_endpoint_intent_matching_emits_desired_mac_mismatch_with_zero_comparator_changes`.
4. rule 5 (ambiguous actual is also blocking, but only when otherwise eligible) —
   `test_ambiguous_interface_is_promoted_to_blocking_on_an_otherwise_eligible_endpoint`,
   `test_ambiguous_interface_is_not_blocking_when_endpoint_is_ordinarily_ineligible`.
5. planner suppression — `test_desired_mac_mismatch_is_manual_review_never_an_automatic_action`.
6. direct-apply/executor zero-actuation — `test_blocked_render_stops_before_any_write_or_ansible_call`,
   `test_dnsmasq_config_action_with_blocked_render_never_invokes_ansible`.
7. recovery/non-repetition round-trip — `test_desired_mac_mismatch_then_resolved_round_trip`
   (blocked -> resolved -> re-blocked against the same snapshot shape, each state proven
   independently rather than assumed from the transition).
8. CLI boundary — `test_render_dnsmasq_blocked_leaves_pre_existing_file_untouched` (a blocked
   render must not overwrite a previously-written `--out` file), `test_render_dnsmasq_blocked_json_shows_the_blocking_finding`.

No live Nautobot/database access was used or required for Step 6 (nctl has no environment-backed
test path); all evidence is through mocked GraphQL responses shaped like the real schema, matching
the pattern already established through Step 5.

## Gate

A blocked diagnostic preview can never become an authoritative artifact or trigger an automatic
dnsmasq action: `compute_dnsmasq_render()` never returns non-empty `conf`/`content_sha256` when
blocked; `build_dnsmasq_apply()` and the `dnsmasq_config` reconcile action both stop before any
write/SSH/Ansible call; drift suppresses the dnsmasq digest comparison instead of comparing a
non-authoritative value; and the `desired_mac_mismatch` gap is manual-review-only. Confirmed by
direct test-suite inspection and one `uv run pytest -q` re-run (954 passed), not merely inferred
from commit messages.

Proceeding to Step 7.
