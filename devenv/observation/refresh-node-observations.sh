#!/bin/zsh

set -u

project_root="${0:A:h:h:h}"
state_dir="$project_root/.local/observation-refresh"
lock_dir="$state_dir/lock"
default_hosts=(agautolab1 agdnsmasq aghub agpc agstudio)
hosts=("${@:-${default_hosts[@]}}")

mkdir -p "$state_dir"
if ! mkdir "$lock_dir" 2>/dev/null; then
  print -u2 "observation refresh is already running"
  exit 0
fi
trap 'rmdir "$lock_dir"' EXIT INT TERM

cd "$project_root" || exit 1
failures=0
for host in "${hosts[@]}"; do
  temporary="$state_dir/$host.tmp.json"
  result="$state_dir/$host.json"
  failed="$state_dir/$host.failed.json"
  rm -f "$temporary"

  /opt/homebrew/bin/uv run --project nctl nctl reconcile "$host" \
    --refresh-observation --max-rounds 1 --yes --json >"$temporary"
  command_status=$?

  if /usr/bin/python3 - "$temporary" "$host" <<'PY'
import json
import sys

path, host = sys.argv[1:]
try:
    payload = json.load(open(path, encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    raise SystemExit(f"{host}: invalid nctl result: {exc}")

actions = [
    action
    for round_result in payload.get("data", {}).get("rounds", [])
    for action in round_result.get("actions", [])
    if action.get("reconciler_id") == "observe_node"
]
if not actions or any(action.get("target_slugs") != [host] or action.get("success") is not True for action in actions):
    raise SystemExit(f"{host}: observation action did not succeed")

failed_actions = [
    action
    for round_result in payload.get("data", {}).get("rounds", [])
    for action in round_result.get("actions", [])
    if action.get("success") is not True
]
if failed_actions:
    raise SystemExit(f"{host}: reconcile action failed")

# max_rounds_reached is expected when one bounded round refreshed evidence but
# the host still has manual/out-of-scope drift.
unexpected = [
    error for error in payload.get("errors", [])
    if error.get("code") != "max_rounds_reached"
]
if unexpected:
    raise SystemExit(f"{host}: unexpected nctl errors: {unexpected}")
PY
  then
    mv "$temporary" "$result"
    rm -f "$failed"
    print "$host: refreshed (nctl exit $command_status)"
  else
    mv "$temporary" "$failed" 2>/dev/null || true
    print -u2 "$host: refresh failed (nctl exit $command_status)"
    failures=$((failures + 1))
  fi
done

exit "$failures"
