# Step 10 — Pre-schema-change baseline

Status: complete (with one corrected process error, disclosed below).

## Baseline artifacts (all captured before any Phase 1 schema change — none has occurred)

| Artifact | Command | Exit | Schema | sha256 |
|---|---|---|---|---|
| drift | `nctl drift --json` | 0 | `nctl.drift.v1` | `aecaa218164da7f1ca69992de621e1fe389662c78e7d7785bdca42e75a91f4bb` |
| hosts-intent | `nctl render hosts-intent --json` | 0 | `nctl.render.*` | `8a84e1aeabfcab0ce9a0663dd1d9a41c561490ac63b582da00c6df43f459f712` |
| production | `nctl render production --json` | 0 | `nctl.render.*` | `531b8edd65d520c22528c647c0aadde07050b91efad9e9048a884732bfb36b3a` |
| braindump list | `nctl braindump list --json` | 0 | `nctl.braindump.list.v1` | `8fa5610cefd59ee3f02004239d064980847db1d2d29a897691d5ff95cf4bf910` |
| braindump sanitized digests | `nctl braindump show <id> --json` × 5, sanitized | 0 (all 5) | `nctl.braindump.show.v1` | `027b815cbb00101738cc269aceef357462a4c3664c5e1d341de159659616e722` |

Positive content assertions (not just exit code): drift `ok:true`, 6 targets, all `converged`
(same result as Step 0, confirming no drift occurred between Step 0 and Step 10); hosts-intent and
production renders both still contain `aghub`/`agdnsmasq`; braindump list returned exactly 5 items
with real UUIDs and timestamps.

Generated-artifact present/absent+digest baseline (`hosts_intent.yml`, `production.yml`,
`production.reports/`) was already captured in Step 0 (`report1.0.md` §3) and is unchanged as of
this step — no schema change has occurred between Step 0 and Step 10, so it is not re-captured.

## Braindump sanitization — process error and correction

While producing the sanitized Braindump digest set (5 documents), the first sanitizer script only
redacted **top-level** string fields longer than 200 characters. The actual prose lives nested
under `data.braindump.body` and `data.braindump.alignment_review.summary`, so nothing was
redacted: the full body and Alignment Review text of all 5 Braindumps were written unredacted to
`.local/vm-p1/20260724T042313Z/braindump-sanitized.json`, and — because the sanitizer's own debug
`print()` was inspected via `cat`/`python3 -c` during this step — **the full Japanese prose text
of all 5 documents and their Alignment Reviews appeared in this session's tool output**, which is
recorded in this conversation's transcript. This is a direct violation of the plan's rule that
Braindump prose must never be written to disk (outside Nautobot) or piped to stdout.

Corrective action taken immediately upon discovery, before continuing:

1. The unredacted file was deleted (`shred -u`, falling back to `rm -f`) before any further step
   ran.
2. The sanitizer was rewritten to recurse into nested structures and redact any key named
   `body`/`summary`/`review`/`prose`/`content`/`text` at any depth, plus a defensive fallback that
   hashes any other string longer than 200 characters found anywhere in the structure.
3. `title` was additionally hash-redacted (not on the plan's explicit allowlist of
   ID/timestamp/authorship/review-freshness/digest, so treated conservatively) even though it was
   short.
4. The regenerated `braindump-sanitized.json` was verified programmatically (a recursive scan
   confirming no string value anywhere exceeds 200 characters) before this report was written.

This report does not reproduce the leaked prose. The user should be aware that this conversation's
transcript/tool-output history for this step contains the unredacted Braindump body and review
text for all 5 documents (IDs listed above are safe; the text itself is not reproduced here) and
may want to consider that when handling this transcript, since the underlying documents themselves
remain safely stored only in Nautobot (their authoritative location) and were never altered.

## Gate evaluation

Corrected sanitized digests now satisfy the plan's evidence-handling rule. All render/drift/
braindump-list artifacts were captured with schema, exit code, and SHA-256, and positive content
was asserted, not just exit code. Step 10 gate passed after the correction; the process error
itself is disclosed rather than hidden, consistent with the plan's mandate to name discrepancies
honestly.

## Discrepancies

**One real process error** occurred and is fully disclosed above (nested-prose sanitizer bug,
corrected within this same step, before any further step proceeded). No live Nautobot, Proxmox, or
desired-state mutation occurred as a result — this was purely an evidence-handling/output-hygiene
error, not an actuation error.
