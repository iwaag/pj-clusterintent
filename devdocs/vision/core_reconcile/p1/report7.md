# Phase 1 Report — Step 7 (CLI docs and closeout)

Date: 2026-07-15. Implements [p1/plan.md](plan.md) Step 7 and consolidates the Phase 1 status
after [report1.md](report1.md) through [report6.md](report6.md).

## Client-neutral operation surface

The supported workflow is documented directly through `nctl --help` and `nctl/README.md`:

- inspect only with `nctl render dnsmasq` (and `--json` for structured details);
- preview with the default `nctl apply dnsmasq` check+diff;
- review the diff and apply with `nctl apply dnsmasq --yes` only after explicit authorization;
- report the operation ID, artifact, and event log;
- preserve and report render, inventory, validation, and Ansible failures rather than bypassing
  safeguards.

No client-specific AI skill is part of Phase 1. The CLI, stable JSON envelopes, and event logs are
sufficient for both humans and AI callers. A generic integration such as MCP can be added
separately if needed without changing the workflow backend.

## Documentation completed across Steps 5–7

- `nctl/README.md`: render/apply usage, dry-run semantics, `[ansible]` configuration, inventory
  target validation, and operation artifact/event locations.
- `nctl/docs/event-log.md`: dnsmasq apply event vocabulary.
- `nctl/docs/output-format.md`: `nctl.apply.dnsmasq.v1` payload and dry-run success semantics.
- `ansible_agdev/README.md` and `README_DEV.md`: deploy-only playbook path/input and removal of
  Nautobot Job/token/File Proxy responsibility.
- `nintent/README.md` and `README_QUICK.md`: nctl owns consumer-format rendering; nintent exposes
  desired/evaluation inputs.

## Deferred Step 4 deployment gate closed

After the nintent push, rebuilt the dev Nautobot images without cache and restarted the stack.

- The build installed `nautobot-intent-catalog==0.5.0` from commit
  `44d6ea3d06e62e9682bba191e00f4db9982e35c3`.
- Nautobot, worker, and scheduler containers are healthy.
- The old Job's historical DB record reports `installed: false`; it is no longer installed or
  runnable.
- `nctl status --json` returned `ok: true`: Nautobot is reachable/authenticated, intent GraphQL is
  present, and all submodules are clean.

## Final Phase 1 exit status

- [x] Live renderer parity: record lines, summary counts, and skip reasons matched; artifacts are
  saved under `p1/parity/`.
- [x] `nctl apply dnsmasq` implementation: dry-run/apply branches, operation artifacts/events,
  stable JSON envelope, target validation, and tests.
- [x] nintent renderer/Job path removed and deployed as 0.5.0.
- [x] Ansible playbook is deploy-only and takes `dnsmasq_records_src`.
- [x] nctl test suite: 90 passed.
- [ ] Dev-cluster Ansible check+diff and real apply: not run.

The final unchecked item is environmental rather than an implementation gap. The correct
service-group inventory is `inventories/generated/production.yml`, but it is absent and its
generation is explicitly on hold in `.local/localenv_memo.md`; the bootstrap `hosts_intent.yml`
cannot contain `dnsmasq_server`. In addition, `agdnsmasq.local` is documented as currently
unresponsive. The live apply test therefore stops safely before Ansible with
`ansible_inventory_missing`. It should be completed when the production inventory path is
unblocked and the host is reachable.

## Deviations from the original Step 6 plan

The plan assumed `hosts_intent.yml` provided `dnsmasq_server`. Repository documentation and the
generated inventory showed that it intentionally has no service groups. Configuration and error
guidance were corrected to use the current production inventory/export path. `nctl apply` also
validates that `dnsmasq_server` resolves to at least one host, avoiding a misleading successful
Ansible no-op.

## Commit boundary and next work

This is the fifth suggested Phase 1 commit: parent-repo report closeout and CLI documentation
status updates. Phase 1 code is complete; only the environment-dependent deployment proof remains.

Per the roadmap, the next implementation phase is Phase 1.5: migrate the hosts-intent export to
nctl using the same pure renderer + GraphQL + parity + Job deletion pattern. That phase does not
itself replace the production service-group inventory; the Phase 2 production-inventory migration
remains the eventual owner of that composition.
