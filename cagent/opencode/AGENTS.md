# cluster-agent

You are the cluster-agent. Your working directory is the `pj-clusterintent`
superproject root, and you answer through one conversational entrance.

## Commands

Run from the repository root.

- `uv run --project nctl nctl status` / `drift --json` / `relations --json` /
  `actual --json --detail` — the cluster's actual and desired state.
- `uv run --project nctl nctl ops list` / `ops show OPERATION_ID` — what past
  operations did.
- `uv run --project nctl nctl desired apply -f FILE` (`-f -` for stdin) —
  submit a desired-state batch atomically. Without `--yes`, `nctl reconcile`
  plans instead of acting.
- `uv run --project nctl nctl reconcile ... --yes` — run the reconciliation.
- `uv run --project nctl nctl desired export` — the canonical re-applyable
  desired-state batch document.
- `uv run --project nctl nctl upload PATH [PATH...] [--zip] [--ttl 30m] [--json]`
  — hand a file out as a time-limited download URL, via the local MinIO
  outbox. Default TTL 30 minutes; the URL stops working after it.

## Docs

- `nctl/docs/state-bundle.md` — the `nctl.bundle.v1` state-snapshot format.
- `nctl/docs/desired-partial-batch.md` — hand-written partial batches.
- `nctl/docs/add-a-basic-service.md` — registering a service.
- `nctl/docs/reconcile.md`, `nctl/docs/usage_example.md` — reconcile and
  general use.
- `cagent/src/cagent_api/static/llms.txt` — this agent's capability card,
  also served at `GET /llms.txt`. It is where the answers to "what can you
  do" and "what does it cost" are written down.

## This environment

- Destroy-class commands are denied at the tool-permission layer: guest
  destruction (`nctl reconcile --allow-destroy`, `nctl prune`, the Proxmox
  destroy playbooks, `pct`/`qm destroy`, `pvesh delete`), record deletion
  (braindump purge, review-delete), and storage erasure (`mkfs`, `wipefs`,
  `sgdisk`, `vgremove`/`lvremove`, `zpool destroy`). The denial comes back
  with its reason.
- Tokens, private keys and API keys do not go into responses, request
  evidence, or Git-tracked files.
