# P2 Step 9 — Documentation and measurement

Status: complete.

The compute ownership note now names `nctl_core.compute.contract` and
`nctl_core.compute.collection`. No manifested test ID moved; all MANIFEST
paths remain present and their owning gates passed in Step 8.

The repeated measurement reports 970 nctl cases across 150 tracked Python
files (75 test files); the full component counts are nintent 236, nauto 110,
nodeutils 54, and Ansible helper 4. The explicit runtime measurement from
Step 8 is 299 in both clean and keepdb modes. Structural evidence was
recollected using the Phase 0 collector in the private P2 evidence directory.

The Phase 2 changes remove the source/domain and Braindump presentation
boundary violations identified in the frozen audit. Production composition,
reconcile execution, SSH, and dnsmasq remain assigned to later roadmap phases.
