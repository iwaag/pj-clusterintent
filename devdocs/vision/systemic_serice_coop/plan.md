# Plan: Systemic LLM Provider Cooperation

## Goal

Make an OpenCode node-agent consume an active cluster Ollama service selected
from Nautobot desired state, rather than relying on a per-host Ansible mapping
or an implicit `127.0.0.1:11434` fallback.

The normal flow becomes:

```text
Braindump -> reviewed decision -> desired-state batch
  -> nctl resolves provider endpoint -> generated Ansible inventory
  -> Ansible deploys/configures services -> nodeutils observes them
  -> nctl drift verifies the result
```

Braindumps remain conversational input and audit context. They must not
silently mutate desired state; the existing explicit desired-state apply path
remains the sole desired-state writer.

## Scope and Model

Represent the provider and its consumers independently:

- `DesiredService(ollama)` expresses that cluster inference is desired.
- An active `DesiredServicePlacement` selects the node running it, e.g.
  `agstudio`, and references a `DesiredEndpoint` containing the address, port,
  and protocol used by clients.
- A node-agent placement declares a dependency on `ollama`; it does not embed
  a host name or URL.

Use the placement `config` field for the first implementation, for example a
node-agent config containing `llm_provider_service: ollama`. Add a dedicated
dependency model only when the generic configuration becomes ambiguous or
needs multiple providers, priorities, or richer policy.

Keep provider-specific settings separated: the endpoint belongs to the
provider placement; OpenCode model selection and agent-specific settings
belong to the node-agent placement/configuration.

## Implementation Steps

1. **Declare the initial intent.**
   Add `ollama` and its active `agstudio` placement through the canonical
   desired-state batch API. Reference the existing desired endpoint and give
   it the API port/path needed by OpenCode. Declare the node-agent's provider
   dependency in its placement config. Do not use a Braindump as an implicit
   writer; record the decision there, review it, then apply the exact batch.

2. **Define a small nctl resolver.**
   In `nctl_core`, resolve a consumer's named provider service to exactly one
   active placement and its usable desired endpoint. Produce a normalized URL
   (including `/v1` for Ollama/OpenAI compatibility). Return useful classified
   errors for no active provider, no endpoint, unusable endpoint, or ambiguous
   provider selection. Keep selection deterministic; a simple explicit
   `primary: true` config flag is sufficient if multiple placements are
   needed.

3. **Project resolved dependencies into production inventory.**
   Extend the production adapter/composer so a node-agent host receives a
   generated host variable such as `nintent_opencode_ollama_url`. Preserve
   provenance in the production report: consumer placement, provider service,
   provider placement, and endpoint IDs. Generated inventory is already an
   ignored local artifact and is the appropriate place for local topology.

4. **Make Ansible consume the generated variable.**
   Remove the static `opencode_agent_ollama_urls` mapping and its `vars_files`
   dependency from `playbooks/agent/setup_opencode.yml`. Pass the generated
   variable to the role. For managed node-agent hosts, missing resolution must
   fail during inventory rendering or playbook preflight rather than silently
   using loopback. Retain a clearly explicit local-loopback option only if it
   remains useful for a deliberate standalone experiment.

5. **Actuate and observe the provider.**
   Add or connect an Ollama deployment profile/role so an active Ollama
   placement installs and starts the provider on its selected node. Extend
   nodeutils' service observation with the facts required to establish that
   Ollama is present and reachable at its declared endpoint. Reuse the
   existing `observed_services` actual-state channel rather than adding a
   parallel ledger.

6. **Reconcile service and dependency drift.**
   Extend service drift so it reports an unsatisfied provider placement and an
   unresolved node-agent dependency before `nctl agent run` can time out.
   Verify the complete flow with `nctl reconcile <provider>` followed by
   `nctl reconcile <consumer> --yes`, then run a short `nctl agent run` prompt
   against the consumer.

## Migration and Repository Hygiene

- Treat the current `ansible_agdev/vars/opencode_agent.yml` mapping as a
  short-lived compatibility input, not a source of truth. Once generated
  inventory supplies the value, remove it from the tracked configuration.
- If a local override is still needed, commit only an
  `opencode_agent.yml.example`; ignore the real override file. Adding an
  ignore rule alone does not untrack an existing file.
- Local DNS names and addresses are usually topology data rather than secrets,
  but keeping them in the Nautobot scratch DB and ignored generated inventory
  avoids publishing unnecessary details. Secrets, if any, stay in `.local/`;
  do not put credentials in service placement config or inventory.
- This is an experimental scratch environment. It is acceptable to apply
  migrations, rebuild Nautobot, and create test records as needed. Avoid only
  unreviewed operations against real cluster infrastructure and irreversible
  broad cleanup.

## Acceptance Criteria

- Adding a new node-agent with an `ollama` dependency needs no host-specific
  Ansible edit.
- The generated host vars contain the endpoint resolved from the active
  desired provider placement, with report provenance.
- Missing or ambiguous provider intent is reported before agent prompting.
- The provider is observed through the normal actual-service pipeline and
  service/dependency drift converges after reconciliation.
- No real local topology mapping remains in tracked public Ansible variables.
