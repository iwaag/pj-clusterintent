# P4 Step 2 — Pure deterministic rules

Status: partially complete.

- `drift/ip_ranges.py` is now the sole owner of IP parsing, range validation, classification, overlap, identity, and deterministic ordering. Direct range-rule imports in `test_drift_evaluation.py` now name that owner.
- `drift/gap_status.py` is the sole owner of gap severity precedence and is used by both the evaluator and snapshot orchestration.
- `drift/interfaces.py::normalize_mac` is the sole MAC normalizer. `dnsmasq.py` now imports it, preserving the byte contract; focused evaluation/dnsmasq tests and nctl ordinary (**970 passed**) passed.
- The MAC/interface *candidate extraction* and node candidate ranking helpers remain in `evaluation.py`. They are coupled to evaluator-local fact/report formatting, so moving them safely requires the resource-evaluator split in Step 3 rather than leaving an artificial helper interface or a compatibility import. This is a visible residual against Step 2's full target, not a claim of completion.
