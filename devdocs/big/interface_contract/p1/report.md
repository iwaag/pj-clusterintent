# Phase 1 Final Report — Establish One Source-Controlled Desired Writer

Parent: [plan.md](plan.md). Per-step detail: [report0.md](report0.md)–[report8.md](report8.md)
(no separate report9.md — Step 9's documentation/search/commit work is recorded here).

## 1. Status

**Status: implemented, not deployed.** All 10 procedure steps (0–8, plus this Step 9 report)
executed, evidence-backed, one commit per step in both `nintent` and `nauto` plus a matching
superproject pointer-bump commit. Local test suites and a disposable Nautobot database prove the
full contract works. Per plan Section 8/10.3 and this initiative's explicit safety boundary,
**no live deployment, live Job run, or live desired-state mutation occurred** — the checked-in
YAML has not been applied to the live database, and the coordinated nintent/nauto commits have
not been pushed (pushing is explicitly the user's own step per `.local/localenv_memo.md`; Phase
4 owns the coordinated live rollout).

## 2. Evidence location

Private evidence: `.local/interface-contract/p1/20260725T134918Z/` (Step 0 boundary capture and
required-search snapshots) and `.local/interface-contract/p1/disposable/` (Step 8's compose
config, fixture scripts, and every extracted artifact JSON) — both directory mode `0700`, files
mode `0600`. No Braindump body, Alignment Review summary, token, or credential was written to any
tracked file or evidence file.

## 3. Repository revisions

| Repository | Start | End | Commits |
|---|---|---|---|
| superproject | `e18c983648d50ee3eaa3650fa596d9adefc6996d` | `a8ff037` (+ this report's commit) | 9 |
| `nintent` | `c343c5a56047b0df9ad901dd4459863ef1954053` | `185479d` | 7 |
| `nauto` | `251b056549f1b01f604b42b486fdc12d667db521` | `2635e64` | 3 |

`nctl`, `nodeutils`, and `ansible_agdev` submodule pointers are unchanged throughout (out of
scope, confirmed unmodified in Step 7).

## 4. Before/after summary

```text
before
  desired declarations split across home_cluster.yaml and intent_sources.yaml
  + confirmed live-only intent (agdnsmasq, aghub, Manual/dnsmasq) absent from source control
  + six stale nodes and their placement/override declarations still checked in
  + unknown YAML roots silently ignored
  + Import defaulted to apply and could disable omitted IntentSources
  + Import preview performed writes and relied on transaction rollback
  + Analyze wrote immediately, no versioned plan artifact
  + a separate Preview Intent Source Analysis Job
  + Seed Home Cluster wrote nintent IntentSource/DesiredService rows
  + Generate Desired Services produced a second desired-service proposal format
  + no intra-batch duplicate-identity detection for 4 of 9 YAML roots
  + Analyze crashed on any enabled URL-less (manual) IntentSource

after Phase 1
  one strict, reviewed nauto/seed/intent_sources.yaml document (9 declared roots)
  + one nintent Import Job: apply=false default, zero-write preview, atomic apply,
    post-commit confirmation, one intent-import-result.json / nintent.intent-import.v1 artifact
  + one nintent Analyze Job: apply=false default, zero-write preview, atomic apply constrained
    to analysis-owned fields, one intent-analysis-result.json / nintent.intent-analysis.v1 artifact
  + omission never disables, deletes, retires, or unlinks
  + no nintent desired-state writes in Seed Home Cluster
  + no Preview Intent Source Analysis Job
  + no Generate Desired Services Job or service_repositories seed/output contract
  + duplicate-identity detection closed for all 9 roots
  + Analyze runs cleanly against real data including a manual IntentSource
```

## 5. Job/file/test/root inventory

| Area | Before | After |
|---|---|---|
| nintent registered Jobs | `PreviewIntentSourceAnalysis`, `ImportIntentSources`, `AnalyzeIntentSources`, `ReconcileDesiredIPAMIntent` (4) | `ImportIntentSources`, `AnalyzeIntentSources`, `ReconcileDesiredIPAMIntent` (3) |
| nauto registered Jobs | `SeedHomeCluster`, `IngestNodeutilsInventory`, `AIResourceReview`, `GenerateDesiredServices` (4) | `SeedHomeCluster`, `IngestNodeutilsInventory`, `AIResourceReview` (3) |
| Import Job variables | `source_file`, `disable_missing`, `preview` | `source_file`, `apply` (default `false`) |
| Analyze Job variables | `fetch_timeout`, `include_disabled` | `fetch_timeout`, `include_disabled`, `apply` (default `false`) |
| Import artifact | `intent-import-preview.json` / `intent-import-apply.json`, ad hoc shape | `intent-import-result.json`, `nintent.intent-import.v1` |
| Analyze artifact | none (immediate writes, log-only summary) | `intent-analysis-result.json`, `nintent.intent-analysis.v1` |
| Checked-in YAML nodes | 9 (6 stale + 3 confirmed-shape) | 5 (`agbach`, `agdnsmasq`, `aghub`, `agpc`, `agstudio`) |
| Checked-in `desired_ip_ranges` | root absent | 3 (`dhcp-reserved`, `network-infra`, `dhcp-unreserved`) |
| Checked-in `desired_services` | 5 (Infrastructure only, in `home_cluster.yaml`) | 6 (5 Infrastructure + `dnsmasq`, all in `intent_sources.yaml`) |
| nintent local test count | 187 | 222 |
| nauto local test count | 110 | 110 (2 removed with `GenerateDesiredServices`, 2 added with the ownership test) |

## 6. Real defects found and fixed (Step 8)

Local Django-free unit tests cannot exercise the ORM-backed apply paths (Nautobot isn't
installed locally). Running the real Jobs against a live disposable database surfaced three
genuine defects invisible to the existing suite — see [report8.md](report8.md) §3 for full
detail:

1. A `.values()` field-list omission (`ip_range_rows` read `row["slug"]` without selecting it) —
   crashed the second Import once IP ranges existed.
2. Missing intra-batch duplicate-identity detection for 4 of 9 YAML roots (`intent_sources`,
   `desired_nodes`, `desired_endpoints`, `desired_ip_ranges`) — a document with a duplicate
   identity silently coalesced two planned `create` rows into one at apply time, a genuine
   preview/apply parity break. Closed for all 9 roots.
3. `urlparse(None)`'s silent bytes-mode fallback crashed Analyze's source-name/GitHub/GitLab
   helpers on any enabled URL-less (manual) `IntentSource` — live-reachable today via the
   confirmed "Manual" source. Every Analyze run against real current data would have failed
   before this fix.

All three have regression tests; the full local suite (222 + 110) is green with these fixes
applied.

## 7. Verification summary

- **Local tests**: 222 nintent tests `OK`, 110 nauto tests `OK`, `py_compile` clean on both.
- **Canonical YAML**: loads through the production loader with zero errors; exactly the
  confirmed Phase 0 identity set (2 intent sources, 5 nodes, 5 endpoints, 3 IP ranges, 0 compute
  rows, 6 services, 1 placement, 0 overrides).
- **Closed roots**: exactly nine roots accepted; both obsolete aliases and an arbitrary unknown
  root fail closed before any section is normalized.
- **Omission**: proven as a structural no-op for every root (never a disable/delete/retire/
  unlink) by both the pure planner tests and the live disposable proof.
- **Import**: default `apply=false` performs zero writes (verified by direct ORM query, not only
  the artifact's own claim); an existing node's lifecycle and every realized link/source survive
  re-import; a locked-field disagreement (`DesiredService` name/slug/display_name) blocks the
  whole row before any write; `apply=true` is one atomic, confirmed transaction; a forced
  persistence failure rolls back the entire transaction, not just the failing row; a repeat apply
  reports only `unchanged`.
- **Analyze**: default `apply=false` performs zero writes; source-owned fields update while every
  operator-owned field (`lifecycle`, `notes`, `requirements`, `resolution_status`, dependency
  `notes`) survives across repeat applies against identical fetched bytes; a malformed dependency
  blocks only its own service, not the rest of the batch; dependency deletion is gated behind
  per-service analysis completeness.
- **Artifacts**: one versioned shape per Job, deterministic object ordering, stable natural-key
  identities, no credential/secret in any field, truthful `writes`/`transaction`/`confirmation`
  state in every observed mode (preview, apply, blocked).
- **Seed Home Cluster**: statically proven (source-scan test) to import/reference/mutate no
  nintent desired model; `home_cluster.yaml` has no nintent desired root.
- **Generate Desired Services**: module, registration, test, seed file, output contract, and
  current documentation all confirmed absent.
- **Job discovery**: nintent 3 retained Jobs, nauto 3 retained Jobs — confirmed against a real
  Nautobot instance via the `GitRepository`/`provides: Jobs` mechanism nauto actually uses in
  production, not a stub.
- **Schema**: migrations remain through `0016`; `makemigrations --check --dry-run` clean both
  locally described and confirmed live in the disposable database, before and after every Step 8
  bugfix.
- **Isolation**: the disposable proof used a wholly separate Postgres/Redis/Nautobot compose
  stack (new network, volumes, containers, no port/host reference to the live stack), built from
  the exact local `nintent`/`nauto` working trees, then fully torn down (`docker compose down
  -v`), leaving no container, volume, or network behind.
- **Secrets/prose**: no token, credential, Braindump body, or Alignment Review summary in any
  tracked file, report, or evidence artifact.

## 8. Definition-of-done cross-check

Every item in plan.md Section 11 is satisfied within Phase 1's implementation scope: sole
checked-in bulk desired document with the exact confirmed identity set; no nintent desired root
in `home_cluster.yaml`; closed-root/omission-as-no-op behavior; Import/Analyze variable and
artifact contracts; ownership preservation and atomicity/confirmation/repeat-idempotence for
both Jobs; `Preview Intent Source Analysis` and `Generate Desired Services` absent with no alias;
IPAM/Ingest/AI Resource Review/GraphQL/REST/UI/nctl/migrations/live state unchanged; local tests,
strict searches, migration check, and disposable real-Job preview/apply/repeat proofs all pass;
no secrets in the report; no live deployment, Job run, or desired-state mutation occurred.

The overall `interface_contract` roadmap remains **not deployed** — Phase 1's own scope is
**complete**. Live YAML apply and the matched code deployment are Phase 4's explicit
responsibility, requiring separate maintenance-window approval, a database backup, and the
user's own `git push` of the coordinated `nintent`/`nauto` commits.

## 9. Next step

Phase 2 — contract REST and canonicalize confirmation reads (`devdocs/big/interface_contract/
roadmap.md`).
