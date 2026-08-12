# Local launchd services

The checked-in `*.plist.in` files document the always-on native services.
Replace `__PROJECTS_ROOT__` with the parent directory containing
`pj-clusterintent` and `pj-agdev`, install the result in
`~/Library/LaunchAgents/`, and bootstrap it in the current GUI domain.

The active agstudio installation uses these labels:

- `com.clusterintent.cagent-opencode`
- `com.clusterintent.cagent-window-opencode`
- `com.clusterintent.cagent-api`
- `com.clusterintent.cagent-zulip`
- `com.agdev.agforge`
- `com.agdev.agautolab-gateway`

Each job uses `RunAtLoad`, `KeepAlive`, a ten-second restart throttle, and logs
under its owning project's ignored `.local/` directory. Secret-bearing inputs
remain in their existing ignored/default locations and are not copied into a
plist.
