# nctl Modularization Phase 1 — Final Report

Status: complete.

Phase 1 establishes nintent as the sole independently maintained semantic owner of the compute
contract. nctl intentionally retains read-time validation so malformed/stale GraphQL rows remain
visible `DesiredSourceIssue` records and cannot reach typed compute collections, drift, planning,
or actuation. That retained implementation is fixture-bound rather than independently maintained:
nintent executes the ordered JSON-only case set, nctl consumes the one committed fixture, and the
superproject freshness gate rejects a stale fixture.

The disposition table corrected Phase 0's omissions: primary-endpoint validation is shared,
realized-link/source pairing and its vocabulary are shared, MAC uniqueness remains deliberate
two-layer enforcement, and the original manifest recount included its header. No source-issue
code, path, severity, message, blocked-consumer value, or evidence value changed in the fixed
malformed-row comparison.

The three required divergence proofs were performed and restored: an nctl bound change failed the
consumer replay, an owner MAC-normalization change failed freshness and then consumer replay after
regeneration, and fixture tampering failed freshness. The surviving lifecycle predicate spelling
is `is_actionable_lifecycle`.

The full local matrix passed: nctl 968, nintent 236 with 14 expected skips, nauto 110, nodeutils
54, Ansible helper 4, OpenSSH conformance 2, Ansible conformance 1, privileged-helper integration
1, and compute-conformance freshness 1. The manifested compute-inert test passed. The source-issue
surface is byte-identical to the frozen pre-Phase-1 source. The dnsmasq artifact is byte-identical;
hosts/production content is unchanged after excluding their declared generated-at/generation-ID and
fresh-observation timestamp metadata.

After user-authorized nintent push and local scratch rebuild, build log, `build_info.json`, and
image label all prove installed nintent
`84ac0b125c996bcc9c821252c34e84ca967c64f0`. `intent_sources.yaml` stayed byte-identical to the
Dockerfile's nauto pin. Both Nautobot runtime modes passed 299 tests with the expected six RawSQL
warnings; the clean run recreated and destroyed only `test_nautobot`.

The final matched tuple is superproject `b3abb603601b094469f99c5490c2f88384ac6afa`, nctl
`077ee9c1b2d9da8870f172de2ef172f792a40cd5`, nintent
`84ac0b125c996bcc9c821252c34e84ca967c64f0`, nauto
`6dab422a725a2e2e4e24e98079e992d1111c0ef1`, nodeutils
`775ed7fad5110a96186a737147b87d3bf450ced2`, and ansible_agdev
`66b31c89986d1b2ecfa187a72209d8bd96838fd4` before this report commit.

Phase 2 inherits a fixture-bound compute block still located in
`nctl/src/nctl_core/sources/desired.py`. Moving it must carry the conformance consumer and must
not change any fixture-pinned semantic value or source-issue behavior.
