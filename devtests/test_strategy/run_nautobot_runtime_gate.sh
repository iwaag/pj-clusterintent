#!/usr/bin/env bash
# Run the exact-local-source Nautobot App gate without using deployed packages or credentials.
set -euo pipefail

usage() {
  printf 'usage: %s [--keepdb|--clean] [test-label]\n' "$0" >&2
}

mode=keepdb
if [[ ${1:-} == --keepdb || ${1:-} == --clean ]]; then
  mode=${1#--}
  shift
fi
if (($# > 1)); then
  usage
  exit 2
fi
label=${1:-nautobot_intent_catalog}

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)
container=nautobot-nautobot-1
postgres_container=my_postgres_db
stage=/tmp/test-strategy-nautobot-runtime-$$
deps_stage=$stage/deps

for path in "$root/nintent" "$root/nauto" "$root/nctl" "$root/nodeutils"; do
  [[ -d $path ]] || { printf 'missing checkout path: %s\n' "$path" >&2; exit 2; }
done
docker inspect --format '{{.State.Running}}' "$container" | grep -qx true || {
  printf 'required Nautobot container is not running: %s\n' "$container" >&2
  exit 2
}
docker inspect --format '{{.State.Running}}' "$postgres_container" | grep -qx true || {
  printf 'required PostgreSQL container is not running: %s\n' "$postgres_container" >&2
  exit 2
}

drop_test_database() {
  # test_nautobot is test-owned; no persistent Nautobot database is changed.
  docker exec "$postgres_container" psql -U nautobot -d nautobot -v ON_ERROR_STOP=1 \
    -c 'DROP DATABASE IF EXISTS test_nautobot WITH (FORCE);'
}

# All gate invocations share the one test-owned database. Two concurrent runs would migrate it at
# the same time and fail with an already-existing column, so refuse to start beside another run.
running_runtime_tests=$(docker exec "$container" sh -c \
  'for entry in /proc/[0-9]*/cmdline; do tr "\0" " " < "$entry" 2>/dev/null; echo; done' \
  | grep -c 'nautobot-server test ' || true)
if ((running_runtime_tests > 0)); then
  printf 'another Nautobot runtime test is already running in %s; refusing to share test_nautobot\n' \
    "$container" >&2
  exit 2
fi

# Set once the run has reached its test body, which proves the database was built completely. Until
# then any exit — setup failure, timeout, or interrupt — must remove the test database, because a
# half-migrated test_nautobot silently poisons every later --keepdb run with an already-existing
# column, and the column it stops on moves with however far the abandoned run got.
database_built=0
cleanup() {
  docker exec --user root "$container" rm -rf -- "$stage" >/dev/null 2>&1 || true
  if ((database_built == 0)); then
    printf 'runtime gate did not reach its test body; dropping the test-owned database\n' >&2
    drop_test_database >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

if [[ $mode == clean ]]; then
  drop_test_database
fi

docker exec "$container" mkdir -p "$deps_stage"
docker cp "$root/nintent/." "$container:$stage/nintent"
docker cp "$root/nauto/." "$container:$stage/nauto"
docker cp "$root/nctl/." "$container:$stage/nctl"
docker cp "$root/nodeutils/." "$container:$stage/nodeutils"

# The Nautobot image deliberately lacks nctl's HTTP client stack. These are pure-Python packages
# copied from nctl's locked local environment into the test-owned stage, never installed globally.
for dependency in httpx httpcore anyio h11; do
  dependency_path=$(cd "$root/nctl" && uv run python -c "import $dependency, pathlib; print(pathlib.Path($dependency.__file__).parent)")
  docker cp "$dependency_path" "$container:$deps_stage/"
done

source_revision() { git -C "$1" rev-parse HEAD; }
source_digest() { git -C "$1" ls-files -s | shasum -a 256 | awk '{print $1}'; }
printf 'runtime gate mode=%s label=%s\n' "$mode" "$label"
for component in nintent nauto nctl nodeutils; do
  printf 'source %s revision=%s tracked-index-digest=%s\n' \
    "$component" "$(source_revision "$root/$component")" "$(source_digest "$root/$component")"
done

runtime_python="import nautobot_intent_catalog, jobs, nctl_core, nodeutils_collect; \
expected = '$stage'; \
modules = (nautobot_intent_catalog, jobs, nctl_core, nodeutils_collect); \
[print(module.__name__, module.__file__) for module in modules]; \
assert all(module.__file__.startswith(expected) for module in modules), 'installed module resolved instead of staged checkout'"
docker exec -e "PYTHONPATH=$stage/nintent:$stage/nauto:$stage/nctl/src:$stage/nodeutils:$deps_stage" \
  -e NAUTOBOT_TOKEN= -e GITHUB_TOKEN= "$container" nautobot-server shell --command "$runtime_python"

docker exec -e "PYTHONPATH=$stage/nintent:$stage/nauto:$stage/nctl/src:$stage/nodeutils:$deps_stage" \
  -e NAUTOBOT_TOKEN= -e GITHUB_TOKEN= "$container" \
  nautobot-server makemigrations --check --dry-run
docker exec -e "PYTHONPATH=$stage/nintent:$stage/nauto:$stage/nctl/src:$stage/nodeutils:$deps_stage" \
  -e NAUTOBOT_TOKEN= -e GITHUB_TOKEN= -e RUNTIME_STAGE="$stage" "$container" \
  sh -c 'nautobot-server test "$@" --keepdb -v 1 > "$RUNTIME_STAGE/test-output.log" 2>&1; result=$?; printf "%s\n" "$result" > "$RUNTIME_STAGE/test-exit-status"; exit 0' \
  test-runner "$label"
result=$(docker exec "$container" cat "$stage/test-exit-status")
output=$(docker exec "$container" cat "$stage/test-output.log")
printf '%s\n' "$output"

# A stated case count means the runner finished database setup, so the test database is coherent
# even when the cases themselves failed. A run that never touched a test database cannot have
# damaged one either. Only setup that started and did not finish poisons reuse.
cases=$(printf '%s\n' "$output" | sed -n 's/^Ran \([0-9][0-9]*\) tests\{0,1\} in .*/\1/p' | tail -1)
if [[ -n $cases ]] || ! printf '%s\n' "$output" | grep -q 'test database for alias'; then
  database_built=1
fi

if [[ $result != 0 ]]; then
  printf 'Nautobot runtime test failed with exit status %s\n' "$result" >&2
  exit "$result"
fi

# Django exits 0 when a label resolves to nothing, so a green status alone is not a proof. Require
# a stated case count; a gate that ran zero cases has verified nothing.
if [[ -z $cases ]] || ((cases < 1)); then
  printf 'Nautobot runtime gate collected no test case for label %s\n' "$label" >&2
  exit 3
fi
printf 'runtime gate result mode=%s label=%s cases=%s\n' "$mode" "$label" "$cases"
