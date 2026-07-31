# Node Agent — Phase 2 Report

Status: in progress (2026-07-31).

## Step 1 — Role and playbook implementation

Added `ansible_agdev/roles/opencode_agent` and
`playbooks/agent/setup_opencode.yml`. The role pins OpenCode `v1.18.10`,
downloads an architecture-specific release asset into a private staging
directory, and verifies it with the release SHA-256 supplied to Ansible's
`get_url` before unpacking and installing `~/.local/bin/opencode`.

Pinned asset digests:

| Platform | Asset | SHA-256 |
|---|---|---|
| macOS arm64 | `opencode-darwin-arm64.zip` | `641fe2e65e42db76c2d32db5f85573c3682a8c72f82d01568a922a8feccc4658` |
| macOS x86_64 | `opencode-darwin-x64.zip` | `b2d9e161b3c6f398ab8a21a129455550c7b79b68579bb542dbc986f10b084ae4` |
| Linux x86_64 | `opencode-linux-x64.tar.gz` | `6b1113da704253fb4da12b41e4236acecb9f2b62949c945f6eeacaa15111b976` |
| Linux arm64 | `opencode-linux-arm64.tar.gz` | `41ae3041e91b894e4c0dc06a73a9a2796254bf390ffb99626a43af5e2912d170` |

The default configuration uses loopback `127.0.0.1:4096`, working directory
`~/agent-work`, Ollama endpoint `http://127.0.0.1:11434/v1`, and model
`qwen3.6:35b-a3b-coding-nvfp4`. All are role variables. macOS uses a user
LaunchAgent and Linux uses a lingering systemd user service. Changes to the
binary, configuration, or unit/plist notify a restart; a health check polls
`/doc` after handlers are applied. The playbook requires an explicit
`--limit`, preventing accidental deployment to every generated SSH host.

## Step 2 — Static verification

`ansible-playbook -i inventories/generated/hosts_intent.yml
playbooks/agent/setup_opencode.yml --syntax-check` passed. `git diff --check`
also passed. `ansible-lint` is not installed in the local development
environment, so that optional check could not run.

## Step 3 — Dry review

Not run yet. The environment instructions require explicit user confirmation
before any SSH access, including an Ansible check-mode run.
