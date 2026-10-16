# cagent (legacy instance retired)

**The legacy instance is retired since 2026-10-16 and no longer answers.**
Its Zulip listener and HTTP entrances are stopped. Old DMs, `{instance}`
topics and `cagent-` prefixes are historical conversations. The cluster
snapshot consumer now reads the managed scan artifact through WFE.

cagent is now the managed **cagent** project in the workflow editor:

- `wf-cagent.consult`: explain cluster state with sources and ages;
- `wf-cagent.report`: record an installation, its purpose and owner;
- `wf-cagent.scan`: collect observations and publish a snapshot; never repair;
- `wf-cagent.change`: plan a change, obtain the Developer's agreement,
  execute, verify and present its records;
- `wf-cagent.freework`: work on the project itself.

Use a `request-…` topic in the workflow's channel, *Request a run* in the
editor, or a workflow delegation. An argue that needs cluster facts uses a
consult request. Front's routing update is a named follow-up.

Nautobot, nctl, nodeutils and Ansible remain the backend. Old evidence,
incidents and conversations are retained. The independent observation job
uses `nctl observe`; no legacy HTTP agent is needed for snapshots.
