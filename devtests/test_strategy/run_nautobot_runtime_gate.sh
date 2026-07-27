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

cleanup() {
  docker exec --user root "$container" rm -rf -- "$stage" >/dev/null 2>&1 || true
}
trap cleanup EXIT

if [[ $mode == clean ]]; then
  # test_nautobot is test-owned; no persistent Nautobot database is changed.
  docker exec "$postgres_container" psql -U nautobot -d nautobot -v ON_ERROR_STOP=1 \
    -c 'DROP DATABASE IF EXISTS test_nautobot WITH (FORCE);'
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
docker exec -d -e "PYTHONPATH=$stage/nintent:$stage/nauto:$stage/nctl/src:$stage/nodeutils:$deps_stage" \
  -e NAUTOBOT_TOKEN= -e GITHUB_TOKEN= -e RUNTIME_STAGE="$stage" "$container" \
  sh -c 'nautobot-server test "$@" --keepdb -v 1; result=$?; printf "%s\n" "$result" > "$RUNTIME_STAGE/test-exit-status"' \
  test-runner "$label" >/dev/null

while ! docker exec "$container" test -f "$stage/test-exit-status"; do
  sleep 1
done
result=$(docker exec "$container" cat "$stage/test-exit-status")
[[ $result == 0 ]] || { printf 'Nautobot runtime test failed with exit status %s\n' "$result" >&2; exit "$result"; }
