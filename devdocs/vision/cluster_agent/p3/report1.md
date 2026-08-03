# Step 1 report — Automated test for the wrapper

## What was done

Extended `devtests/test_strategy/test_mtls_conformance.py` (reused per the
plan, rather than a second TLS harness) with:

- `_Fixture.write_client_conf`/`run_wrapper` helpers: write a real
  `client.conf` pointing at the fixture's own ephemeral port/CA/cert/key,
  then `subprocess.run` the actual committed
  `ansible_agdev/roles/cagent_client/files/cagent` script (not curl, not a
  reimplementation).
- `test_wrapper_ask_with_wait_prints_answer_and_exits_zero` — `ask` (default
  wait) against a real TLS handshake + real ledger + a (locally faked)
  OpenCode turn; asserts exit 0 and the completed answer text on stdout.
- `test_wrapper_status_fetches_a_created_requests_state` — `ask --no-wait`
  then `status REQUEST_ID`.
- `test_wrapper_continue_reuses_the_session` — `ask` then `continue
  SESSION_ID`, asserts the second turn's response carries the same
  `session_id`.
- `test_wrapper_revoked_cert_call_fails_with_forbidden_envelope` — revoke
  before calling; asserts non-zero exit and the `forbidden` envelope
  visible on stderr.

`_FakeOpenCode` (this file's OpenCode stand-in) had to grow real per-session
message-count tracking with a short (`0.2s`) delayed completion on
`prompt_async`, instead of the previous "always count=1, always completed"
constant — the previous version never satisfied `worker.py`'s real
`count > baseline` completion-detection logic, so anything waiting for an
actual `completed` transition (the wrapper's default wait behavior) hung
until the worker's 300s `TURN_TIMEOUT_SECONDS` and then failed — invisible
before because no prior test in this file ever waited past the immediate
post-create `queued` state.

README_DEV command-matrix note: no new gate file added; the existing mTLS
conformance gate's row now covers 12 cases (was 6 at the start of this
phase), noted here rather than duplicating the table.

## Real bug found and fixed during this step

While making the new wait-based tests reliable, an **intermittent, non-test
failure** turned up: freshly signed-and-registered certificates were
occasionally (`assert 403 == 202`) rejected as "certificate not registered
or revoked" immediately after registration, with no revoke involved. Ruled
out test-order/fixture-isolation causes (each test's `_Fixture` owns a
fresh CA/ledger/`tmp_path`; reproduced with `-x` at different, unrelated
tests across repeated runs — classic non-deterministic evidence, not an
ordering bug) and confirmed the same intermittent failure predates this
step entirely by checking out the Step 0 commit and rerunning it stand-alone
5 times (1 failure out of 5, on an unrelated pre-existing test).

Root cause, confirmed with a standalone script performing a real TLS
handshake: `cagent_api/ca.py`'s `_wrap()` computed `serial_hex =
format(cert.serial_number, "x")` — plain Python int-to-hex, which drops a
would-be leading zero nibble whenever the serial's most significant byte is
`< 0x10`. `ssl.SSLSocket.getpeercert()["serialNumber"]` (what
`auth.CertAuthenticator` actually compares against the ledger) never drops
it — OpenSSL's representation is always byte-aligned (even hex-digit
count). Measured empirically: **53/500** (≈10.6%, matching the ~1/16
theoretical rate) of randomly generated serials hit this, and a live
TLS-handshake script confirmed the exact mismatch (e.g. Python:
`d4c5746d...` (39 chars) vs. OpenSSL: `0D4C5746...` (40 chars)).

This is a real, previously-latent production defect: **any node
enrollment has roughly a 1-in-10 chance of the freshly signed, freshly
registered certificate being permanently rejected** by `cagent-api`,
looking exactly like "not registered" even though `cagent-ledger list`
shows it `active` — an extremely confusing operator experience, and one
agpc's real enrollment (p2/report5b.md) simply didn't hit by chance
(its serial happens to be even-length). Fixed by adding
`ca.serial_number_to_hex()` (pads to even length, matching OpenSSL) and
routing `_wrap()` and `ca_cli.py`'s CA self-print through it. Added
`test_serial_hex_matches_getpeercert_even_when_top_byte_needs_zero_padding`
(loops, bounded at 500 tries, until it reproduces the odd-length case, then
proves that cert authenticates) as a permanent regression test — 5/5 clean
reruns of the full conformance file after the fix, vs. visible flakiness in
at least 1 of every ~5 runs before it (both before and after this step's
own additions, confirmed by testing the Step 0 commit standalone).

No agpc/production remediation needed: its already-working serial is
unaffected; the fix only prevents future enrollments from hitting the
~10% chance.

## Deviations from the plan

None to the wrapper. The `ca.py` fix is additional, unplanned but necessary
work discovered while making Step 1's tests reliable — same category as
Step 0's `server.py` auth-gap fix (a pre-existing Phase 2 defect, not a
Phase 3 contract change).

## State

`uv run pytest -q` in `cagent/`: **70 passed** (unchanged from Step 0 — the
`ca.py` fix didn't need new unit tests since no existing test asserted the
old, wrong hex format; covered instead by the new real-TLS regression
test). `uv run --project cagent pytest -q
devtests/test_strategy/test_mtls_conformance.py`: **12 passed** (was 7 at
the end of Step 0: +4 wrapper-driving tests, +1 serial-padding regression
test), confirmed clean across 5 consecutive full-file reruns. No live
process running.

## Next

Step 2 — Ansible role `cagent_client` (install the wrapper, `~/.cagent/`
config, and an enrollment-check warning).
