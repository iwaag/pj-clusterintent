# state_bundle: file representation of desired/actual cluster state

## Goal

Define how "the cluster's desired/actual state as a file" is represented, so
a request like "stateをファイルにまとめて出力して" resolves to a well-defined
artifact instead of an improvised dump. Two layers:

1. **State bundle** — a zip of the existing versioned `--json` envelopes
   (`nctl.drift.v1`, `nctl.actual.v1`, `nctl.relations.v1`, …), one file per
   view, plus a small manifest. No new semantics; the bundle is a container.
2. **`nctl desired export`** — the one genuinely new capability: read the
   complete current desired state and emit it as a **canonical batch
   document**, the same YAML shape `nctl desired apply -f` accepts. Export
   is therefore a re-applyable, human-readable backup, and "export → apply
   preview reports no changes" is its built-in acceptance check.

Actual state is observed, not declared — it has no round-trip concept, so
the existing `nctl.actual.v1` envelope is already its file representation.

## Scope decisions (already made — do not relitigate)

- Reuse existing per-command envelopes as bundle payloads; do not invent a
  new mega-schema for state.
- Desired-state file format = the existing batch document shape. One format
  owner for both read and write; no second "export format".
- Bundling starts as a documented composition (commands + zip + `nctl
  upload` from the file_output plan, already present as
  `nctl/src/nctl_core/upload.py`). Promote to a `nctl bundle` command only
  if repetition proves painful (Easier Next Time policy) — not this phase.
- Experimental environment: success-path focus, minimal prohibitions,
  breaking changes allowed, no retention/cleanup design.

## Step 1 — `nctl desired export`

New `desired export` subcommand under the existing `desired_app` Typer group
(`nctl/src/nctl_core/cli/main.py`), core logic in a new module (suggestion:
`nctl/src/nctl_core/desired_export.py`), repo conventions as usual: CLI
stays thin, `--json` wraps the document in a versioned envelope (suggestion:
`nctl.desired.export.v1`), default output is the raw YAML document itself on
stdout so `nctl desired export > snapshot.yaml` just works.

Shape of the output: a Phase-0 batch envelope —

```yaml
dry_run: true
operations:
  - op: upsert
    kind: desired_node
    key: {slug: ...}
    values: {...}
  # one operation per existing desired row, every writable field explicit
```

Hints discovered while planning:

- The fetch side already exists: `nctl_core/sources/desired.py` pulls the
  complete desired graph in one pinned GraphQL round trip and already
  lowercases Nautobot's UPPERCASE choice-field names back to the batch
  vocabulary. Build the exporter on that snapshot; do not write a second
  desired-state query.
- The authoritative list of exportable kinds is whatever the batch writer
  (`nctl_core/desired_write.py` / `submit_batch`) accepts — enumerate it
  from that module, not from what GraphQL happens to return. If the fetch
  layer carries desired data that the batch endpoint cannot write
  (i.e. it cannot round-trip), fail the export naming that kind rather than
  silently dropping data. If that situation actually arises, it is a real
  contract gap to surface, not an export bug to paper over.
- Key shapes per kind (e.g. `{slug: ...}` for nodes,
  `{desired_node: ..., name: ..., endpoint_type: ...}` for endpoints) must
  match what `submit_batch` resolves — read them from the writer/README
  canonical examples, and emit `values` with every writable field explicit,
  since apply is a partial upsert and omitted fields would just be
  "preserved", masking an incomplete export.
- Determinism (README_DEV lesson 5): stable-sort operations by kind then
  key, and keep YAML key order fixed, so two exports of unchanged state are
  byte-identical. This makes diffing two snapshots meaningful for free.

Acceptance evidence:

- Unit tests against a fixture snapshot: known rows in → exact expected
  document out; unknown/unwritable kind → named failure; unchanged input →
  byte-identical output.
- Live round-trip: `nctl desired export > s.yaml && nctl desired apply -f
  s.yaml --json` (preview, no `--yes`) reports zero changes on the scratch
  Nautobot. This is the definitive check; record it in the report.

## Step 2 — bundle manifest + composition recipe

Define `nctl.bundle.v1` as a manifest convention and document the recipe;
no new nctl command this phase.

- `manifest.json` fields: `schema` (`nctl.bundle.v1`), `generated_at`,
  nctl git SHA (or version), and a `contents` list — one entry per file with
  `path`, `schema` (the envelope schema inside, or
  `nctl.desired.export.v1`), and that file's own `generated_at`.
- Canonical bundle layout:

  ```
  cluster-state-<UTC timestamp>.zip
  ├── manifest.json
  ├── desired.yaml     # nctl desired export
  ├── drift.json       # nctl drift --json
  ├── actual.json      # nctl actual --json
  └── relations.json   # nctl relations --json
  ```

- Views are fetched sequentially in one sitting, so they are close but not
  one atomic snapshot. That skew is acceptable here (experimental
  environment); the per-file `generated_at` in the manifest is the honest
  record of it. Do not build snapshot pinning for this.
- Write the recipe (the exact command sequence ending in `nctl upload
  --zip`, or zip-then-upload) into the place agents learn workflows from —
  alongside the nctl README command docs and whatever runbook surface
  cagent uses. The agent writes `manifest.json` itself from the commands'
  envelope headers; that is acceptable at composition stage, and chronic
  manifest mistakes are exactly the pain signal that would justify a future
  `nctl bundle` command.

Evidence: one bundle produced by following the written recipe verbatim,
unzipped and checked: manifest lists all four files with correct schemas.

## Step 3 — end-to-end through the cluster-agent

Send the original request ("desired state/actual stateを全てファイルに
まとめてダウンロードURLを示してください") through the cagent human
entrance and confirm the reply presents a working download URL whose zip
contains a valid `nctl.bundle.v1` bundle.

Evidence: request id + the downloaded bundle's manifest, noted in the phase
report.

## Out of scope (explicitly deferred)

- A `nctl bundle` command (only if composition proves painful).
- Snapshot-atomic multi-view fetch.
- Any actual-state round-trip or import.
- Retention, scheduling, or automatic periodic snapshots.
- Using `desired export` output as a disaster-recovery replacement for the
  PostgreSQL dumps in `.local/backups/` — it is a complement, not yet a
  validated recovery path.
