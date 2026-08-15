# brainforge — agent manual

**brainforge** = talking with the user while keeping a Braindump (the user's
wish, free text) and its Alignment Review (your reply, free text) in sync via
`nctl`, and reaching real cluster state through `nctl` commands.

## What the four things are

| Thing | Where it lives | How it changes |
|---|---|---|
| Braindump | Nautobot, via `nctl braindump` | written from the user's own words (`authorship=user_direct` or `agent_transcribed`) |
| Alignment Review | Nautobot, one per Braindump | `nctl braindump review` replaces it; there is only ever one |
| Desired state (nintent) | Nautobot | `nctl desired apply` batches |
| Actual state (Nautobot/nodeutils) | Nautobot | observation only — nothing writes it directly |

Editing review text does not change drift, reconcile, or hosts; the review is
prose, not an input to actuation.

## Execution tools

- **SSH** — strong privileges, custom handling, error analysis.
- **Ansible** — deterministic setup/provisioning/config, actuated via
  `nctl reconcile`.
- **agent doors** — non-deterministic processing through an agent's own
  conversational entrance (cagent's window/human doors, an autolab node's
  gateway). `nctl agent`, the SSH-tunnelled node-local variant, was removed
  with the node-agent service it reached.

## Commands (`nctl braindump --help`, `nctl --help` for full options)

- `nctl braindump list [--json]` — `attention` flags unreviewed / stale.
- `nctl braindump show <id> [--json]`
- `nctl braindump create --title T --authorship user_direct|agent_transcribed (--body TEXT | --file PATH)`
- `nctl braindump review <id> (--summary TEXT | --file PATH)` — replaces the current review.
- `nctl braindump review-delete <id> [--yes]` — leaves the Braindump, marks it unreviewed.
- `nctl braindump complete <id> --reason TEXT [--yes]` — active → completed.
- `nctl braindump purge <id> [--yes]` — permanent deletion of a superseded or completed document; without `--yes` it is a read-only plan.
- `nctl drift [--host H] [--service S] [--json]` — desired vs actual, read-only.
- `nctl lifecycle <node-slug> <state> [--json]` — direct lifecycle setter (planned/approved/active/deprecated/retired); not part of reconcile.
- `nctl reconcile [host] [--yes] [--max-rounds N] [--json]` — without `--yes` a dry plan, with it an execution across up to `--max-rounds` rounds.
- `nctl session new brainforge [--topic WORD]` — creates this session's scratch folder and prints its path (`--json` for an envelope).

`body`/`summary` are opaque strings — natural language, not JSON, not scores.

Retiring a guest: `nctl/docs/add-and-retire-proxmox-lxc.md` and
`.claude/skills/retire-proxmox-lxc/SKILL.md` describe the sequence.

## Scratch area

`.local/workspace/brainforge/` — drafts, not the source of truth. Nothing reads
it back automatically; if it is not in Nautobot via `nctl`, it is not stored.
Keep secrets and raw tokens/SSH keys out of it.

```
.local/workspace/brainforge/
  <session-slug>/       # e.g. 2026-07-22_[4 random characters]
    sources/             # Braindump drafts before `nctl braindump create`
    reviews/             # Alignment Review drafts before `nctl braindump review`
    evidence/            # JSON snapshots pulled during this session
    human/               # resources for tasks only a human can do
  archive/               # old flat-layout sessions, moved here 2026-07-22
```

## Known gotchas

- One Braindump has at most one current review, and `review` always replaces —
  there is no history to reconstruct.
- nintent plugin changes need commit + user-initiated push + rebuild to take
  effect in the running Nautobot container; there is no hot reload.
- `deployment_profile: dnsmasq` on a `DesiredServicePlacement` that is not part
  of the managed dnsmasq DNS infrastructure makes `nctl reconcile` run an
  incompatible Ansible playbook, which fails with
  `ansible-playbook daemon setup apply exited with code 2`.
- An observed service with no matching Braindump or desired entry is not
  evidence that it is unwanted; `unmanaged-services-review.txt` in the
  workspace `reviews/` dir may already record a general policy for these.
