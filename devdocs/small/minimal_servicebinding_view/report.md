# Minimal DesiredServiceBinding GUI View — Report

Date: 2026-08-01

## Background

`service_relation` Phase 1 ([devdocs/vision/service_relation/p1/plan.md](../../vision/service_relation/p1/plan.md#L78))
deliberately left `DesiredServiceBinding`'s UI surfaces (table/filter/nav/detail
template) as discretionary and did not build them — the model shipped with a
batch-endpoint writer, REST API viewset, and GraphQL only. As a result the
Nautobot GUI never showed a "Service Bindings" page even though the roadmap
was fully complete and the three real bindings (`aghub`/`agpc`/`agstudio`
node-agent → `ollama`) were correctly persisted and converged (confirmed via
`nctl relations`). This was raised as a question ("why is there no menu for
it") and this small task adds the missing, minimal read-only view.

## What was implemented

Mirrored the existing read-only-only pattern used by every other Desired
State model in `nintent/nautobot_intent_catalog` (list + detail, no
add/edit/delete):

- `filters.py`: `DesiredServiceBindingFilterSet` (id/consumer_placement/
  binding_name/provider_service, plus a `q` search on `binding_name`).
- `tables.py`: `DesiredServiceBindingTable` (three columns: consumer
  placement, binding name, provider service — all linked).
- `views.py`: `DesiredServiceBindingListView` / `DesiredServiceBindingView`
  (`ObjectListView`/`ObjectView`, `select_related` on both FKs).
- `urls.py`: `service-bindings/` and `service-bindings/<uuid:pk>/`, names
  `desiredservicebinding_list` / `desiredservicebinding` — the model's
  `get_absolute_url` (`models.py:776`) already pointed at the `detail` name,
  so no model change was needed.
- `navigation.py`: added "Service Bindings" under the existing "Desired
  State" nav group, right after "Service Placements".
- `templates/nautobot_intent_catalog/desiredservicebinding.html`: new detail
  template, same shape as the other model detail templates (attr-table with
  linked FKs).

No model, migration, batch-endpoint, or API changes — this task only adds the
GUI list/detail surface on top of the already-shipped model and data.

## Test updates

Both existing UI-contract test files enumerate every retained model/route by
name, so they needed the new model added rather than being satisfied
automatically:

- `tests/test_templates.py`: added `desiredservicebinding.html` to the
  expected-templates set.
- `tests/test_ui_contract.py`: added `desiredservicebinding_list` /
  `desiredservicebinding` to `RETAINED_UI_ROUTE_NAMES` (18 → 20, test renamed
  accordingly), added a `MODEL_URL_PREFIXES` entry (`has_add=False`, since
  this model never had add/edit/delete routes to begin with — only
  edit/delete literal paths are checked 404 for it, not add), and added a
  `RUNTIME_MODEL_MATRIX` entry using the pre-existing `make_desired_service_binding`
  factory with `label_field="binding_name"`. This automatically covers list
  render, detail render, permission enforcement, and POST-non-mutation for
  the new pages via the existing runtime test classes — no new test classes
  needed.

## Verification

| Command | Result |
| --- | --- |
| `python3 -m unittest discover -s nautobot_intent_catalog/tests` (nintent, Django-free) | OK, 129 tests, 10 expected skips |
| `./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb` (superproject root) | OK, 206 tests, 0 failures |

The runtime gate run includes the updated `test_ui_contract.py` /
`test_templates.py`, so it live-renders the new list and detail pages against
a real Nautobot, checks permission enforcement, and checks POST does not
mutate rows — the same coverage every other retained model gets.

## Deployment

Changes are committed to the local `nintent` working tree only; not yet
pushed or deployed to the local scratch Nautobot container. Per the
established deployment path (`.local/localenv_memo.md`): push nintent → the
user pushes → `docker compose build --no-cache` (check the resolved SHA in
the build log — plain `build` can cache a stale commit) → migrate (no new
migration needed, this is UI-only) → restart. Left for the user/next step
since it touches the running container and a push to the remote.
