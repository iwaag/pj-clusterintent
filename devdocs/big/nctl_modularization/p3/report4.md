# P3 Step 4 — Service action handlers

Status: partially complete.

- Added static `service_profile` and `dnsmasq_config` handlers and routed the
  service loop through the dispatch seam.
- The exact dnsmasq `host_slugs` limit and playbook grouping behavior are in
  their respective handlers. The focused executor suite passed: **45 passed**.
- The residual legacy service helper implementations and their test ownership
  remain to be deleted/re-owned in Steps 5–6; therefore this step does not
  claim the executor import/branch exit criterion yet.

Implementation commit: nctl `90e97a5`.

