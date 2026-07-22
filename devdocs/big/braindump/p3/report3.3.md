# Step 3.3 — Exercise a user-authored vague case and its visible unreviewed interval

Status: complete, including the direct Nautobot UI follow-up on 2026-07-22.

## 1. Dynamic/vague diary behavior

- Braindump: `3049fd77-253a-4ca4-a062-864e34a303ac`
- Source: the user's directly supplied machine/placement source file.
- Before its first review, `nctl braindump create` returned `attention: unreviewed` and no review
  row. `nctl braindump review` then created exactly one current review.
- The review retains the conditional placement preference as prose and does not create a host
  ranking, placement score, or fixed desired service assignment.
- The 2026-07-22 replacement review still leaves Ollama/Qwen and workload placement unstructured
  until the user supplies availability, model/update, network, persistence, profile-ownership, and
  fixed-versus-dynamic placement decisions.

## 2. Direct UI-to-nctl proof

The user created a separate validation Braindump through the Nautobot add form.

- Braindump: `45255668-b0c4-456f-9d6c-a9fc0f611da1`
- Title: `test`
- Authorship: `user_direct`
- Created: `2026-07-22T09:35:28.555603Z`

Before any agent review write, authenticated `nctl braindump list/show --json` observed:

- total Braindump count `5`;
- `review_present: false`;
- `attention: unreviewed`; and
- `alignment_review: null`.

This proves that the UI-created row was immediately visible through the supported nctl GraphQL read
path and that no placeholder, signal, scheduler, or background worker filled its review.

After reading all current diary rows, desired/actual state, current drift, and a bounded read-only
network check relevant to the user's test statement, the agent created one current review through
nctl. The result was `action: created`, review
`550591e9-c18d-4fa3-a67b-55c8e3dc5f1c`; the Braindump body and `user_direct` authorship remained
unchanged.

The UI row is the transport/lifecycle acceptance proof; the earlier machine-placement row remains
the dynamic/vague semantic case. These are separate pieces of evidence and are not represented as
though the UI validation body itself contained the earlier private placement prose.

## 3. Isolation

Across the review-creation window:

- normalized desired, actual, and observed snapshot hashes were unchanged;
- normalized drift remained `converged: 4, unknown: 2` with identical target statuses and codes;
- the nctl operation-directory count remained `116`;
- production inventory and dashboard modification times were unchanged; and
- no reconcile, Ansible, nodeutils, Nautobot Job, or host action was triggered.

## Discrepancies

None. Both the dynamic/vague behavior and the formerly missing direct UI-entry interval now have
live evidence.
