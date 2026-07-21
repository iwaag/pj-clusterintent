# Step 3.3 — Exercise a user-authored vague case and its visible unreviewed interval

Status: partially complete; UI-specific exit evidence is still required.

## 1. Completed diary behavior

- Braindump: `3049fd77-253a-4ca4-a062-864e34a303ac`
- Source: the user's directly supplied machine/placement source file.
- Before its first review, `nctl braindump create` returned `attention: unreviewed` and no review
  row. `nctl braindump review` then created exactly one current review.
- The review retains the conditional placement preference as prose and does not create a host ranking,
  placement score, or fixed desired service assignment.

## 2. Remaining required UI proof

The Phase 3 plan requires one Braindump entered through the Nautobot UI and observed through nctl as
unreviewed before the agent processes it. This interaction used the deterministic nctl file-input
path because the user supplied source files locally; it did not use the Nautobot add form.

Consequently, the normal unreviewed lifecycle is proven, but the UI-to-nctl visibility requirement
is not yet proven. A future direct UI entry must be left without a review long enough to observe
`review_present: false` / `attention: unreviewed`, then reviewed through nctl.

## Discrepancies

Do not mark Step 3.3's UI-specific exit criterion complete until that direct UI entry has occurred.
