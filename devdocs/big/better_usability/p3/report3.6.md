# Phase 3 Step 3.6 — Update the current operator path without rewriting history

Parent: [plan.md](plan.md), Step 3.6.

## `nctl/docs/add-a-basic-service.md`

Prerequisites now state explicitly that a newly created `DesiredNode` is `active` by default (no
lifecycle promotion, no operational-config row) and points to `nctl lifecycle` for deliberate
`planned` staging. `DesiredService.lifecycle: active` in the worked example stays explicit,
unchanged, per Decision 5 (that default is intentionally not changing).

## `nctl/README.md` bootstrap/register flow

No section there currently claims manual lifecycle promotion or an operational-config step is
required — the node-registration recipe itself lives in `add-a-basic-service.md`'s prerequisites
and `devdocs/small/basic_service/plan.md`'s scenario 1, both updated below. Nothing needed fixing
in `nctl/README.md` proper beyond the Step 3.2 `### lifecycle` section already landed.

## `devdocs/small/basic_service/plan.md` scenario-1 supersession note

Added a narrow blockquote directly above the "Scenario 1" transcript: the historical steps are
preserved verbatim, but current readers are told a `DesiredNode` created today is `active` by
default with no manual promotion step, and that deliberate staging (`lifecycle: planned` +
`nctl lifecycle <slug> active`) is the explicit opt-in path now, not the implicit default the old
transcript's ordering suggested.

## nintent Quick Add / YAML examples

`nintent/README.md`'s two `desired_nodes` YAML examples (`edge-router-1` and the
`pcmain`/`dnsmasq-main` pair) had their `lifecycle: approved`/`lifecycle: active` lines removed and
replaced with a one-line comment noting the omitted field now defaults to `active`, plus a pointer
to `nctl lifecycle` for deliberate `planned` staging on the first example. This demonstrates the
normal (omitted) path in the examples readers copy from, rather than teaching an explicit-value
habit that Phase 3 makes unnecessary.

`nintent/CONCEPT.md`'s illustrative `lifecycle: active` examples (Proxmox/VM hierarchy, service-host
node) were deliberately left unchanged: they are architecture-concept illustrations, not the
copy-paste recipe surface the plan targets, and their explicit values remain accurate regardless of
the default. Editing them would be the "mechanical churn" the plan warns against for seed data,
applied to a doc where it isn't warranted.

## Doc/code grep sweep for obsolete claims

`rg -n -i "default.*planned|planned by default|manual promotion|operational.config.*required|requires? an operational.config"` across `nintent/*.md`, `nctl/*.md`, `nctl/docs/*.md`, and the
`devdocs/big/better_usability/` and `devdocs/small/basic_service/` trees found no stale claim that
new nodes default to `planned`, require manual promotion, or require an operational-config row
outside of this step's own new text and the roadmap's forward-looking phase description (both
correct as written).

A broader `lifecycle: planned` grep also turned up matches only in dated historical documents —
`devdocs/functions/ansible_hosts_intent/plan.md` (a "design exploration log," per the root
`README.md`'s own description of that tree) and several `devdocs/vision/core_reconcile/` and
`devdocs/big/better_usability/p0/` phase reports. These are explicitly allowed to retain dated
facts per plan.md Step 3.6 item 5 and were left untouched.

## Result

Full nintent suite re-run after the doc-only changes: **92 passed**, unaffected (expected — no
source files changed in this step). The documented recipe surface (`add-a-basic-service.md`,
`basic_service/plan.md` scenario 1, and the nintent YAML examples) now teaches the Phase 3
live-on-creation behavior as the normal path, with deliberate staging named as the explicit
alternative rather than left as an undocumented implicit step.
