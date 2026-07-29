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

Completed against the pushed nintent commit `5743c6a`.

- The Dockerfile now pins that exact commit; the rebuilt image's `build_info.json` confirms it.
- The initial migration attempt detected a pre-existing number collision with
  `0016_remove_reconciliation_dashboard_surfaces`. Added and deployed merge migration
  `0017_merge_20260729_1945`; all nintent migrations are applied.
- `Import Intent Sources` completed successfully as preview, apply, and final no-op preview
  (JobResults: `7df8f1d1`, `9cd13611`, and `1e14fca2`, respectively).
- A fresh nctl GraphQL desired-state read confirms agfixture primary endpoint:
  `ip_address=192.168.0.9/24`, `gateway_address=192.168.0.1`, `ip_policy=static`.

No existing LXC was recreated or changed.
