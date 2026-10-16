#!/bin/zsh
# Scheduled node observation (project_migration p5): `nctl observe` only.
# Collects and ingests fresh nodeutils reports; never plans or runs any other
# reconcile action, so drift on a host is recorded, not repaired.
#
#   refresh-node-observations.sh            every node nctl's bootstrap inventory exports
#   refresh-node-observations.sh HOST...    only these desired-node slugs
#
# Every run keeps its envelope under .local/observation-refresh/history/
# (newest $keep), latest.json points at the newest, and one timestamped line
# per host goes to stdout (launchd's log). A host that was unavailable or
# failed is never reported as refreshed. Exit: nctl observe's (0 all observed,
# 1 any host not observed or no result, 2 usage).

set -u

project_root="${0:A:h:h:h}"
state_dir="$project_root/.local/observation-refresh"
history_dir="$state_dir/history"
lock_dir="$state_dir/lock"
keep=500

mkdir -p "$history_dir"
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
if ! mkdir "$lock_dir" 2>/dev/null; then
  print -u2 "$(stamp) observation refresh is already running"
  exit 0
fi
trap 'rmdir "$lock_dir"' EXIT INT TERM

cd "$project_root" || exit 1
started="$(date -u +%Y%m%dT%H%M%SZ)"
temporary="$state_dir/run-$started.tmp.json"
/opt/homebrew/bin/uv run --project nctl nctl observe "$@" --json >"$temporary"
command_status=$?

/usr/bin/python3 - "$temporary" "$history_dir" "$started" "$command_status" "$keep" <<'PY'
import json, os, sys
from pathlib import Path

path, history, started, status, keep = sys.argv[1], Path(sys.argv[2]), sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
try:
    envelope = json.loads(Path(path).read_text(encoding="utf-8"))
    state = envelope["data"]["state"]
except (OSError, ValueError, KeyError, TypeError) as exc:
    envelope, state = None, "no-result"
    print(f"{started} no usable nctl observe result (exit {status}): {exc}", file=sys.stderr)
target = history / f"{started}-{state}.json"
if envelope is None:
    target.write_text(json.dumps({"started": started, "exit": status, "state": state,
                                  "raw": Path(path).read_text(errors="replace") if Path(path).exists() else ""}))
else:
    envelope["refresh"] = {"started": started, "exit": status}
    target.write_text(json.dumps(envelope, indent=1))
    data = envelope["data"]
    for host in data.get("hosts", []):
        detail = f" — {host['detail']}" if host.get("detail") and host["outcome"] != "observed" else ""
        print(f"{started} {host['host']}: {host['outcome']}{detail} (operation {data['operation_id']})")
    for skipped in data.get("skipped", []):
        print(f"{started} {skipped.get('desired_node_slug')}: not in scope ({', '.join(skipped.get('reasons', []))})")
    print(f"{started} observe {data['operation_id']}: {state} (exit {status})")
latest = history.parent / "latest.json"
tmp = latest.with_suffix(".tmp")
tmp.write_text(json.dumps({"file": target.name, "state": state, "started": started, "exit": status}))
os.replace(tmp, latest)
for old in sorted(history.glob("*.json"))[:-keep]:
    old.unlink()
PY
rm -f "$temporary"
exit "$command_status"
