# Node Agent — Phase 1 Findings Report

Status: complete (2026-07-31).

## Selected runtime

The spike selected **OpenCode 1.18.10**.  It was the shortest path to the
required shape: `opencode serve` provides a headless HTTP server and the
native `opencode attach` TUI can attach to it and resume an existing session.
It also accepts the existing Ollama endpoint through an OpenAI-compatible
provider configuration.  The pinned macOS ARM64 release archive was verified
against its published SHA-256 before installation:

```text
v1.18.10 / opencode-darwin-arm64.zip
641fe2e65e42db76c2d32db5f85573c3682a8c72f82d01568a922a8feccc4658
```

Goose and Pi remain plausible alternatives, but were not installed: OpenCode
already met the remote-TUI and server requirements, so switching would not
have added useful evidence in this spike.

## Target and installation

The selected node is `agstudio.local`, which is macOS 26.2 on Apple Silicon,
not Linux as the initial plan wording had assumed.  The runtime runs as the
existing `eiji` user.  Its working directory is `/Users/eiji/agent-work`.

On both the node and controller, the installed binary is
`~/.local/bin/opencode`.  The node install was:

```sh
curl -fsSL https://github.com/anomalyco/opencode/releases/download/v1.18.10/opencode-darwin-arm64.zip -o "$stage/opencode-darwin-arm64.zip"
echo '641fe2e65e42db76c2d32db5f85573c3682a8c72f82d01568a922a8feccc4658  '"$stage"'/opencode-darwin-arm64.zip' | shasum -a 256 -c -
unzip -q "$stage/opencode-darwin-arm64.zip" -d "$stage/unpack"
install -m 0755 "$stage/unpack/opencode" ~/.local/bin/opencode
```

The node configuration is `~/.config/opencode/opencode.json`.  Its material
shape is:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "ollama/qwen3.6:35b-a3b-coding-nvfp4",
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "options": { "baseURL": "http://127.0.0.1:11434/v1" },
      "models": {
        "qwen3.6:35b-a3b-coding-nvfp4": {}
      }
    }
  }
}
```

The persistent service is a per-user `launchd` job, because the target is
macOS:

```text
~/Library/LaunchAgents/com.clusterintent.opencode.agent.plist
Program: ~/.local/bin/opencode serve --hostname 127.0.0.1 --port 4096
WorkingDirectory: ~/agent-work
RunAtLoad: true
KeepAlive: true
```

It is loaded with:

```sh
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.clusterintent.opencode.agent.plist
```

The server binds only to loopback.  It intentionally has no HTTP password:
the current operator path reaches it only through SSH local forwarding, so it
is not exposed to the LAN or an untrusted network.

## Ollama and model

Ollama is co-located on `agstudio.local` at `http://127.0.0.1:11434`.
The selected model is `qwen3.6:35b-a3b-coding-nvfp4`, already verified before
this phase as tool-capable.  In this spike it completed the file and shell
probes in approximately 4--8 seconds per short request.  It correctly used
the working directory, created `NOTES.md`, edited it across resumed sessions,
and reported the `pwd` result.  No replacement model was needed.

## Operator attach command

Create the protected transport from the controller (once per login):

```sh
ssh -fN -i ~/.ssh/ansible_key -o ExitOnForwardFailure=yes \
  -L 14096:127.0.0.1:4096 eiji@agstudio.local
```

Then open or resume a session without opening an interactive SSH shell:

```sh
~/.local/bin/opencode attach http://127.0.0.1:14096 \
  --dir /Users/eiji/agent-work --session SESSION_ID
```

For the spike session, `SESSION_ID` was `ses_048189e4fffe9JJMtDO9zZN75A`.
The service stores sessions on the node; do not treat this example ID as a
stable configuration value.

## Interaction results

| Check | Result | Evidence / limitation |
|---|---|---|
| Attach to a new interactive session | passed | Native TUI attached through the loopback SSH tunnel and displayed the configured model/provider. |
| Read, write, and edit files | passed | The agent created `NOTES.md`, then edited it to add `Shell verified.` and, after restart, `Restart resumed.` |
| Run shell commands | passed | The agent ran `pwd` and reported `/Users/eiji/agent-work`. |
| Detach and re-attach with context | passed | A controller TUI attached to the existing session and displayed its earlier history; later prompts retained the same session context. |
| Cancel / interrupt generation | mixed | `POST /api/session/SESSION_ID/interrupt` returned 204 and prevented the scheduled post-sleep write. TUI Ctrl-C exited the local TUI but did **not** cancel the remote task; its delayed write still occurred. Phase 3 must map a deliberate abort command to the server interrupt API rather than relying on TUI Ctrl-C. |
| Service restart and session continuation | passed | `launchctl kickstart -k gui/$(id -u)/com.clusterintent.opencode.agent` restarted the server. The original session remained addressable and successfully performed the third edit. |
| Terminal behavior | partial | ANSI colors and normal full-screen TUI rendering worked. Ctrl-C has the limitation above. Automated terminal resize and TUI process exit-status propagation were not conclusively exercised, so they remain manual acceptance checks for Phase 2/3. |

The temporary cancellation probe file was removed after observing the TUI
Ctrl-C limitation.  The useful `NOTES.md` spike artifact remains in
`~/agent-work`.

## Implications for Phase 2

The Ansible role should install the exact OpenCode macOS ARM64 release (or
choose the architecture-specific pinned archive), verify its SHA-256, create
`~/.local/bin/opencode`, and template the configuration and the `launchd`
plist above.  It should ensure `~/agent-work` exists, bootstrap or kickstart
the user service, and health-check `http://127.0.0.1:4096/doc` from the node.
On Linux targets, use a systemd user unit with the same command and loopback
binding instead of copying the macOS plist.

The role must also template the Ollama base URL and default model rather than
hard-coding them.  LAN binding should require an explicit password and a
separate security decision; the successful Phase 1 default is loopback plus
SSH forwarding.

## Implications for Phase 3

`nctl agent attach HOST` can resolve the node and invoke the two-command
workflow above (or manage an equivalent tunnel) before executing the native
OpenCode TUI.  It needs a session option that passes `--session`.  A future
noninteractive `abort` action should call OpenCode's session interrupt API,
not simulate Ctrl-C in the attached terminal.

The old `/api/session/.../prompt` endpoint accepted a prompt but did not offer
an execution wait operation in this version.  This did not affect TUI use,
but Phase 5 should use the current `/session/{id}/message`,
`/prompt_async`, and `/api/session/{id}/interrupt` endpoints after pinning and
testing the exact OpenCode version.
