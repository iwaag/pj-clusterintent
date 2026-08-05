# file_output: `nctl upload` — temporary download URLs for arbitrary files

## Goal

Give the cluster-agent (and any operator) one generic primitive:

```
nctl upload PATH [PATH...] [--zip] [--ttl DURATION] [--json]
```

Uploads the given file(s) to a local MinIO instance and prints a
time-limited presigned download URL. A request like "bundle the cluster's
desired/actual state into a file and give me a download URL" is then just a
composition: `nctl drift --json > state.json && nctl upload state.json`.
No state-specific export command is added.

## Scope decisions (already made — do not relitigate)

- Generic upload of arbitrary files, not limited to desired/actual state.
- MinIO runs locally via `devenv/nautobot/docker-compose.yml`; both "scratch"
  and "production" use this local setup for now. This is an experimental
  environment — no product-grade security hardening this phase.
- Success-path focus. Misupload guards (e.g. refusing `.local/secrets`) are a
  separate future session.
- No object deletion / lifecycle rules this phase. Files may accumulate.
- Breaking-change phase: no backward compatibility required anywhere.
- Do not reuse Nautobot's FileProxy machinery.

## Step 1 — MinIO in devenv

Add a `minio` service to `devenv/nautobot/docker-compose.yml`:

- Image `minio/minio`, command `server /data --console-address ":9001"`,
  ports `9000` (S3 API) and `9001` (console), a named volume for `/data`,
  root credentials via `devenv/.env` (`MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD`).
- One-shot init container (`minio/mc`, `restart: "no"`, same pattern as the
  existing `postgres-nautobot-init` service): wait for MinIO, create the
  bucket (suggestion: `nctl-outbox`), create a dedicated access key for nctl
  with readwrite policy on that bucket. Root credentials stay out of nctl.
- Keep the bucket private. The presigned URL is the only intended read path.

Hints:

- `mc admin user add` + `mc admin policy attach` is the simplest way to get a
  non-root key; a `mc admin user svcacct add`-style service account also
  works. Implementer's choice.
- Nothing else in the compose file depends on MinIO; do not add `depends_on`
  links to Nautobot.

Evidence: `docker compose --env-file ../.env up -d` from `devenv/nautobot/`
brings MinIO up; `mc ls` (or console at `:9001`) shows the bucket.

## Step 2 — `[storage]` config in nctl

Extend `nctl/src/nctl_core/config.py` with a `StorageConfig(StrictModel)`
section, following the existing `NautobotConfig` conventions:

```toml
[storage]
endpoint = "http://localhost:9000"   # also the host baked into presigned URLs
bucket = "nctl-outbox"
access_key = "nctl"
secret_key_file = "/Users/eiji/projects/pj-clusterintent/.local/minio-secret"
# secret_key_env = "NCTL_STORAGE_SECRET"   # alternative, mirroring token_env
default_ttl_minutes = 30
```

- Reuse the `token_file`/`token_env` resolution pattern (raw file content,
  whitespace-stripped; `extra="forbid"` so an inline secret key is rejected).
- Make the whole `[storage]` section optional; `nctl upload` without it fails
  with a clear ConfigError naming the section, everything else is unaffected.
- Update the sample `nctl.toml` at the repo root and drop the real secret in
  `.local/` (git-ignored) as usual.

Important gotcha — presigned URLs are signed over the host: the URL a
recipient uses must have exactly the host/port the signature was computed
against. You cannot sign against `localhost:9000` and hand the URL to a
machine that reaches MinIO as `agstudio.local:9000`. Keep one `endpoint`
value that is both the upload target and the advertised download host.

The right hostname cannot be auto-detected at runtime — only the operator
knows how recipients reach this machine — so it is deliberately a
self-declared nctl.toml value, same in nature as `[nautobot].url` (nctl.toml
is git-ignored, per-environment config; one value owns both roles so the
upload target and the advertised URL can never diverge). Choose it by
audience: `http://localhost:9000` suffices only if downloads happen on this
same machine; since cluster-agent requesters are typically on another
machine's browser, prefer a LAN-resolvable name like
`http://agstudio.local:9000` from the start. If split-horizon access
(localhost from inside, another name from outside) ever matters, add a
second `public_endpoint` used for signing — not needed this phase, just
don't design it out.

Evidence: config unit tests (present/absent section, secret resolution,
inline-secret rejection) pass in the nctl suite.

## Step 3 — upload core + CLI command

New module `nctl/src/nctl_core/upload.py` plus a thin Typer command in
`cli/main.py`, following the repo convention: the CLI parses args, core does
the work, a `render_*_text` function formats human output, `--json` emits a
versioned envelope (suggestion: `nctl.upload.v1`) via the existing
`nctl_core.output.emit` path.

Behavior:

- One PATH, no `--zip`: upload the file as-is.
- Multiple PATHs, or any PATH that is a directory, or explicit `--zip`:
  build a single zip (stdlib `zipfile`, temp file) and upload that. One
  invocation always yields exactly one download URL.
- Object key: prefix with a timestamp + short random suffix
  (e.g. `2026-08-05/143012-a1b2c3/state.json`) so repeated uploads never
  collide and accumulation stays browsable. No overwrite semantics needed.
- `--ttl` overrides `default_ttl_minutes`; keep parsing simple (integer
  minutes is fine; a duration string like `30m`/`2h` is a nice-to-have).
- Output: the presigned URL, expiry time, object key, and byte size. Human
  text should be phrased so the agent can relay it directly ("valid until…").

Dependency choice (implementer's discretion):

- `minio` Python SDK — small, purpose-built, `presigned_get_object` is one
  call. Probably the best fit.
- `boto3` — works, much heavier.
- Hand-rolled SigV4 over the existing `httpx` dependency — no new dependency
  but you own the signing math and its edge cases; only worth it if the SDKs
  are unacceptable for some reason.

Testing (nctl gate: `uv run pytest -q --durations=20` from `nctl/`):

- Unit-test zip/key/ttl logic and config plumbing with the store faked at a
  seam (inject a client or monkeypatch), matching how other modules fake
  Nautobot.
- One optional integration test against a real local MinIO is welcome but
  must skip cleanly when MinIO is not running — the ordinary nctl suite has
  "no expected skips" today, so if you add it, put it behind an explicit
  marker/env flag rather than an implicit skip, or park it under
  `devtests/`.

Evidence: with devenv MinIO up, `uv run --project nctl nctl upload
somefile --json` returns a URL that downloads correctly via `curl` and stops
working after expiry (spot-check with a short `--ttl`).

## Step 4 — teach the cluster-agent

- Add `nctl upload` to the surfaces the agent already learns nctl from
  (nctl README command list; cagent's `llms.txt` / prompt material if it
  enumerates capabilities there — check `cagent/src/cagent_api/` and
  `cagent/opencode/` config for where nctl usage is described).
- Document the composition pattern explicitly: write state with existing
  commands (`nctl drift --json`, `nctl relations --json`, …) into a temp
  file, then `nctl upload` it, then relay the URL + expiry to the requester.
- End-to-end check: send the original request ("desired/actual stateを
  ファイルにまとめてダウンロードURLを") through the cagent human entrance
  and confirm the reply contains a working presigned URL.

Evidence: transcript (request id) of the successful end-to-end run, noted in
the phase report.

## Out of scope (explicitly deferred)

- Object deletion, bucket lifecycle/ILM, quota — later session.
- Misupload/secret-leak guards — later session.
- Split-horizon `public_endpoint`, non-local storage backends, multi-bucket.
- Download-side nctl command (recipients use the URL directly).
