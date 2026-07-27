# P1 Step 3 — Build the conformance case set and generator

Status: complete.

## Delivered owner mechanism

Added Django-free `nintent/nautobot_intent_catalog/compute_conformance.py`. Its ordered,
JSON-only `CASES` execute the owner and emit `compute-conformance/v1` results; expected outcomes
are therefore observed from owner code, never hand-written. The deterministic serializer uses
two-space JSON, preserves declaration order, uses UTF-8 characters directly, and ends with one
newline.

The case set exercises accepted and rejected closed vocabularies/configuration, MAC
normalization, link pairing, endpoint eligibility, all 25 ordered lifecycle pairs, primary
endpoint zero/one/two and disqualifying cases, and every integer-bound minimum/minus-one/
maximum/plus-one plus null, wrong-type, and boolean values. The constants block is read from live
owner attributes.

Added owner-side tests proving that every declared public semantic symbol is represented, every
fixture constant resolves from the live owner, and serializing twice is byte-identical.

## Verification

The nintent Django-free gate passed: **236 tests run, 14 skipped**. The additional three tests are
the owner conformance assertions. No fixture has yet been committed, and nctl remains unchanged.

## Gate verdict

Complete: the owner-generated case set and serializer exist, all outcomes derive from execution of
the semantic owner, public-symbol/constant coverage is checked, and serialization is proven
stable.
