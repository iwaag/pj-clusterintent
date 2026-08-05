# Report — Step 4: verification

Status: complete (2026-08-06)

## Automated gate

`cd nctl && uv run pytest -q --durations=20` after all steps: **1255 passed**,
0 failed, 0 skipped.

## Live check (local scratch Nautobot, read-only)

The local stack from `.local/localenv_memo.md` was up, so
`uv run --project nctl nctl actual --json --detail` was run once from the
superproject root: exit 0, `schema: nctl.actual.v2`, `ok: true`,
`detail_level: raw`, 5 devices each carrying `facts_raw` with real nodeutils
sections (`hardware`, `gpu`, `memory`/`cpu`, `disk`, `network`, `services`,
`software`, …). Trimmed excerpt from the real device `agpc`:

```json
{
  "gpu": {
    "gpus": [
      {"name": "Quadro RTX 8000", "source": "nvidia-smi", "vendor": "NVIDIA",
       "memory_gb": 48.0, "driver_version": "590.48.01"},
      {"name": "Advanced Micro Devices, Inc. [AMD/ATI] Device 13c0",
       "source": "lspci", "vendor": "Advanced Micro Devices, Inc. [AMD/ATI]",
       "memory_gb": null}
    ],
    "count": 2, "detected": true, "memory_gb": 48.0
  },
  "memory": {"total_gb": 123.41},
  "cpu": {"model": "AMD Ryzen 9 9950X 16-Core Processor"},
  "services.docker.containers": [
    {"id": "e2d77d2b4e22", "name": "relaxed_montalcini", "state": "exited", "...": "..."}
  ]
}
```

Additional live checks:

- `nctl actual agpc --json --detail` → devices section scoped to exactly
  `["agpc"]`, `ok: true`.
- `nctl actual --json` (no `--detail`) → the `facts_raw` key serializes as
  JSON `null` per device (pydantic keeps the field), and no raw content (GPU
  models, container names, etc.) appears in the output — the purity contract
  is about content, which the automated tests also pin.
- `nctl actual nosuchhost --json` → exit 1 with the `unknown_host` envelope
  error, as designed in Step 1.

All commands were read-only against the persistent local scratch environment;
no cluster, desired-state, or external mutation occurred.

## Acceptance statement

A consumer can now obtain per-node detail beyond the basic facts via
`nctl actual --detail`, and a state bundle can carry it (optional
`actual_detail.json`, [state-bundle.md](../../../nctl/docs/state-bundle.md)).
