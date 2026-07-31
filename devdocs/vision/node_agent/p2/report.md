# Node Agent — Phase 2 Report

Status: complete (2026-07-31).

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
playbooks/agent/setup_opencode.yml --syntax-check` passed, both before and
after the live validation fixes. The committed role also passed `git show
--check`. `ansible-lint` is not installed in the local development environment,
so that optional check could not run.

## Step 3 — Dry review

`ansible-playbook -i inventories/generated/hosts_intent.yml
playbooks/agent/setup_opencode.yml --check --diff --limit agstudio` passed.
It predicted only the configuration directory mode and configuration template
changes. In check mode, the role deliberately skips download, service, and
health operations because those tasks rely on a real temporary staging
directory and system service state; this is an optional diagnostic, not the
operation's dry-run authority.

## Step 4 — agstudio adoption

The live run against `agstudio` adopted the existing macOS installation. It
updated the configuration directory mode, `opencode.json`, and the LaunchAgent,
then used `launchctl kickstart -k` to restart the service. The `/doc` health
endpoint returned 200 after one retry. An immediate rerun reported
`changed=0`.

## Step 5 — agpc fresh deployment and attach proof

Before deployment, `agpc` successfully queried the existing agstudio Ollama
OpenAI-compatible `/v1/models` endpoint and found the selected model. Thus no
Ollama bind-address change and no additional LAN exposure were needed.
`vars/opencode_agent.yml` records the non-secret `agpc` endpoint as
`http://agstudio.local:11434/v1`; agstudio retains the default loopback URL.

The first `agpc` run exposed a role defect: the archive extraction directory
was not created. The failure removed its private staging directory and had not
yet configured the node. After adding that directory creation, a second run
downloaded and SHA-256-verified the Linux x86_64 archive, installed OpenCode,
enabled lingering for `eiji`, installed and started the systemd user service,
and passed the `/doc` health check after one retry. Its immediate rerun
reported `changed=0`.

For both nodes, the controller opened an SSH loopback forward and launched the
native `opencode attach` client against the remote service. The TUI rendered
for the expected remote working directory. A native `opencode run --attach`
verification then had the selected model create `phase2-attach-proof.txt` and
run `pwd` through its shell tool:

| Node | Working directory | Result |
|---|---|---|
| agstudio | `/Users/eiji/agent-work` | file write and `pwd` passed |
| agpc | `/home/eiji/agent-work` | file write and `pwd` passed |

## Limitations carried to Phase 3

- The OpenCode service remains loopback-only and currently has no HTTP
  password; controller access is through SSH local forwarding.
- `opencode attach` remains the runtime-native TUI path. Phase 3 should wrap
  its tunnel/session invocation in `nctl` rather than reimplement the
  protocol.
- The Phase 1 finding remains: TUI Ctrl-C exits the local client but does not
  reliably interrupt the remote task. A future abort command must call the
  OpenCode interrupt API.
