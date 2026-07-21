# Phase 0 Step 0.2 — Complete the nintent surface inventory

Parent: [plan.md](plan.md), Step 0.2.

## Check performed

Read the live `nintent/nautobot_intent_catalog/` source tree and confirmed each row of the plan's
Step 0.2 boundary table against the actual current files, rather than trusting the plan's prose
description.

| Boundary | Verified current state |
|---|---|
| Models | `models.py` declares each domain model as `@extras_features("graphql") class X(PrimaryModel)` — e.g. `IntentSource`, `DesiredService`, `DesiredDependency`, `DesiredNode`, `DesiredEndpoint`, `DesiredServicePlacement`, `DesiredNodeOperationalOverride`, `DesiredIPRange`. Matches the plan's assumed pattern for adding `BrainDumpDocument`/`AlignmentReview`. |
| Migration | `migrations/` currently ends at `0013_analysis_provenance_and_generic_endpoint_policy.py`; next migration would be `0014_*`. Purely additive migrations are the existing norm (each file name names one change). |
| Forms | `forms.py` exists as a dedicated module, confirming forms are maintained separately from models as the plan states. |
| Tables | `tables.py` exists as a dedicated module (list-view column definitions), confirming the plan's assumption. |
| Views | `views.py` exists; app `urls.py` wires explicit `ListView`/`EditView`/detail-view routes per model (e.g. `desirednode_list`, `desirednode_add`, `desirednode/<uuid:pk>/`, `desirednode/<uuid:pk>/edit/`) — confirms Braindump/Review will need the same explicit list/add/detail/edit routes, no generic-model auto-routing exists. |
| URLs | `urls.py` (app) confirmed as the single explicit route table described above. |
| Templates | `templates/nautobot_intent_catalog/` and a `templates/nautobot_intent_catalog/inc/` subfolder exist, confirming per-model templates are hand-maintained, not generated. |
| Navigation | `navigation.py` builds one `NavMenuTab("Intent Catalog")` containing one `NavMenuGroup` with a `NavMenuItem` per model (Sources, Services, Nodes, Endpoints, …) plus a conditional nctl-dashboard link. Confirms "one `Braindumps` entry" in Step 0.2 is consistent with the existing single-tab/single-group pattern. |
| Filters | `filters.py` exists as a dedicated module. |
| REST serializer | `api/serializers.py` exists as a dedicated module, separate from `api/views.py`. |
| REST viewsets/router | `api/views.py` currently defines exactly three viewsets — `DesiredNodeViewSet`, `DesiredServiceViewSet`, `DesiredEndpointViewSet` — and `api/urls.py` registers exactly `nodes`, `services`, `endpoints` on an `OrderedDefaultRouter`. This confirms the plan's "Current state" claim ("registers only desired nodes, services, and endpoints") is accurate as of this check, and that Braindump/AlignmentReview require two new viewsets plus two new `router.register(...)` calls — no existing generic registration will pick them up automatically. |
| GraphQL | Confirmed every model opts in via the `@extras_features("graphql")` decorator at class definition; no separate GraphQL schema file exists in this app, so adding the same decorator to the two new models is the same one-line mechanism already used eight times. |
| Documentation | `nintent/README.md` exists (14 KB) as the single top-level doc file; Phase 1 will extend it rather than add a second doc file, consistent with the plan. |
| Tests | `nautobot_intent_catalog/tests/` currently holds `test_analysis.py`, `test_importers.py`, `test_jobs_import.py`, `test_loaders.py`, `test_names.py`, `test_operations_hosts.py`, `test_operations_ipam.py`, `test_templates.py` — module-per-concern, confirming Phase 1 should add its own `test_braindump.py`/similar rather than folding into an unrelated file. |

## Result

Every row in the plan's Step 0.2 table was checked against the live nintent source tree; no
discrepancy was found and no edit to `plan.md` was required. The "Current state" section of
`plan.md` (REST registering only nodes/services/endpoints; models using `PrimaryModel` +
`@extras_features("graphql")`; UI surfaces maintained independently) is confirmed accurate, not
just asserted.
