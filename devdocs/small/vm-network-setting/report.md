# LXC Initial Network Configuration — Report

Date: 2026-07-29

## Result

Implemented the static IPv4 initial-network contract for LXC creation.

- `DesiredEndpoint.gateway_address` is nullable, has migration `0016`, is available through
  GraphQL, the YAML loader/importer, and the typed nctl desired source.
- Gateway-bearing endpoints require `ip_policy: static`, an IPv4 CIDR, and a usable IPv4 gateway
  in that CIDR's subnet. The shared nintent/nctl compute contract normalizes these to
  `ipv4_cidr` and `gateway_ipv4`; incomplete, IPv6, malformed, or cross-subnet values cannot make
  an active/approved compute instance creation-ready.
- The create derivation includes those exact normalized parameters. The bounded LXC adapter now
  passes `name=eth0,bridge=<bridge>,hwaddr=<mac>,ip=<ipv4_cidr>,gw=<gateway_ipv4>` to `pct create`.
- `nauto/seed/intent_sources.yaml` now gives `agfixture` `192.168.0.9/24` and gateway
  `192.168.0.1`; the nctl LXC workflow documentation now distinguishes automatic network setup
  from the remaining manual guest SSH bootstrap.

## Verification

Passed:

- `cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests` — 238 passed, 14 expected skips.
- `cd nctl && uv run pytest -q --durations=20` — 1005 passed.
- `uv run --project nctl pytest -q devtests/test_strategy/test_compute_conformance.py` — 1 passed.
- `uv run --project nctl pytest -q devtests/test_strategy/test_ansible_conformance.py` — 2 passed; fake `pct` received the complete `net0` argument.

The loader coverage includes a valid CIDR/gateway and rejects missing CIDR, another subnet,
IPv6, and malformed gateway inputs. The compute conformance fixture pins the same behavior in
nintent and nctl.

## Scratch-environment deployment

Not performed. Per `.local/localenv_memo.md`, the Nautobot image installs nintent from GitHub,
not the local checkout. Applying the migration and Import Job therefore requires committing the
nintent changes, a user-performed push, then rebuilding/restarting the Nautobot image. After that,
run the Import Job as preview, apply, and no-op repeat, and confirm the `agfixture` endpoint reads
`192.168.0.9/24` with gateway `192.168.0.1`. No existing LXC was recreated or changed.
