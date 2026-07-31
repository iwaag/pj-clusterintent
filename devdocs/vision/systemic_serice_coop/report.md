# Report: Systemic LLM Provider Cooperation

## Implemented

- Added a pure `nctl` service-dependency resolver for active `node_agent`
  placements with `config.llm_provider_service`. It resolves exactly one
  active provider placement and endpoint, produces
  `nintent_opencode_ollama_url`, and records consumer/provider/endpoint
  provenance in the production report.
- Resolver failures are classified, node-local drift errors: missing,
  ambiguous, invalid, or unusable provider endpoints no longer become an
  OpenCode timeout.
- Added `llm_provider_service` as a required `node_agent` placement config
  field. The OpenCode playbook consumes only the nctl-generated URL and
  rejects an unresolved provider. The old tracked host mapping was removed;
  an ignored local override has an example file only.
- Added the `ollama` deployment profile as an observed provider profile.
- Extended nodeutils to observe a hinted Ollama provider through its macOS
  launchd label, process name, or bounded local HTTP health probe. Probe hints
  now include a placement's declared service endpoint.

## Desired State Applied to Scratch Nautobot

The confirmed batch in `.local/systemic-service-coop.yaml` created:

- the active `ollama` DesiredService;
- `agstudio`'s `ollama-api` service endpoint (`http`, port `11434`);
- the active `ollama-agstudio` placement; and
- `llm_provider_service: ollama` on the `aghub` and `agstudio` node-agent
  placements.

The batch preview was `3 create / 2 update / 0 conflict`, then committed with
the same counts.

## Verification

- `uv run --project nctl pytest -q nctl/tests` — **1040 passed**.
- `uv run --project nodeutils python -m unittest discover -s nodeutils/tests`
  — **59 passed**.
- `ansible-inventory` validation and `setup_opencode.yml --syntax-check` —
  passed.
- Production inventory for `aghub` resolved the generated OpenCode URL from
  the `ollama-agstudio` desired placement.
- Applied the limited `aghub` node-agent playbook. It updated OpenCode config
  and restarted the agent successfully.
- `nctl agent run aghub --prompt 'Reply with exactly: OK'` completed with
  `OK`, proving the consumer uses a reachable provider endpoint.

## Remaining Drift

`aghub` is converged, including service-dependency provenance. `ollama` still
reports `service_missing` after fresh `agstudio` observations. The new probe
configuration is deployed and contains the declared endpoint, but the
agstudio-local collector did not record a successful launchd, process, or HTTP
probe even though the node-agent request succeeded. This is an accurate
unresolved actual-state observation, not an endpoint-resolution failure.

The last observation operation was `01KYW9KPSMJ1574HWC157WBG9S`; it completed
collection and inventory regeneration but correctly stopped as
`manual_intervention_required` for the unsupported provider-observation gap.
Future work should identify the local Ollama process/API exposure as seen from
`agstudio`'s collector and adjust only that probe, then rerun
`nctl reconcile agstudio --refresh-observation --yes`.

## Follow-up Diagnosis (2026-07-31)

Direct read-only checks on `agstudio` established the immediate cause:

- Ollama is healthy (`ollama serve`, launchd label `homebrew.mxcl.ollama`, and
  a listener on port 11434); both loopback API endpoints return HTTP 200.
- `agstudio.home.arpa` does not resolve on `agstudio` itself. The original
  nodeutils HTTP probe used that client-facing DNS name, so it could not
  observe its own provider even though consumers could use it.

The follow-up initially added a generated local-loopback probe endpoint as a
fallback. After the resolver cache was flushed and normal `home.arpa`
resolution recovered, that fallback was removed: observation now uses the
same client-facing endpoint as consumers.
However, `playbooks/nautobot/run_nodeutils_collect.yml` clones nodeutils from
GitHub into `/opt/nodeutils`; it cannot use an unpushed local nodeutils commit.
The remote collector was confirmed to lack the new probe function. Push the
new nodeutils commits, then rerun the `agstudio` refresh observation. This is
expected to register `ollama` as an active `http_probe` service and converge
the remaining drift.
