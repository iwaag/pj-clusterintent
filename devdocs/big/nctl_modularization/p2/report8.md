# P2 Step 8 — Full matrix and runtime boundaries

Status: complete.

The complete offline matrix passed: nctl 970, compute conformance 1, nintent
Django-free 236 (14 expected skips), nauto 110, nodeutils 54, Ansible helper
4, privileged-helper integration 1, and OpenSSH/Ansible conformance 3.

The runtime label was made explicit as `nautobot_intent_catalog.tests`: both
the fresh clean DB and retained keepdb modes passed all 299 tests (48.522s and
49.324s respectively), with the expected six RawSQL warnings. The runtime
`prose-authority` test exposed one former internal import and was updated in
nintent, under the user's explicit authorization, to import the new
`nctl_core.braindump_render` presentation boundary. `post-mutation-evidence`
also passed in both modes.

Read-only nctl status, drift JSON, and ops-list commands completed against the
local scratch Nautobot; no write command was run.
