# Step 3.8 report — Phase 3 strict closeout

Date: 2026-07-22 (JST)

## Result

Phase 3 is **complete against the original exit criteria**.

The phase first closed with an accepted safe-stop boundary while two facts remained explicit: the
direct Nautobot UI-entry interval had not been exercised, and production SSH host-key verification
had stopped the dnsmasq configuration action. Both follow-ups are now complete without weakening
SSH verification, adding diary schema, or introducing review automation:

1. `fix_sshkey4` proved the corrected SSH identity and dnsmasq content path through reversible live
   add/apply/observe/converge/remove/apply/observe/converge operations; and
2. a user-created UI Braindump was observed through nctl with no review row, then received exactly
   one current Alignment Review.

## Final live inventory

- `nctl braindump list --json` reports five `user_direct` Braindumps and five current reviews.
- The UI-created row `45255668-b0c4-456f-9d6c-a9fc0f611da1` was first recorded as
  `review_present: false`, `attention: unreviewed`, and `alignment_review: null`; review
  `550591e9-c18d-4fa3-a67b-55c8e3dc5f1c` was then created without changing its body or authorship.
- No agent recommendation was stored as a Braindump and no review-history mechanism or duplicate
  review row exists.
- Current drift is `converged: 4, unknown: 2`. The agdnsmasq node and dnsmasq service are converged;
  aghub remains unknown because it has no realized object/interface candidate, and agstudio remains
  unknown because its actual observation is stale.

## Three-case matrix

| Case | Live result |
|---|---|
| Direct/specific named-host wish | Stored and reviewed in the same AI-mediated interaction; unsupported Ollama/Qwen details stayed prose rather than becoming invented desired state. |
| Dynamic/vague placement preference | Preserved as conditional prose; no fixed placement, score, or ranking field was created without the missing user policy. |
| Fresh unexplained service | Fresh `prometheus` on agpc was asked about softly, never classified as unwanted; the user recorded a `user_direct` policy that unmanaged services are intentionally unmanaged for now. |

The later UI validation row separately proves the UI-to-nctl unreviewed lifecycle without claiming
that its body was the earlier private placement source.

## Structured loop and SSH completion

- The user separately approved `agdnsmasq` lifecycle `planned -> active` through the canonical
  `nctl lifecycle` REST/GraphQL path.
- Plan-only and apply were separate user gates with inspectable operation artifacts.
- The original apply safely stopped at the production SSH trust boundary.
- The separately planned and approved SSH initiatives replaced route-based identity with the stable
  DesiredNode UUID alias while retaining strict verification.
- `fix_sshkey4/report_step7.md` then proved a real scoped dnsmasq content mismatch, exact-host
  production preflight, successful deployment, fresh v2 observation/ingest, matching path/digest,
  and no repeated action. Its reverse operation restored the original desired and deployed content.
- The LAN and onboarding-policy reviews were subsequently replaced in the same rows to explain the
  successful current result; the placement review was also replaced to incorporate the separately
  confirmed unmanaged-service policy.

## Review isolation

The 2026-07-22 closeout replaced three existing reviews and created the UI row's first review.
Across the recorded windows:

- all existing review replacements retained their UUIDs and advanced `last_updated`;
- every Braindump body and `user_direct` authorship value remained unchanged;
- normalized DesiredSnapshot, ActualSnapshot, and observed-facts hashes were unchanged;
- normalized drift summary, severity summary, target identities/statuses, and sorted diff codes were
  unchanged (`converged: 4, unknown: 2`);
- the nctl operation-directory count remained `116`; and
- production inventory and dashboard modification times were unchanged.

Thus review prose had no desired-state, reconcile, inventory, Ansible, observation, ingest, or host
effect.

## Regression and repository checks

The strict closeout ran the current checked-out suites and tooling:

- nctl: `948 passed, 1 warning` (the existing Starlette/httpx warning);
- nintent: `98 passed`;
- nodeutils: `20 passed`, lock check and ruff clean;
- nauto: `14 passed` and Jobs compile cleanly; and
- both required Ansible playbooks pass syntax check, production inventory parses, and a live
  production-inventory ping to agdnsmasq succeeds with `changed: false`.

The parent and all submodule worktrees were clean before these documentation changes. Raw source
prose, full review prose, tokens, headers, managed file contents, and raw SSH keys remain outside
committed reports. Only IDs, timestamps, normalized results, and behavioral summaries are recorded.

## Friction decision

The live work exposed operational issues in inventory variable inheritance, SSH trust identity,
managed-file content observation, exact host scoping, and test completeness. Those issues were
fixed in their owning deterministic layers; none demonstrated a need for another Braindump field,
status, score, finding schema, review history, link table, scheduler, or embedded LLM runtime.

The UI-created row also required no special API path or background reviewer: ordinary UI storage,
GraphQL visibility, and one explicit nctl review write were sufficient.

## Remaining cluster work outside Phase 3

- Realize or intentionally disposition aghub.
- Refresh agstudio's stale actual state when a separately reviewed scoped operation is desired.
- Diagnose the pre-existing agdnsmasq `missing_actual_ip_address` / repeated-IPAM behavior without
  conflating it with dnsmasq content convergence.
- Remove or upgrade the two obsolete local nodeutils v1 dump files through a separately scoped
  maintenance action; the current reader correctly rejects them and reports the errors.

These findings remain visible but do not block the exchange-diary workflow or its safety boundary.

## Final scope statement

No live desired state, service configuration, SSH store, production inventory, dashboard, or host
was mutated during this strict-closeout continuation. The only live writes were the agent-owned
Alignment Review replacements/creation requested by the Phase 3 workflow. The earlier reversible
SSH/dnsmasq verification was independently planned, explicitly approved, fully observed, and
cleaned up.
