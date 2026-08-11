# Scheduled node observation

`refresh-node-observations.sh` refreshes the five nodes that host active
placements. Each invocation uses exactly one host-scoped reconcile round with a
forced nodeutils collect and Nautobot ingest. Normal safe reconcile actions that
are already planned for that host can run in the same round; destruction remains
disabled, and no second round is allowed. The script validates every executed
action rather than treating nctl's expected `max_rounds_reached` exit as failure.

The LaunchAgent runs at login and every six hours, keeping observations below
the 24-hour drift threshold. Install the template after replacing
`__PROJECT_ROOT__` with this checkout's absolute path:

```sh
sed "s|__PROJECT_ROOT__|$PWD|g" \
  devenv/observation/com.clusterintent.observation-refresh.plist.in \
  > ~/Library/LaunchAgents/com.clusterintent.observation-refresh.plist
launchctl bootstrap "gui/$(id -u)" \
  ~/Library/LaunchAgents/com.clusterintent.observation-refresh.plist
```

Per-host results and launchd logs are written below
`.local/observation-refresh/`. A lock directory prevents overlapping runs.
