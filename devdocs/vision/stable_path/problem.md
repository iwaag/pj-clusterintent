# Problem: Agent Workdir Resolution Dependency on Declared OS

## Overview

When `nctl agent` commands (`run`, `attach`, `sessions`, etc.) resolve the working directory (`workdir`) on a target node, they rely on declared values (Desired State) and manual configuration rather than actual observed OS data (Actual State). This leads to configuration omissions, inconsistencies, and runtime failures.

---

## Specific Issues and Reproduction Conditions

### 1. `agent_workdir_unresolved` Error on New Nodes
For a newly added node with `node-agent` enabled, if no node-specific entry exists in `[agent.workdir_by_slug]` within `nctl.toml` and no `declared_host_os` is specified on the `DesiredNode`, running `nctl agent run` fails with the following error:

```json
{
  "code": "agent_workdir_unresolved",
  "message": "DesiredNode 'aghub' needs [agent].workdir_by_slug or a declared_host_os"
}
```

### 2. Path Inconsistency Due to Mismatch Between Declared and Actual OS
If `declared_host_os` is set to `macos` in the Desired State but the actual physical machine is running Linux (or vice versa), `nctl agent` prioritizes the declared state and resolves the workdir to `/Users/eiji/agent-work`. Because this path does not exist on the Linux host, OpenCode session creation and file operations fail with runtime errors such as `Path not found`.

---

## Root Cause

The `workdir` resolution logic in `_target_from_snapshot()` within `nctl/src/nctl_core/agent.py` only checks manual configuration or declared state (`declared_host_os`), without referencing actual OS observation facts (`observed_system`) collected by `nodeutils`.

```python
# nctl/src/nctl_core/agent.py L102-L110
configured_workdir = cfg.agent.workdir_by_slug.get(host)
if configured_workdir is not None:
    workdir = configured_workdir
elif declared_os in {"macos", "darwin"}:
    workdir = cfg.agent.macos_workdir
elif declared_os == "linux":
    workdir = cfg.agent.linux_workdir
else:
    raise AgentError("agent_workdir_unresolved", ...)
```

---

## Proposed Solution

Introduce a tiered resolution logic in `nctl agent` workdir resolution, similar to `nctl_core/production/derivation.py`, based on the following precedence order:

1. **`nctl.toml` `[agent.workdir_by_slug]`**: Explicit per-host override.
2. **Actual Observed Facts (`observed_system` via `nodeutils`)**:
   - `observed_system == "Linux"` $\rightarrow$ `linux_workdir`
   - `observed_system == "Darwin"` $\rightarrow$ `macos_workdir`
3. **Declared State (`declared_host_os`)**: Fallback for unobserved initial nodes.
