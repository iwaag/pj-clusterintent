# Step 2 — Retire the AI review feature

## Live action (user-performed)

User deleted the `AI Resource Review` Job Hook in the Nautobot admin UI
before this code landed.

## Code changes

- Deleted `nauto/jobs/ai_resource_review.py` (296 lines: the
  `JobHookReceiver`, Ollama HTTP client, prompt builder).
- `nauto/jobs/__init__.py`: removed the `AIResourceReview` import,
  its `register_jobs(...)` argument, and its `__all__` entry.
- `nauto/jobs/ingest_nodeutils_inventory.py`: removed
  `make_ai_resource_summary` and the
  `"ai_resource_summary": self.make_ai_resource_summary(report)` write
  from `build_custom_fields`. `make_docker_service_summary` kept —
  still used directly for the `docker_service_summary` custom field
  (that field's deletion is scoped to Step 3).
- No dedicated test file existed for `ai_resource_review.py`, and no
  test referenced `ai_resource_summary`/`make_ai_resource_summary` —
  nothing to delete there.
- `nauto/README.md`: removed the `jobs/ai_resource_review.py` tree
  entry, its description paragraph, the `AI_RESOURCE_REVIEW_*` env var
  block, the `think=false` note, and the Job Hook setup step. Field
  list bullets (including the AI-review fields) are left for Step 4
  per plan ordering — they still exist as live custom fields until
  Step 3 deletes them.
- `devenv/nautobot/docker-compose.yml`: removed
  `AI_RESOURCE_REVIEW_URL`/`_MODEL`/`_TIMEOUT`/`_LOG_PROMPT` from both
  the `nautobot` and `nautobot-worker` service environments.

## Not changed

- `devenv/.env` (gitignored, untracked) still sets
  `AI_RESOURCE_REVIEW_URL`/`_MODEL`/`_TIMEOUT`. Left alone since it's
  outside version control and harmless now that nothing reads those
  vars — user's call whether to clean it up locally.
- `agent_task_state` custom field: was only consumed as an input by
  the now-deleted Job Hook and was never written by the ingest job.
  Its removal from `seed/home_cluster.yaml` is scoped to Step 3 (it's
  on the frozen deletion list from Step 0).

## Verification

`python3 -m unittest discover -s tests` (from `nauto/`): **112
passed**, 0 failures, 0 errors.
