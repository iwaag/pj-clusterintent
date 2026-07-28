# P2 Step 7 — Audit and deduplicate protocol clients

Status: complete.

`NautobotClient._request()` now centralizes the seven identical
`httpx.RequestError` translations while preserving the message
`cannot reach {url}: {exc}`. Verb-specific authentication handling and the
GraphQL error path remain unchanged.

`INTENT_GRAPHQL_TYPES` remains in `nautobot.py`: it is the transport client's
explicit declaration of the schema nctl consumes, and `ping()` owns the
installed-app versus usable-GraphQL protocol interpretation. `jobs.py` was
audited and retained unchanged: its status vocabulary, result sanitization,
artifact download, and response decoding describe the Nautobot Job protocol,
not desired-state policy.

`tests/test_nautobot.py` and `tests/test_jobs.py` passed (`35 passed`),
covering GraphQL/REST decoding; the nctl ordinary suite passed (`970 passed in
5.85s`) and whitespace validation was clean. No protocol message, envelope,
or external state changed.
