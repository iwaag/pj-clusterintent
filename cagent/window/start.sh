#!/usr/bin/env bash
# Start the OpenCode instance behind the cluster-agent's unauthenticated
# window (default :4098).
#
# A second instance next to cagent/opencode/start.sh (:4097), not a second
# configuration of it: the window's whole point is a *smaller* tool
# permission set than the authenticated entrances, and OpenCode fixes both
# permissions and instructions at process start. Its own port, its own
# XDG_CONFIG_HOME/XDG_DATA_HOME under .local/cagent-window/, its own
# AGENTS.md. Working directory is the superproject root, so the commands the
# window is allowed to run resolve exactly as they are written in the guide.
#
# Edits to window/AGENTS.md and this permission set need a restart of this
# script. window/GUIDE.md does not — it is re-read from disk per request.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PORT="${CAGENT_WINDOW_OPENCODE_PORT:-4098}"
RUNTIME_DIR="$REPO_ROOT/.local/cagent-window"
CONFIG_DIR="$RUNTIME_DIR/config"
DATA_DIR="$RUNTIME_DIR/data"
OPENAI_KEY_FILE="${CAGENT_OPENAI_API_KEY_FILE:-$REPO_ROOT/.local/cagent/openai_api_key}"

mkdir -p "$CONFIG_DIR/opencode" "$DATA_DIR"

# Same refuse-don't-fallback rule as the main instance: no key, no start.
if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  if [[ -r "$OPENAI_KEY_FILE" ]]; then
    export OPENAI_API_KEY
    OPENAI_API_KEY="$(<"$OPENAI_KEY_FILE")"
  else
    echo "OpenAI authentication is required: set OPENAI_API_KEY or create $OPENAI_KEY_FILE (mode 0600)." >&2
    exit 2
  fi
fi

# Agent ≠ Model: the window's backend is a parameter, and it may differ from
# the authenticated entrances' model. Whatever it is, it ends up in the run
# record for every answer.
MODEL="${CAGENT_WINDOW_MODEL:-${CAGENT_OPENCODE_MODEL:-openai/gpt-5.6-luna}}"

sed -e "s#__AGENTS_PATH__#$SCRIPT_DIR/AGENTS.md#" \
    -e "s#__MODEL__#$MODEL#" \
  "$SCRIPT_DIR/opencode-window.json.template" > "$CONFIG_DIR/opencode/opencode.json"

# opencode's tool-execution environment does not inherit the launching
# shell's PATH; without this, `uv` is not found by the bash tool.
export PATH="/opt/homebrew/bin:$HOME/.local/bin:$PATH"
export XDG_CONFIG_HOME="$CONFIG_DIR"
export XDG_DATA_HOME="$DATA_DIR"

cd "$REPO_ROOT"
echo "cluster-agent window OpenCode: config=$CONFIG_DIR data=$DATA_DIR port=$PORT model=$MODEL" >&2
exec opencode serve --hostname 127.0.0.1 --port "$PORT" --print-logs
