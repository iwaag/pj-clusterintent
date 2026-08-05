# Step 2 report — `[storage]` config in nctl

Status: **complete**

## What was done

- `nctl/src/nctl_core/config.py`: added `StorageConfig(StrictModel)` with
  `endpoint`, `bucket`, `access_key`, `secret_key_env` (default
  `NCTL_STORAGE_SECRET`), optional `secret_key_file`, and
  `default_ttl_minutes` (default 30, bounded 1–10080). `extra="forbid"` from
  `StrictModel` rejects an inline `secret_key`.
- Secret resolution mirrors `NautobotConfig.resolve_token`: raw file content,
  whitespace-stripped; file beats env. One improvement over the plan sketch: a
  relative `secret_key_file` resolves against the loaded `nctl.toml`'s
  directory via the existing `resolve_local_path` owner (same contract as the
  `[ssh]` paths), not the process cwd. Convenience accessor
  `Config.resolved_storage_secret_key()`.
- `Config.storage` is `StorageConfig | None = None` — the whole section is
  optional and nothing else is affected. `Config.require_storage()` raises a
  `ConfigInvalidError` naming the `[storage]` section and its keys; `nctl
  upload` (Step 3) will use it.
- `nctl/example.nctl.toml` (the tracked sample): documented `[storage]`
  section, including the endpoint-is-signed-into-URLs gotcha.
- Root `nctl.toml` (git-ignored live config): added `[storage]` with
  `endpoint = "http://agstudio.local:9100"` (LAN-resolvable name per plan;
  port 9100 per the Step 1 port deviation), `bucket = "nctl-outbox"`,
  `access_key = "nctl"`, `secret_key_file = ".local/minio-secret"` (created in
  Step 1).

## Evidence

- New unit tests in `nctl/tests/test_config.py` (Tier B parameter cases):
  section absent → `storage is None` and `require_storage()` raises naming
  `[storage]`; section present with defaults; secret from env; secret file
  beats env; relative `secret_key_file` resolves against the config directory
  regardless of cwd; missing secret file raises naming `secret_key_file`;
  inline `secret_key` rejected; TTL bounds (0 and 10081) rejected.
- `uv run pytest -q tests/test_config.py` from `nctl/`: **33 passed**.
- Full nctl gate `uv run pytest -q --durations=20` from `nctl/`:
  **1204 passed** (no skips), so the optional section leaves the rest of the
  suite untouched.
