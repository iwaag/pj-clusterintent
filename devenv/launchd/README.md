# Local launchd services

The legacy cagent API and Zulip listener retired in project_migration p5.
Their templates were removed; installed plists are archived in ignored
local state. Managed cagent runs use WFE's executor and request intake.

The independent observation-only job remains documented and installed from
[`../observation/`](../observation/README.md). It runs `nctl observe`, never
general reconciliation. No retired cagent HTTP process is needed for it.

Historical cagent code and request evidence remain in `cagent/` and ignored
local state. Do not reinstall old service labels to refresh cluster data;
use the managed project's `scan` workflow and its snapshot artifact.
