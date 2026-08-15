# Local launchd services

The checked-in `*.plist.in` files document the always-on native services.
Replace `__PROJECTS_ROOT__` with the parent directory containing
`pj-clusterintent` and `pj-agdev` (and `__HOME__`, where a template uses it,
with the home directory), install the result in `~/Library/LaunchAgents/`,
and bootstrap it in the current GUI domain.

The active agstudio installation uses these labels:

- `com.clusterintent.cagent-api`
- `com.clusterintent.cagent-zulip`
- `com.agdev.agforge`
- `com.agdev.agautolab-gateway`

`com.clusterintent.cagent-opencode` and `com.clusterintent.cagent-window-opencode`
are gone: cagent runs its agent in-process, so `cagent-api` is its only job.
Boot the two removed labels out of the GUI domain when upgrading an existing
installation, and delete their plists from `~/Library/LaunchAgents/`.

Each job uses `RunAtLoad`, `KeepAlive`, a ten-second restart throttle, and logs
under its owning project's ignored `.local/` directory. Secret-bearing inputs
remain in their existing ignored/default locations and are not copied into a
plist.
