# Step 5 Report — agfixture desired-state preview

Status: stopped before apply.

The canonical `nauto/seed/intent_sources.yaml` proposal was changed exactly as planned for the
guest-OS realization choice:

```yaml
desired_nodes.agfixture.accepted_actual_types:
  - device
```

Because the local Nautobot image bakes this canonical file at
`/opt/nautobot/intent_sources.yaml`, the local scratch image was rebuilt and its in-container
SHA-256 was confirmed to equal the working-tree SHA:

```text
671783de559050f40da4bf9c9187c6a3ebdd703fe5df2ebb6b24fbc2d1fafa0c
```

The supported `Import Intent Sources` Job was then run with `apply=false` against that explicit
path. JobResult: `0b600cb4-bccb-4dcc-a928-b5be10c7ad63` (`success`). Its private structured
artifact is retained at:

```text
.local/vm_converge_fix/step5-import-preview/intent-import-result.json
```

The artifact has schema `nintent.intent-import.v1`, mode `preview`, zero errors, and totals
`create=0`, `update=2`, `unchanged=25`, `conflict=0`. It contains the expected single DesiredNode
change:

```text
DesiredNode agfixture: accepted_actual_types [virtual_machine] -> [device]
```

It also contains an **unreviewed, unrelated** change:

```text
DesiredEndpoint agfixture/primary: gateway_address null -> 192.168.0.1
```

Therefore the preview does not meet Step 5's requirement that it show exactly the reviewed
agfixture field change and no unrelated desired rows. No `apply=true` import, no ledger mutation,
and no reconcile was run. Steps 6 and 7 remain pending a user decision on whether the endpoint
gateway update is intended and, if so, a fresh bounded preview and explicit apply approval.
