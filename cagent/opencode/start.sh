#!/usr/bin/env bash
# Start the dedicated, loopback-only OpenCode instance for the cluster-agent.
#
# Isolated from any node-agent OpenCode instance: its own port, its own
# XDG_CONFIG_HOME/XDG_DATA_HOME under .local/cagent/ (gitignored local
# runtime state, not committed), and its own instructions file
# (cagent/opencode/AGENTS.md). Working directory is the superproject root so
# `uv run --project nctl nctl ...` resolves the same way it does for a human
# session.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PORT="${CAGENT_OPENCODE_PORT:-4097}"
RUNTIME_DIR="$REPO_ROOT/.local/cagent"
CONFIG_DIR="$RUNTIME_DIR/config"
DATA_DIR="$RUNTIME_DIR/data"

mkdir -p "$CONFIG_DIR/opencode" "$DATA_DIR"

# Render the committed template with an absolute path to AGENTS.md — a
# relative "AGENTS.md" resolves against the session's working directory,
# not the config directory, and a missing instructions file makes OpenCode
# hang a turn forever (no completion, no error). See p1/report2.md.
sed "s#__AGENTS_PATH__#$SCRIPT_DIR/AGENTS.md#" \
  "$SCRIPT_DIR/config.json.template" > "$CONFIG_DIR/opencode/opencode.json"

# opencode's tool-execution environment does not inherit the launching
# shell's PATH; without this, `uv` (and other Homebrew-installed tools)
# are not found by the bash tool. See p1/opencode_api_notes.md.
export PATH="/opt/homebrew/bin:$HOME/.local/bin:$PATH"
export XDG_CONFIG_HOME="$CONFIG_DIR"
export XDG_DATA_HOME="$DATA_DIR"

cd "$REPO_ROOT"
echo "cluster-agent OpenCode: config=$CONFIG_DIR data=$DATA_DIR port=$PORT" >&2
exec opencode serve --hostname 127.0.0.1 --port "$PORT" --print-logs
