#!/usr/bin/env bash
# Start the dedicated, loopback-only OpenCode instance for the cluster-agent.
#
# Isolated from any node-agent OpenCode instance: its own port, its own
# XDG_CONFIG_HOME/XDG_DATA_HOME under .local/cagent/ (gitignored local
# runtime state, not committed), and its own instructions file
# (cagent/opencode/AGENTS.md). Working directory is the superproject root so
# `uv run --project nctl nctl ...` resolves the same way it does for a human
# session.
#
# Instructions are fixed at process start, not per session: sessions created
# by an already-running instance keep the AGENTS.md loaded at startup, so
# restart this script after editing AGENTS.md, before testing. See
# devdocs/vision/file_output/report4.md (first-attempt timeout on stale
# instructions).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PORT="${CAGENT_OPENCODE_PORT:-4097}"
RUNTIME_DIR="$REPO_ROOT/.local/cagent"
CONFIG_DIR="$RUNTIME_DIR/config"
DATA_DIR="$RUNTIME_DIR/data"
OPENAI_KEY_FILE="${CAGENT_OPENAI_API_KEY_FILE:-$RUNTIME_DIR/openai_api_key}"

mkdir -p "$CONFIG_DIR/opencode" "$DATA_DIR"

# OpenCode's built-in OpenAI provider reads OPENAI_API_KEY. Prefer an
# explicitly supplied environment variable; otherwise read the cluster-agent
# specific, gitignored key file. Never put this key in the rendered config,
# request evidence, or Git. Refuse to start rather than silently falling back
# to the former local Ollama model.
if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  if [[ -r "$OPENAI_KEY_FILE" ]]; then
    export OPENAI_API_KEY
    OPENAI_API_KEY="$(<"$OPENAI_KEY_FILE")"
  else
    echo "OpenAI authentication is required: set OPENAI_API_KEY or create $OPENAI_KEY_FILE (mode 0600)." >&2
    exit 2
  fi
fi

# The backend model is configuration, not identity (devpolicy/policy.md,
# Agent ≠ Model): CAGENT_OPENCODE_MODEL selects it, and the default below is
# the only place the choice is written down. Switching it needs a restart of
# this script — instructions and model are both fixed at process start.
MODEL="${CAGENT_OPENCODE_MODEL:-openai/gpt-5.6-luna}"

# Render the committed template with an absolute path to AGENTS.md — a
# relative "AGENTS.md" resolves against the session's working directory,
# not the config directory, and a missing instructions file makes OpenCode
# hang a turn forever (no completion, no error). See p1/report2.md.
sed -e "s#__AGENTS_PATH__#$SCRIPT_DIR/AGENTS.md#" \
    -e "s#__MODEL__#$MODEL#" \
  "$SCRIPT_DIR/config.json.template" > "$CONFIG_DIR/opencode/opencode.json"

# opencode's tool-execution environment does not inherit the launching
# shell's PATH; without this, `uv` (and other Homebrew-installed tools)
# are not found by the bash tool. See p1/opencode_api_notes.md.
export PATH="/opt/homebrew/bin:$HOME/.local/bin:$PATH"
export XDG_CONFIG_HOME="$CONFIG_DIR"
export XDG_DATA_HOME="$DATA_DIR"

cd "$REPO_ROOT"
echo "cluster-agent OpenCode: config=$CONFIG_DIR data=$DATA_DIR port=$PORT model=$MODEL" >&2
exec opencode serve --hostname 127.0.0.1 --port "$PORT" --print-logs
