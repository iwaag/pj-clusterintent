# P2 Step 0 — Freeze the tuple and reproduce baselines

Status: complete.

Private evidence: `.local/nctl-modularization/p2/20260728T120000Z/` (mode 0700; derived files mode 0600).

The frozen implementation tuple matches the plan: superproject
`602c4cd09bfe33aaee7f4029bfa16d76864b5d90`, nctl
`077ee9c1b2d9da8870f172de2ef172f792a40cd5`, nintent
`84ac0b125c996bcc9c821252c34e84ca967c64f0`, nauto
`6dab422a725a2e2e4e24e98079e992d1111c0ef1`, nodeutils
`775ed7fad5110a96186a737147b87d3bf450ced2`, and ansible_agdev
`66b31c89986d1b2ecfa187a72209d8bd96838fd4`. All six implementation
repositories were clean. The superproject had only the user-supplied, initially
untracked P2 plan directory; it was preserved and is included with this commit.

The local Nautobot container's `org.clusterintent.nintent-commit` label and
`/opt/nautobot/build_info.json` both identify installed nintent
`84ac0b125c996bcc9c821252c34e84ca967c64f0`. Desired compute platform and
instance row counts were both zero.

Baseline gates reproduced:

- nctl ordinary: `968 passed in 5.28s`.
- Compute-conformance freshness: `1 passed`; the fixture SHA-256 remains
  `ccff71d9f4c7715a46c026c1529373fc38806208df49f512bc85d6a3e31b81ce`.
- The Phase 1 malformed-row source-issue corpus is byte-identical (empty diff).
- The Phase 0 structural collection was re-run into the P2 `*-before.tsv`
  evidence files, including import edges and coupling.
- The source artifacts retain the Phase 0 bytes under the declared exclusions:
  dnsmasq is byte-identical; hosts exclude only `generated_at`; production
  excludes generated-at/generation-ID/report-path and fresh-observation
  `collected_at` metadata. No content difference was found after those
  exclusions.
- The Phase 0 error-taxonomy collector was re-run and its 58 declared classes
  plus `Envelope` were captured as the Step 6 before-state. This is a
  static/reachable-code inventory; Step 6 will compare it against the same
  collector after the taxonomy move.

No tracked production or test source was changed in this step. An initial log
capture used a non-traversable private logs directory; the directory mode was
restored to 0700 and the nctl ordinary gate was immediately re-run successfully
with its log retained. No code or external state changed during that recovery.
