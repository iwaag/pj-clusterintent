# Phase 0 Step 0.1 — Confirm vocabulary and ownership

Parent: [plan.md](plan.md), Step 0.1.

## Check performed

Compared the Step 0.1 vocabulary/ownership table in `plan.md` against `../roadmap.md`'s "Core
boundaries" table and "Two deliberately separate comparisons" section, term by term.

| Term | plan.md Step 0.1 | roadmap.md | Match |
|---|---|---|---|
| Braindump | Current user-originated prose; writer = user or agent transcribing confirmed words; runtime authority = context only | User-originated free-form text; preserves wishes/constraints/preferences/uncertainty | yes |
| Alignment Review | Current AI reply grounded in current cluster evidence; writer = AI agent; runtime authority = communication only | AI-authored free-form text; explains current relationship, continues conversation | yes |
| Desired state | Structured executable commitment; writer = existing nintent/nctl write paths; runtime authority = reconcile input | Structured nintent/Nautobot data; the executable commitment consumed by deterministic workflows | yes |
| Actual state | Latest observation/ledger facts; writer = nodeutils/nauto/Nautobot paths; runtime authority = drift input | Nautobot plus nodeutils observations; latest observed cluster state | yes |
| Convergence drift | Deterministic desired-versus-actual comparison; writer = nctl; runtime authority = reconcile input | Existing deterministic desired-versus-actual result; `nctl drift` is its single source of truth; `nctl reconcile` may act from it | yes |

No terminology or ownership conflict found between the two documents.

## "Alignment" is not a persisted boolean

Confirmed by re-reading both documents: neither the roadmap's "Minimal data contract" section nor
the plan's `AlignmentReview` section (Step 1 of the "Authoritative minimal contract") adds a status,
score, or boolean field. `AlignmentReview.summary` is the only content field; freshness is judged
from `last_updated` comparison (Step 0.4 of this plan), never from a stored alignment verdict. An
Alignment Review is prose, not a second drift engine — `nctl drift` remains the sole deterministic
comparison (see Step 0.3's explicit exclusion of Braindumps from `SourceSnapshot`, drift
comparators, and reconcile classification).

## Result

Vocabulary and ownership are frozen with no discrepancy between `plan.md` and `roadmap.md`. No edit
to either document was required.
