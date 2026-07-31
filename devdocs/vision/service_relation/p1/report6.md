# Step 6 Report — Deploy to Local Nautobot

Status: complete.

## Push

User pushed both submodules before this step ran. Verified against the
remote:

- `nintent`: local `HEAD` and `origin/main` both at `f30a786be431541ecc40c8bdf415a8a52f83e761`.
- `ansible_agdev`: local `HEAD` and `origin/main` both at `abbd5b42fff3492dcd8e932c1fa41a3e99d4abe3`.

## Rebuild

`docker compose --env-file ../.env build --no-cache` from `devenv/nautobot/`.
Build log shows `pip install git+https://github.com/iwaag/nintent.git@main`
resolving to commit `f30a786be431541ecc40c8bdf415a8a52f83e761` — matches the
pushed nintent `HEAD` exactly, confirming the image is not using a cached
stale commit (the known gotcha from `.local/localenv_memo.md`).

## Restart + migrate

- `docker compose --env-file ../.env up -d`: `nautobot-nautobot-1`,
  `nautobot-nautobot-worker-1`, `nautobot-nautobot-scheduler-1` recreated and
  healthy.
- `nautobot-server migrate nautobot_intent_catalog` inside the container: ran
  clean.
- `nautobot-server showmigrations nautobot_intent_catalog`: `0025_desiredservicebinding`
  applied (`[X]`).
- `nautobot-server makemigrations nautobot_intent_catalog --check --dry-run`:
  `No changes detected`.
- `nautobot-server shell` sanity check: `DesiredServiceBinding` model imports
  and queries cleanly (`count=0`, as expected — no live rows yet).

## Next

Step 7 (pause point): the live migration batch (three `node_agent`
placements: aghub, agstudio, agpc) and acceptance demonstration. Will show
the dry plan first before applying with `--yes`, per the plan.
