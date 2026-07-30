# brainforge — agent manual

**brainforge** = the process where you (the AI agent) talk with the user, keep a Braindump
(user's wish, free text) and its Alignment Review (your reply, free text) in sync via `nctl`, and
only ever touch real cluster state through separately confirmed, deterministic nctl commands.

# rule

- read nctl/docs/usage_example.md
- When you get requests from user, first you must show plan to how to do it using nctl before actually performing it. If it's not possible by using only nctl, you need to explain what necessary fanctionality is lacking in nctl.

## The four things you're allowed to touch, and how

| Thing | You may... | You may NOT |
|---|---|---|
| Braindump (user's words) | read it; write it only when transcribing words the user actually said (`authorship=agent_transcribed`) | invent a wish and store it as Braindump |
| Alignment Review (your words) | write/replace it any time to reflect current understanding | let it drive reconcile/actuation directly |
| Desired state (nintent) | propose changes; write them only after explicit user confirmation | change it because a review "implies" it |
| Actual state (Nautobot/nodeutils) | read it (`nctl drift`, `nctl status`) | write it directly (it comes only from observation) |

Editing review text can **never** change drift, reconcile, or hosts. If you ever think it did,
something is wrong — stop and tell the user.

## Workspace scratch area

`.local/workspace/brainforge/` is your scratch space, not the source of truth. **It is isolated
per session**, so a new session never reads a previous session's drafts:

```
.local/workspace/brainforge/
  <session-slug>/       # e.g. 2026-07-22_[radom 4 characters] — pick one at the start of a session
    sources/             # drafts of Braindump text before `nctl braindump create`
    reviews/             # drafts of Alignment Review text before `nctl braindump review`
    evidence/            # JSON snapshots pulled during this session, for reference/audit
    human/               # helpful resources for tasks which only can be done by humans.
  archive/               # old flat-layout sessions moved here 2026-07-22; not read by agents
```

Start of session: run `nctl session new brainforge [--topic WORD]` to create your session folder —
don't hand-pick a slug yourself (agents were doing this inconsistently). It prints the new folder's
path (or a JSON envelope with `--json`); create `sources/`, `reviews/`, `evidence/` subfolders
lazily as you actually need them — don't pre-create empty ones. Never read or reuse another
session's slug folder; if you need something from a prior session, ask the user or read it back
from Nautobot via `nctl`, not from another session's directory.

Files here are never read back automatically by anything. If it's not in Nautobot via nctl, it
doesn't count as stored. Don't put secrets or raw tokens/SSH keys in this workspace.

## Standard loop for one turn

1. `nctl braindump list --json` — see what exists, check `attention` (unreviewed / stale).
2. `nctl braindump show <id> --json` — read the specific Braindump + its current review.
3. `nctl drift --json` (optionally `--host`/`--service`) — see current desired-vs-actual.
4. Talk with the user. Update the Braindump only if they gave you new/changed words to store.
5. Write your understanding as a new Alignment Review (replaces the old one, there is only ever one).
6. If a structured change is needed (a new desired node/service/lifecycle), propose it in plain
   words and get explicit yes/no before writing anything. Never batch multiple structural changes
   into a single unreviewed confirmation.
7. If approved, make the change through the normal nintent/nctl path (not by editing the review),
   then re-run `nctl drift` / re-observe, and only then update the Alignment Review to describe
   the new result.

## Key commands (see `nctl braindump --help`, `nctl --help` for full options)

- `nctl braindump list [--json]`
- `nctl braindump show <id> [--json]`
- `nctl braindump create --title T --authorship user_direct|agent_transcribed (--body TEXT | --file PATH)`
- `nctl braindump review <id> (--summary TEXT | --file PATH)` — replaces the current review
- `nctl braindump review-delete <id> [--yes]` — leaves Braindump, marks it unreviewed
- `nctl braindump purge <id> [--yes]` — only for a superseded document the user has explicitly
  said is no longer useful; without `--yes` this is a read-only plan
- `nctl drift [--host H] [--service S] [--json]` — desired vs actual, read-only
- `nctl lifecycle <node-slug> <state> [--json]` — direct lifecycle setter (planned/approved/active/deprecated/retired), not part of reconcile
- `nctl reconcile [host] [--yes] [--max-rounds N] [--json]` — without `--yes` it's a dry plan only; `--yes` actually executes. Never pass `--yes` without the user having approved the specific plan.
- Retirement may use a desired-state batch draft in this session's scratch area, but that draft is never a source of truth: preview the two partial upserts for `DesiredNode.lifecycle: retired` and `DesiredComputeInstance.desired_presence: absent`, then apply that exact reviewed batch only after approval. Run `nctl reconcile GUEST --allow-destroy --json` and review `data.plan.actions` for its one pinned `destroy_compute_instance` action (guest slug, VMID, and control node). Only then may the separately approved `--allow-destroy --yes` run proceed. Success is fresh `compute_instance_removal_complete` drift evidence with reconcile `state: converged`; afterward use the separate `nctl prune GUEST` preview before any prune apply.

`body`/`summary` are opaque strings — write natural language, not JSON, not scores, not status codes.

## When to stop and ask instead of deciding

You are meant to run on a cheap/local model too. Do not try to be clever here — escalate to the
user instead of guessing when:

- The wish is ambiguous and a wrong guess would change desired state (ask a clarifying question,
  don't pick an interpretation).
- A structural/desired-state change is implied — always get explicit confirmation first, no
  exceptions, even for "obviously fine" changes.
- An actual/observed service has no matching Braindump or desired entry — do NOT mark it unwanted.
  Describe it neutrally, ask whether it's intentional, and offer to record a Braindump for it.
  (See existing precedent in `unmanaged-services-review.txt` in the workspace reviews/ dir — the
  user may already have set a general policy on this.)
- `nctl reconcile` or an Ansible/SSH action hits a real error (trust/config/host unreachable) —
  report the exact error to the user; do not retry with weakened checks, and do not disable
  verification to get past it.
- You're not sure whether something already has a Braindump/review — list first, don't create a
  duplicate.

## Known gotchas

- One Braindump has at most one current review; `nctl braindump review` always replaces, never
  appends. There is no history — don't try to reconstruct "what the review used to say."
- Before requesting `purge`, show the superseded document and ask whether any part remains useful
  to current cluster operation. If a transient detail is still useful, transcribe it into the
  current operational-context Braindump with its reason and removal condition instead. Purge only
  after the user says the old document itself is no longer useful.
- `reconcile --yes` actually executes across up to `--max-rounds` rounds; always show the user
  the dry-plan (no `--yes`) result first for anything non-trivial.
- nintent plugin changes require commit + user-initiated push + rebuild to take effect in the
  running Nautobot container (no hot reload). Don't expect a nintent code change to show up
  without that cycle.
