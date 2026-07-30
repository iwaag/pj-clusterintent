# Retire core Phase 2 — Step 4 deployment and live transition

Date: 2026-07-30

## Status: blocked on operator push

Local implementation is committed and the scratch image pin is ready:

- nauto `6462ebcbd9b8033853b60473dbe7f18d400cdd0b`
- nctl `13ae1cd64646cc94af76f54a200ca3d69b611318`
- superproject `6964dfd` (before this report commit), with `NAUTO_COMMIT` pinned to the new nauto
  revision.

The deployed container still truthfully reports nauto `3bd1820`. The plan explicitly reserves
nauto push for the operator, and rebuilding or Git Repository sync before that commit is available
remotely cannot deploy the change. No `agfixture` or Proxmox mutation has occurred.

Pre-deployment gates already passed: compute conformance 1 case and Nautobot runtime keepdb 181
cases (plus the Step 1/3 ordinary suites). After the operator pushes the exact nauto commit, the
remaining scratch-only work is: rebuild/sync, run Seed Home Cluster, take fresh read-only
observations and ingests, create/verify/delete the disposable synthetic VM row, rerun drift, and
write the final gate/report evidence.
