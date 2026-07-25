# Step 1 — Implement shared pure contracts and prove database mechanisms

Status: `complete`.

Raw evidence: `.local/vm-p3/20260725-step1/` (private, mode 0700/0600).

## 1. Django-free pure contract module

Added `nintent/nautobot_intent_catalog/compute_contract.py`, following the existing
`intent_contract.py` pattern (`ComputeContractError(code, message, path)`, pure functions, no
Django import). It implements:

- `validate_provider_type` — only `"proxmox"` accepted.
- `validate_config_schema_version` — omitted (`None`) input normalizes to `"v1"`; any other
  explicit value is rejected.
- `validate_platform_config` — closed key set `{cluster_name, default_storage, default_bridge}`,
  all optional, stripped non-empty strings, max length 255, unknown keys/non-object/wrong types
  rejected.
- `validate_instance_config` — closed key set `{vmid, template, storage, bridge, unprivileged}`;
  `template` required (non-empty, max 512); `unprivileged` required boolean for `container`,
  forbidden for `virtual_machine`; kind-aware in one shared function.
- `validate_vmid`, `validate_vcpus`, `validate_memory_mb`, `validate_root_disk_gb` — exact Section
  5.2/5.3 bounds (`vcpus` 1..8192, `memory_mb` 16..2147483647, `root_disk_gb` 1..2147483647,
  `vmid` 100..999999999), boolean-as-int rejected.
- `normalize_mac_address` — colon/hyphen six-octet input to canonical lower-case colon form;
  `None`/empty -> `None`; dotted/short/overlong/mixed-separator/non-hex/list/numeric/boolean
  rejected.
- `effective_lifecycle` — the exact Section 5.4 precedence table (retired > deprecated > planned >
  both-active=active > else approved), plus `is_actionable_lifecycle`.
- `effective_value` / `effective_single_source_value` — instance-override-then-platform-default
  provenance for storage/bridge, and single-source provenance for `cluster_name`/`vmid`.

## 2. Pure tests

Added `nintent/nautobot_intent_catalog/tests/test_compute_contract.py`: 56 tests covering every
valid/invalid key, wrong scalar type, boundary and adjacent-invalid numeric value, every MAC
normalization/rejection class, every lifecycle-pair combination (including precedence ties), and
every effective-value provenance path.

```
$ python3 -m unittest discover -s nautobot_intent_catalog/tests
Ran 167 tests in 0.018s
OK
```

(167 = the full existing Django-free suite plus the 56 new tests; no regression.)

## 3. Platform+JSON-VMID uniqueness constraint spike (real PostgreSQL 15.17)

Ran a disposable, fully-rolled-back transaction directly against `my_postgres_db` (`nautobot`
database) creating table `zz_p3_step1_spike` with:

- `CHECK (NOT (config ? 'vmid') OR ((config->>'vmid')::bigint BETWEEN 100 AND 999999999))`
- `UNIQUE INDEX ... (platform_id, ((config->>'vmid')::bigint)) WHERE (config ? 'vmid')`

Results (`spike_full.log`):

| Case | VMID | Platform | Expected | Result |
|---|---|---|---|---|
| min bound | 100 | A | pass | `INSERT 0 1` |
| max bound | 999999999 | A | pass | `INSERT 0 1` |
| same VMID, second platform | 100 | B | pass | `INSERT 0 1` |
| below bound | 99 | C | fail | `ERROR: ... violates check constraint "zz_vmid_range_ck"` |
| above bound | 1000000000 | C | fail | `ERROR: ... violates check constraint "zz_vmid_range_ck"` |
| duplicate same-platform VMID | 100 | A (again) | fail | `ERROR: ... violates unique constraint "zz_p3_step1_platform_vmid_uq"` |

Final positive row count: 5 (matches the three pass cases above plus two `vmid`-omitted rows,
which the partial index correctly leaves unconstrained). The whole spike ran inside one
transaction that ended in `ROLLBACK`; `SELECT to_regclass('zz_p3_step1_spike')` afterward returned
`NULL`, and a live `\dt zz_*` check post-session shows no matching relation — the disposable table
left no trace.

## 4. ORM constraint generation and migration serialization

Built the same constraint through Django's ORM (`nautobot-server shell`, unmanaged throwaway model,
never migrated):

```python
models.UniqueConstraint(
    "platform_id",
    Cast(KeyTextTransform("vmid", "config"), output_field=models.BigIntegerField()),
    name="...", condition=models.Q(config__has_key="vmid"),
)
```

`constraint.create_sql(...)` produced exactly the manually-verified SQL:

```sql
CREATE UNIQUE INDEX "..." ON "..." ("platform_id", ((("config" ->> 'vmid'))::bigint))
WHERE "config" ? 'vmid'
```

`MigrationWriter.serialize(constraint)` round-trips cleanly to
`models.UniqueConstraint(models.F('platform_id'), django.db.models.functions.comparison.Cast(...), condition=models.Q(...), name=...)`
with resolvable imports (`django.db.models.fields.json`, `django.db.models.functions.comparison`).

**Decision**: the ORM *can* generate the exact expression constraint, so Step 2 uses the standard
`models.UniqueConstraint(...)` mechanism rather than a hand-written reversible-migration SQL
fallback. This also means `DesiredComputeInstance.config` stays the sole VMID store — no
duplicate/shadow VMID field is needed.

## 5. Proxmox 9 provider bounds source

The `100..999999999` VMID bound is documented in the Proxmox VE Administration Guide (the same
range appears unchanged across the Proxmox 5–9 release lines, including the installed
`pve-manager 9.1.1`): a VMID "has to be a number between 100 and 999999999." This is the value
already adopted by the plan's Section 5.3 and the Step 1 pure validator/DB bounds above; it was
**not** derived from the live VMID range 100–108 currently in use on `aghub`, which only exercises
the low end of the documented range.

## Gate

The reviewed constraint implementation — Django `UniqueConstraint` with `Cast(KeyTextTransform(...))`
and a `has_key` partial condition — is selected, proven reversible (ran inside a rolled-back
transaction with no persisted trace), and matches the exact SQL a real migration will emit, before
the Step 2 model migration is authored.

Proceeding to Step 2.
