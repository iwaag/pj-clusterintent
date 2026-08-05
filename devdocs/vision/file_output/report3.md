# Step 3 report — upload core + CLI command

Status: **complete**

## What was done

- New module `nctl/src/nctl_core/upload.py`:
  - `run_upload(cfg, paths, *, zip_requested, ttl, store, now)` — core logic:
    one regular file uploads as-is; multiple paths, any directory, or `--zip`
    build a single zip (stdlib `zipfile`, temp dir); exactly one object and one
    URL per invocation. Object keys are
    `YYYY-MM-DD/HHMMSS-<6hex>/<name>` so repeated uploads never collide and
    accumulation stays browsable by date. Zip naming: `<stem>.zip` for one
    path, `bundle.zip` for several; directories are archived recursively under
    their own name prefix with sorted member order.
  - `parse_ttl_minutes` — integer minutes plus the `30m`/`2h` nice-to-have,
    bounded 1..10080 (7 days, matching the config bound).
  - `ObjectStore` protocol seam (`put_file`/`presign_get`) with `MinioStore`
    over the **minio SDK** (the plan's suggested dependency; added
    `minio>=7.2` to `nctl/pyproject.toml`). `make_store(cfg)` resolves
    `[storage]` + secret and raises a `ConfigError` naming what is missing.
  - `build_upload` wraps the result in a versioned `nctl.upload.v1` envelope
    via the existing `nctl_core.output` path; `render_upload_text` phrases the
    human output for direct relay ("download URL (valid until …, N min)").
- CLI: `nctl upload PATH... [--zip] [--ttl] [--json]` in `cli/main.py`,
  following the repo convention (CLI parses, core works, `emit` renders).
  Missing `[storage]`/secret → usage error (exit 2) naming the section;
  `missing_path`/`invalid_ttl` → exit 2; store failures → error envelope,
  exit 1.
- `tests/test_cli_surface.py`'s retained-command set gained `upload` (the
  test exists precisely to catch surface changes; this one is intentional).
- Documented the command and the composition pattern (`nctl drift --json >
  f && nctl upload f`) in `nctl/README.md` (usage block + `### upload`
  section, including the endpoint/signing caveat and no-lifecycle note).

## Testing

- `nctl/tests/test_upload.py` — store faked at the `ObjectStore` seam
  (matching how other modules fake Nautobot): TTL parse parameter tables
  (accept/reject, bounds); single-file as-is upload with key format, size,
  default TTL, expiry math; key collision-freedom; `--ttl` override; explicit
  zip of one file; multi-path bundle (zip contents asserted by round-trip);
  recursive directory zip with prefix; missing path reported before any
  upload; store failure → `upload_failed` envelope with no presign after a
  failed put; missing `[storage]`/secret ConfigError messages; envelope/text
  rendering.
- `nctl/tests/test_cli_upload.py` — arg passthrough, `--json` envelope,
  usage-vs-failure exit codes.
- No integration test was added to the ordinary suite (it has a no-expected-
  skips contract); live MinIO was exercised manually below.
- Gates: `uv run pytest -q --durations=20` from `nctl/`: **1235 passed**, no
  skips (31 of them the new upload tests).

## Live evidence (devenv MinIO, endpoint http://agstudio.local:9100)

- `uv run --project nctl nctl upload sample.json --ttl 2 --json` → ok
  envelope, object key `2026-08-05/040628-475def/sample.json`, 30 bytes,
  `expires_at` 2 minutes out.
- `curl` of the presigned URL returned the exact uploaded content.
- Multi-file human-text run (`nctl upload example.nctl.toml README.md --ttl
  30m`) → `bundle.zip` URL; downloading and `unzip -l` listed exactly the two
  source files.
- After the 2-minute TTL elapsed, the same URL returned **HTTP 403
  `AccessDenied: Request has expired`** — expiry enforced.
