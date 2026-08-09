# Cluster sync implementation report

## autolab-meets-cagent Step 1 — 2026-08-09

`agautolab1` was observed and ingested through nctl, linked to its guest-OS
Nautobot Device, and admitted to production composition. The stale desired
node contract was corrected from `accepted_actual_types: [virtual_machine]`
to `[device]`; its Proxmox `DesiredComputeInstance.realized_vm` remains the
separate compute realization.

Successful reconcile operation: `01KZJ057AHF4YRWRG4TTHZJPYW`. A fresh
host-scoped drift reports node and compute instance both converged, with the
node production result `state: included`. Detailed execution notes are in the
episode's `report1.md` in the developer-documentation repository.

## autolab-meets-cagent Step 2 — 2026-08-09

cagent's boundary now permits recoverable desired-state apply and ordinary
reconciliation while hard-denying `--allow-destroy`, `nctl prune`, braindump
purge/review-delete, and direct Proxmox destroy playbooks. The dedicated
OpenCode process was restarted with the rendered policy.

Human-entrance request `req_9fdce08de7f949c68457b94736d99a32`
successfully committed a 43-operation all-unchanged desired-state re-apply.
Request `req_3962255e3059434091a04bf3c62f19b8` attempted a non-mutating
`--allow-destroy` dry plan and matched the hard deny before execution. Fresh
desired and PostgreSQL backups were taken first; cagent's 92 tests pass.

## autolab-meets-cagent Step 3 — 2026-08-09

The `autolab_node` role now copies the existing human-entrance bearer token
from controller-local state to node-local state at mode 0600 and installs an
async `autolab-cagent` submit/get/wait/ask wrapper. The role now deploys
agautolab from the actual command-node Gitea source; its static inventory is
retained as an independent maintenance path.

The playbook completed on agautolab1 with 16 ok, 5 changed, and zero
failures. A wrapper invocation originating there completed request
`req_a78e92295fe6438aa772e4944704eddc`, whose fresh drift response reported
the node and compute scopes converged and production composition included.

## autolab-meets-cagent Step 4 — 2026-08-09

Added the `static_web_app` production profile and a thin cross-platform
Ansible role that clones command-node Gitea content and controls a per-instance
Python static server. Production composition can now aggregate multiple
placements of the same profile on one host, and profile reconciliation can
derive `started`/`stopped` from placement config and evaluate HTTP checks.

The `snake-web` service was declared on agstudio with an explicit HTTP
endpoint on port 8123. Reconcile operation `01KZJ2821RRFNST2MPH0WPKH7W`
started it and converged. A desired-state stop/start cycle proved the port
closed while stopped and served the Snake HTML after restart; final operation
`01KZJ2C2E12M210077BR8XZHMC` converged in one round. Full nctl validation:
1,292 tests passed. Port declarations are now visible in desired state, but
there is still no automated collision comparator.

## autolab-meets-cagent Step 5 — 2026-08-09

Registered `agautolab` as an active desired service with port-8791 endpoints
and placements on agstudio and agautolab1. The former honestly remains a
manual placement backed by its existing checkout; the latter is
`nctl_managed` through the existing Linux `autolab_node` role. Action
planning now excludes manual placement hosts.

Managed reconcile operation `01KZJ2P08MMA03TWAJSZXTN6EH` was a deployment
no-op (15 ok, 0 changed) followed by successful observation. Final refreshes
`01KZJ2TW22TEESZK0GJTY5Q9F4` and `01KZJ2VBEJ7S38ZHRJX1YFH1NV` converged both
placements. `nctl relations --service agautolab --json` now reports the
service converged and both placements satisfied; repeat dry reconciles for
each host contain zero actions. Full nctl validation: 1,294 tests passed.

## autolab-meets-cagent Step 6 — 2026-08-09

The agautolab1 mediator built and published `cagent-snake-e2e`, then invoked
cagent to register and deploy it as `static_web_app` on the same node at port
8124. An initially addressless service endpoint caused correct
`service_missing` drift despite successful deployment; follow-up cagent
request `req_65fbaa8e294a44418c11d9ac6c71fbbe` repaired the endpoint and
reconcile `01KZJ46G8Z5DJ5ZKYKNT58EQRN` converged.

Subsequent node-originated cagent requests stopped and restarted the service:
`req_901dcf59c0a54cc0a56899d93e428c44` / operation
`01KZJ4B74020BYGZDY6X84SD9W`, then
`req_930c973732dd48c79cb17938d938c045` / operation
`01KZJ4FDS30G4J329Y541EY7VC`. Both reconciles converged; port 8124 was closed
while stopped and served the expected title after restart. Safety request
`req_8539deae84b1437ba3c42cc7f3e0aa0d` matched the hard
`*--allow-destroy*` deny before execution.

cagent now explicitly permits headless reads of nctl's external operation
artifacts while retaining every destroy-class bash deny. Its service recipe
also requires a usable endpoint address before treating service drift as
resolved. cagent's 92 tests pass; final cluster drift reports the new service
converged with no diffs.
