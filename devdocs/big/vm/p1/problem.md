# Problem: no authoritative LXC initial-access build source exists for Step 8

## Observed symptom

Phase 1 Step 8 requires selecting one initial-access mechanism for the disposable LXC (and,
eventually, the `agdnsmasq` case) that is proven — not assumed — to establish the shared Ansible
user, that user's approved SSH public key, the required privilege path, a running SSH daemon, a
running mDNS daemon advertising the endpoint's `mdns_name`, and a unique per-clone SSH host key.
The plan's own exit criterion (§8, plan.md exit criterion 8) requires "an authoritative template
build source" that proves these properties, and explicitly says: "If any property is unproven,
the golden template is not selected on the basis that it 'should work.' Either design a separately
bounded Proxmox provisioning action or mark Phase 1 blocked."

## Root cause

No such source exists anywhere in this project today:

- `ansible_agdev` has no packer, cloud-init, or LXC-template-build role/playbook.
- `nintent/CONCEPT.md` and `devdocs/big/vm/roadmap.md` describe the requirement (roadmap
  Decision 9, §205-208) but do not name or reference an actual build repository.
- The live Proxmox `local` storage does expose a `vztmpl` content area (confirmed in Step 2,
  `report1.2.md` §2: `content: backup,vztmpl,import,iso`), but Step 0 already established that the
  privileged helper (`nodeutils-pvesh-read`) does not allow
  `/nodes/{node}/storage/{storage}/content`, so Phase 1 cannot even enumerate what template
  artifacts currently sit on that storage, let alone audit one for user/key/privilege/sshd/mDNS
  properties.
- No prior Braindump, plan, or report in this repository (`devdocs/big/vm/`,
  `devdocs/small/`) names a specific template artifact, its digest, or its owner.

In short: Step 8 asks Phase 1 to *prove* properties of a template that does not yet have any
documented origin, build definition, or artifact identity in this project. There is nothing to
audit.

## Design concern

Proceeding past this gap without a real answer would violate the plan's own anti-guessing rule
(§Step8, and roadmap Decision 9: "it must not rely on an undocumented property of a template").
Any of the following would be an unjustified guess if picked unilaterally:

- assuming an official upstream Proxmox `vztmpl` (e.g. `debian-13-standard`) already has the
  required Ansible user/key baked in — it does not, by default;
- assuming a golden template exists somewhere off-repo without a pointer to it;
- inventing a build definition now, inside Phase 1, when Phase 1's own scope is explicitly
  read-only/non-deploying (plan §3 Non-goals: Phase 1 does not "deploy nodeutils, the privileged
  helper, or an Ansible role, or update a remote checkout").

## Recommendation

This is a decision only the operator can make, not one Phase 1 can infer from code or live state:

1. Decide whether the disposable LXC's first-boot user/key/sshd/mDNS setup will come from (a) a
   custom golden template built and maintained by a new packer/Ansible pipeline, or (b) a
   first-boot provisioning step (e.g. an Ansible play run once against a plain upstream template
   immediately after create, before the SSH-enrollment stop) layered on top of an official
   upstream `vztmpl`.
2. Once a mechanism is chosen, its build definition/playbook must be committed somewhere in this
   repo (or a named external repo) so Step 8's proof requirements are actually checkable evidence,
   not an assumption.
3. Until then, Phase 1 records exit criterion 8 as **unmet** — the report's exit-criteria
   checklist (Step 12) should mark Phase 1 `partially complete`, not `complete`, and name this gap
   explicitly rather than silently skipping it or picking an unproven default.

Steps 9 (finding vocabulary), 10 (baseline), 11 (rollout/rollback), and 12 (final audit) do not
depend on this decision and can still proceed; Step 8's live SSH-proof sub-steps (2, 4, 5 in the
plan's procedure) are the ones blocked pending this decision.
