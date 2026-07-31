# Node Agent — Phase 3 Report

Status: complete (2026-07-31).

## Command surface

`nctl` now owns the interactive entry point instead of requiring operators to
remember an SSH forwarding command and an OpenCode URL:

```sh
nctl agent status HOST [--json]
nctl agent attach HOST [--session SESSION_ID]
```

`status` resolves `HOST` only as an exact `DesiredNode.slug`, reads the
desired snapshot, requires that node's UUID-derived alias to be enrolled in
the managed SSH store, opens a temporary loopback forward, and probes the
node-local `GET /doc` endpoint. It records an `agent status` operation event
log and emits the `nctl.agent.status.v1` envelope. An unknown name returns the
structured `unknown_host` error; an unenrolled node directs the operator to
`nctl ssh enroll <slug> ...`.

`attach` uses the same resolution and trust path, opens an ephemeral local
port, and runs the controller-local native client with its inherited terminal:

```text
opencode attach http://127.0.0.1:<ephemeral-port> --dir <remote-workdir> [--session ID]
```

The child exit code is returned by `nctl`; the tunnel is terminated and waited
for in the enclosing context. No endpoint, port, or alternate host is accepted
from the command line.

## Controlled configuration

The optional `[agent]` section has controller-owned values only:

```toml
[agent]
port = 4096
ssh_user = "eiji"
identity_file = "~/.ssh/ansible_key"
macos_workdir = "/Users/eiji/agent-work"
linux_workdir = "/home/eiji/agent-work"

[agent.workdir_by_slug]
agstudio = "/Users/eiji/agent-work"
agpc = "/home/eiji/agent-work"
```

The explicit identity file plus `IdentitiesOnly=yes` avoids unrelated keys in
the controller SSH agent causing authentication failures. The SSH command also
sets `HostKeyAlias`, `UserKnownHostsFile`, and `StrictHostKeyChecking=yes` from
the existing nctl trust contract. No credentials or key material are printed.

## Verification

Local tests cover exact slug failure, enrollment enforcement, closed SSH
arguments, tunnel teardown, native attach command construction and exit-code
propagation, status-envelope rendering, configuration, and CLI exits. The
complete nctl suite passed:

```text
1022 passed
```

Live verification used the configured managed key and the desired snapshot:

| Check | Result |
|---|---|
| `nctl agent status agstudio --json` | HTTP 200 through the temporary forward; operation `01KYW0MSFWH7P648A1SRM94WC6`; macOS workdir resolved. |
| `nctl agent status agpc --json` | HTTP 200 through the temporary forward; operation `01KYW0MT3ASFA42P29J58HQ739`; Linux workdir resolved. |
| Unknown slug | `nctl agent status no-such-node --json` returned `unknown_host`, operation `01KYW0MTTT3BR5GQ3EVD2SM8JJ`. |
| Native TUI | `nctl agent attach agstudio` opened OpenCode 1.18.10 with the selected Ollama model and `/Users/eiji/agent-work`. |
| Model and resume | Through the same nctl-managed tunnel, native OpenCode returned the expected no-tool response from agstudio and, on agpc, appended the expected response to existing session `ses_048032980ffewkvz6U06YkJJ6P`; both response markers were verified via the node-local session API. |
| Tunnel cleanup | The real native client runs completed with no matching temporary SSH process. The automated terminal harness force-terminated one interactive TUI attempt and left its child tunnel; the exact validated child PIDs were immediately stopped. This was harness termination rather than a native client exit; normal teardown is covered by the attach lifecycle test and the live native-client runs. |

## Carried limitation

As found in Phase 1, Ctrl-C in the OpenCode TUI exits the local client but does
not reliably interrupt the remote task. Phase 5 must implement deliberate
abort through OpenCode's session interrupt API; Phase 3 intentionally does not
simulate it.
