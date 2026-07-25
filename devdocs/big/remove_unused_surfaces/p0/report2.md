# Phase 0 Step 2 — Record the live read-only baseline

Parent: [plan.md](plan.md), Step 2.

All commands below are read-only: `nautobot-server --version`, `showmigrations`,
`makemigrations --check --dry-run`, `pip show`, a `direct_url.json` read, one `nbshell` session
running only `.count()`/`.values().annotate()` aggregations and read attribute access, and one
local `Config.load()` plus `Path.exists()`/directory listing. No row was written, no migration was
opened, no dashboard/serve command ran.

## Versions

| Item | Value |
|---|---|
| Nautobot | 3.1.3 |
| Django | 5.2.14 |
| `nautobot-intent-catalog` distribution | 0.9.0 |
| `nautobot-intent-catalog` installed commit (`direct_url.json`) | `ad9d36397d23c269ad748e13acbccc532fa29f52` |

The installed commit differs from the local `nintent` submodule HEAD
(`ad0c6424141cea62bf731288ed1f0ca0df4e4711`, report1.md). This is the expected and normal state of
the nintent deployment flow recorded in `.local/localenv_memo.md`: the running container is built
from a previously pushed revision and only advances on the next coordinated
commit→push→rebuild→migrate cycle. It is not unexpected live drift and is not the "live state
advanced past `0014`" stop condition in Step 2's gate.

## Migration state

```text
$ nautobot-server showmigrations nautobot_intent_catalog
 [X] 0001_initial
 ... (0002 through 0014, all [X])
 [X] 0014_braindump_exchange_diary
```

`0015`/`0016` do not appear — live is exactly on `0014`, matching plan §2.1's expectation and
`report1.md`'s local migration-file check.

```text
$ nautobot-server makemigrations nautobot_intent_catalog --check --dry-run
No changes detected in app 'nautobot_intent_catalog'
(exit 0)
```

## Running Job count

`JobResult.objects.filter(status__in=["PENDING", "RUNNING"]).count()` → **0**. No IDs to record.

## Cache aggregates

```text
DesiredNode.objects.values("reconciliation_status").annotate(count=Count("id"))
  {'reconciliation_status': 'converged', 'count': 5}
DesiredNode total: 5 rows (no blank/null bucket present — every row already has a status)

DesiredService.objects.values("reconciliation_status").annotate(count=Count("id"))
  {'reconciliation_status': '', 'count': 5}
  {'reconciliation_status': 'converged', 'count': 1}
DesiredService total: 6 rows

DesiredNode.reconciliation_checked_at non-null: 5 / 5
DesiredService.reconciliation_checked_at non-null: 1 / 6
```

These are the aggregation queries the removal migration (`0016`) will need to reason about: all
five `DesiredNode` rows and one `DesiredService` row currently carry non-null dashboard-derived
cache data that migration `0016` will drop without translation, per plan §4.7.

## Generated dashboard directory

`Config.load().dashboard.resolved_out_dir()` → `/Users/eiji/.local/state/nctl/dashboard`
(exists). Contents by name/size only (not read): `drift.json` (1106 bytes), `index.html` (13905
bytes). This path is outside the repository tree (no in-repo `.gitignore` entry is needed or
expected for it).

`cfg.dashboard.url` → `None`. No local `nctl.toml` exists at the repo root (confirmed in
`report0.md`), so there is no active deployment `dashboard_url` value to record beyond this
"unconfigured" state; `example.nctl.toml`'s `url` key is commented out.

## Gate

Live package commit, migration state, running-Job count, cache aggregates, and the generated
dashboard path are all current as of this step and were captured without changing any of them.
