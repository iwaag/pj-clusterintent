# Step 5 — Update Current Documentation

## Changes

`nintent/README.md`:

- "Reconciliation and IPAM boundary" section: added a paragraph documenting
  that `Reconcile Desired IPAM Intent` now handles explicit IP intent, not
  only DHCP-reserved intent — the `dhcp_reserved`/`static`/`external`
  eligibility split, the self-observation requirement and its write-time
  recheck, the policy-aware `IPAddress.type` selection, and that a conflict/
  skip/empty-coverage result is never convergence.

`nintent/README_QUICK.md`:

- Updated the Jobs table's one-line description of `Reconcile Desired IPAM
  Intent` from "dry-run/apply `dhcp_reserved` endpoints" to reflect the new
  eligibility rule.

`nintent/README_DEV.md`:

- Added a "`Reconcile Desired IPAM Intent` (ipam_policy plan)" subsection
  under "Nautobot Verification" with concrete Nautobot-backed checks: migration
  no-op, updated Job description discovery, a dry-run scoped to one
  `static`/`external` endpoint with a matching observation (expects
  `endpoints: 1` and a Host-equivalent `create_fields.type`), a Device with an
  absent/mismatched `primary_ip_address` producing a skip rather than a write
  attempt, and a post-apply check that the created/linked type and
  `realized_ip_address_source="derived"` are correct.

`nctl/README.md`:

- Added a paragraph next to the existing SSH-preflight/`reconcile_ipam`
  documentation stating the eligibility rule is policy-aware (not
  `dhcp_reserved`-only), naming the three new manual-review codes, and
  restating the ledger-boundary guarantee (creates/links only when an
  explicit desired IP and a matching self-observation already exist; never a
  host IP-configuration actuator; never assigns an `IPAddress` to an
  `Interface`).

Historical plans/reports (`devdocs/small/ipam_policy/report1-4.md`,
`devdocs/small/fix_sshkey*/`, etc.) were not rewritten, per plan.md's explicit
instruction.

## Status

Step 5 complete. All five implementation steps from plan.md are now done at
the code and local-documentation level. Automated verification (full local
suites, already run per-step) and the Nautobot-backed/live verification phase
remain — the latter requires a user-approved push, container rebuild, and a
supervised scoped apply against the real `agdnsmasq` node.
