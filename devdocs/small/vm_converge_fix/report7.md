# Step 7 Report — Import idempotency repair

Status: implemented and committed; deployment/retry pending.

The failed Step 6 repeat was traced to the nintent Import Job's planning projection: its
`DesiredEndpoint.objects.values()` field list omitted `gateway_address`. The database row had in
fact stored `192.168.0.1` (independently confirmed by the nctl desired-state GraphQL read), but
the preview compared the YAML value to an absent projected value and repeatedly reported
`null -> 192.168.0.1`.

The nintent repair:

- introduces one shared `DESIRED_ENDPOINT_UPDATE_FIELD_NAMES` projection that includes
  `gateway_address`;
- uses that projection for the import plan; and
- extends post-commit confirmation to every YAML-owned DesiredEndpoint field, including gateway.

Regression coverage was added and the Django-free suite passed:

```text
python3 -m unittest discover -s nautobot_intent_catalog/tests
-> 239 passed, 14 expected skips
```

Committed nintent revision: `525057f fix intent endpoint import idempotency`.

The local Nautobot Dockerfile intentionally installs nintent from the pinned GitHub revision, not
from the working tree. Per `.local/localenv_memo.md`, deployment needs the user to push this commit
before the scratch image can be rebuilt. Until that happens, no repeat Import Job or reconcile
apply is attempted against an image that lacks this repair.
