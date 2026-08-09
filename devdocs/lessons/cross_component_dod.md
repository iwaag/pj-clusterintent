# Definition of Done for Cross-Component Changes

Consult this checklist when writing a completion report for a reconciliation, inventory, SSH,
observation, or actuation change. It is review-time material: read it when declaring
completion, not as standing constraints during implementation. Rationale and case studies live
in [`reconciliation_lessons.md`](reconciliation_lessons.md); the completion vocabulary and
command matrix live in [`README_DEV.md`](../../README_DEV.md).

Before declaring such a change complete, verify and record all applicable items below.

## Contract and ownership

- [ ] The desired state transition and observable acceptance target are stated.
- [ ] Every route, identity, path, generation, and host-set value has one owner.
- [ ] External-tool assumptions were checked against normative behavior.
- [ ] Security policy cannot be overridden through an adjacent variable or arbitrary inventory
      field.

## Automated verification

- [ ] Focused unit and error-path tests pass.
- [ ] A real planner/executor multi-round test proves the intended transition.
- [ ] The test asserts that the intended action and preflight actually ran.
- [ ] Non-default ports, relative/canonical paths, malformed input, stale snapshots, multi-host
      scope, and post-mutation failures were considered.
- [ ] Repository-standard commands are reproducible from their documented working directories
      and leave every worktree clean.

## Production/external or framework-backed verification

- [ ] The initial state and reversible fixture are recorded.
- [ ] The dry plan names the exact expected action and target set.
- [ ] Apply uses the same generation and exact target set.
- [ ] Post-actuation observation records the exact state the action changed.
- [ ] Fresh drift proves convergence and no repeated action.
- [ ] Negative boundaries use disposable state and do not weaken policy.
- [ ] Production/external cleanup restores the original desired, actual, service, and
      trust-store state as applicable. Scratch verification cleans only fixture-owned state;
      declared persistent test resources may remain.

## Reporting

- [ ] Results distinguish the feature under test from unrelated cluster drift.
- [ ] Empty evidence is treated as an unexercised path, not a pass.
- [ ] Every omitted or substituted check is visible and prevents an unqualified `complete`
      status.
- [ ] Reports contain no tokens, credentials, raw SSH key blobs, or private user prose.
