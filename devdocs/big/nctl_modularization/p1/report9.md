# P1 Step 9 — Coordinated deployment

Status: complete.

## Matched nintent deployment

nintent commit `84ac0b125c996bcc9c821252c34e84ca967c64f0` was pushed by the user and verified at
`origin/main`. It contains the Phase 1 compute-contract owner/conformance work and its owner
documentation, together with the intervening test-only nintent changes since the previously
installed `e8732f17ae35d8c72d4d593e8d7311bd234fc0bf`.

Before rebuilding, `nauto/seed/intent_sources.yaml` was compared between Dockerfile pin
`1c78af8bdbfc69cafdc293b4082f866de9f271b0` and checkout
`6dab422a725a2e2e4e24e98079e992d1111c0ef1`: both have SHA-256
`f6cdcbb195fe09083edefbde7d317f70b1de280a179f3fb369587a7da30edfc6`.

`devenv/nautobot/Dockerfile` changes only `NINTENT_COMMIT` and its freezing-plan comment.
`NAUTO_COMMIT` is unchanged.

## Rebuild and runtime verification

After user approval, `docker compose build --no-cache` completed and its build log says pip
resolved nintent to `84ac0b125c996bcc9c821252c34e84ca967c64f0`. The Dockerfile's installed-commit
check passed. The running web container's `/opt/nautobot/build_info.json` and the rebuilt image
label both report that same nintent commit and the unchanged nauto commit.

Only Nautobot web, worker, and scheduler were recreated. All three are healthy and the HTTP
endpoint responds.

Both runtime modes passed with the exact-local staged sources and no credentials:

| mode | result |
|---|---|
| keepdb | 299 tests passed; 6 expected RawSQL warnings |
| clean | 299 tests passed; 6 expected RawSQL warnings; fresh `test_nautobot` created and destroyed |

The Phase 0 runtime baseline was 290 tests. The nine-test increase matches the Phase 1
compute-contract owner/conformance additions (also visible in the Django-free count rising from
227 to 236, with the same 14 skips).

The runtime wrapper's streamed caller output ended while its container-side test continued, so
the test process was re-run using the wrapper's exact staged source/PYTHONPATH setup with an
explicit persisted exit-status file. This retained the actual 299-test result and clean-DB
lifecycle rather than treating a truncated caller stream as a passing gate.

## Gate verdict

Complete: nintent was pushed and installed at the pinned matched revision, all three independent
build-commit proofs agree, the image-side nauto input is unchanged, all replacement containers are
healthy, and both Nautobot runtime modes pass.
