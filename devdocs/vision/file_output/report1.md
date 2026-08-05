# Step 1 report — MinIO in devenv

Status: **complete**

## What was done

- Added a `minio` service and a one-shot `minio-init` service (image `minio/mc`,
  `restart: "no"`, same pattern as `postgres-nautobot-init`) to
  `devenv/nautobot/docker-compose.yml`, plus a named `minio_data` volume.
- Added `devenv/nautobot/nctl_outbox_policy.json`: a readwrite policy scoped to
  the `nctl-outbox` bucket only (`ListBucket`/`GetBucketLocation` on the bucket,
  `Put/Get/DeleteObject` on its objects).
- `minio-init` waits for MinIO, creates bucket `nctl-outbox`
  (`mc mb --ignore-existing`), creates policy `nctl-outbox-rw`, creates the
  dedicated `nctl` user (idempotent: skipped when the user already exists),
  attaches the policy, then positively verifies by listing the bucket **with the
  nctl user's own credentials**. Root credentials stay out of nctl.
- Credentials: `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD` were already present in
  `devenv/.env`. Generated a 40-char random secret for the `nctl` user, stored
  as raw content in git-ignored `.local/minio-secret` (mode 600) and as
  `NCTL_MINIO_SECRET_KEY` in `devenv/.env` (consumed only by `minio-init`).
- No `depends_on` links from Nautobot services to MinIO, per plan.

## Deviation from plan: host ports

Host ports 9000/9001 were already taken on this machine (9000 → `portainer`,
9001 → the unrelated `service_scripts` MinIO `my_minio`). The devenv MinIO is
therefore published on **9100 (S3 API)** and **9101 (console)**. Container-side
ports are unchanged. Step 2's `[storage].endpoint` will use port 9100.

## Incident during execution (resolved)

First `minio-init` run failed with "secret key is invalid": `devenv/.env` had no
trailing newline, so the appended `NCTL_MINIO_SECRET_KEY=` line was concatenated
onto the `GITHUB_TOKEN` line and the variable resolved empty. Fixed by splitting
the line in place (values never displayed), re-ran `minio-init`, exit 0.
Side effect check: `GITHUB_TOKEN` line restored byte-identically; secret values
were never printed to the transcript.

## Evidence

- `docker compose --env-file ../.env up -d minio minio-init` from
  `devenv/nautobot/` brings both up.
- `nautobot-minio-init-1` final run exit code **0**, log shows:
  `Bucket created successfully local/nctl-outbox`, `Created policy nctl-outbox-rw`,
  `Added user nctl`, `Attached Policies: [nctl-outbox-rw] To User: nctl`, and a
  successful `mc ls` as the nctl user.
- Host reachability: `curl http://localhost:9100/minio/health/ready` → 200.
- Bucket privacy: anonymous `GET /nctl-outbox` → `AccessDenied` (presigned URL
  remains the only intended read path).
