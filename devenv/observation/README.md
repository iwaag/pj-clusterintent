# Scheduled node observation

`refresh-node-observations.sh` runs `nctl observe` (see
[`nctl/docs/observe.md`](../../nctl/docs/observe.md)): one operation that
collects and ingests fresh nodeutils reports and runs **no other reconcile
action**. Drift a host shows is recorded by the observation and left for a
person or a `change` request; this job never repairs it
(`project_migration` p5, decision D3). With no arguments the scope is every
node nctl's bootstrap inventory exports (active lifecycle, an mDNS
endpoint); arguments narrow it to those desired-node slugs.

A host that is asleep or otherwise not offering its trusted SSH key is
reported `unavailable` and not contacted; the other hosts are still observed.
No host is called refreshed unless its outcome is `observed`.

Every run keeps its `nctl.observe.v1` envelope in
`.local/observation-refresh/history/<UTC start>-<state>.json` (newest 500),
and `latest.json` names the newest. One timestamped line per host goes to
launchd's `stdout.log`. A lock directory prevents overlapping runs.

The LaunchAgent runs at login and every six hours, keeping observations below
the 24-hour drift threshold. It is independent of any workflow run. Install
the template after replacing `__PROJECT_ROOT__` with this checkout's absolute
path:

```sh
sed "s|__PROJECT_ROOT__|$PWD|g" \
  devenv/observation/com.clusterintent.observation-refresh.plist.in \
  > ~/Library/LaunchAgents/com.clusterintent.observation-refresh.plist
launchctl bootstrap "gui/$(id -u)" \
  ~/Library/LaunchAgents/com.clusterintent.observation-refresh.plist
```

**Recovery.** If the job is broken, run the script by hand or `nctl observe`
directly. Do not put `nctl reconcile --refresh-observation --yes` back in its
place: that runs whatever safe actions are planned for the host, which is how
this job used to change hosts unattended.
