# modernize_cagent p1 — step 4 report: handoffs

## What was built

- `topics_serve.handle_handoffs` (skeleton landed in step 3) is now complete.
  After the front's answer is posted, what it *wrote* in `<N>/front/` drives
  the branches — its chat answer is never parsed:
  - `required_info.md` → `<N>/operator/` is created, the file copied in,
    `agent/tools/toolset_nctl.md` copied to `<N>/operator/tools/`, the
    operator run with `guides/operator_read/guide.md` as its prompt, and its
    answer posted verbatim. The serving ends there.
  - `requested_change.md` → registered as a Plane Work via the new
    `cagent_api/plane.py`.
  - Both present → both branches, independently: the Work is registered
    first, then the operator runs (mixed requests stay observe-first, per
    the plan's decision).
  - Neither → the front's answer was the whole serving.
- `cagent/src/cagent_api/plane.py` — a slimmed copy of agforge's `plane.py`
  on the shared `agag.plane` client: fixed project `ClusterAdmin` (found, or
  created on first use), `split_document` (first `#` heading = title, rest =
  description — the front guide's existing contract),
  `external_source="cagent"`, `external_id="<channel>/<topic>"` so one topic
  is one Work and a re-serve updates it. No labels, no `[TOOLS]` footer, and
  no `[AUTO]` project marker — nothing selects these Works for automated
  execution this phase.
- Credentials: `pj-agdev/.local/plane-credentials.env` copied (mode 0600) to
  `pj-clusterintent/.local/plane-credentials.env` (git-ignored, verified with
  `git check-ignore`); path overridable via `CAGENT_PLANE_ENV`.

## Verification

- `tests/test_topics_serve.py` extended, mirroring agforge's suite: the
  operator workspace is built (file + toolset copied) and its answer posted
  verbatim; the front's answer posts before the operator runs; the change
  branch registers the Work without building an operator dir; both files
  present registers the Work then runs the operator; a Plane failure is
  posted as `failed during handoffs: …`, not swallowed.
- New `tests/test_plane.py`: a registered Work carries the cagent external
  key, no labels, and the `Ready` starting state; `ClusterAdmin` is created
  on first use without the `[AUTO]` marker; serving the same topic twice
  updates one Work; the env-var override and the missing-credentials error.
- `uv run pytest`: 192 passed.
