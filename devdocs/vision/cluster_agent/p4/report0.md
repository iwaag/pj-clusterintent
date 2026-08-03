# Step 0 report — Contract delta + reachability facts

## Contract

`p4/contract.md` frozen: second HTTPS listener (`:8789`, server-only TLS,
no client cert) guarded by a static bearer token
(`CAGENT_HUMAN_TOKEN_FILE`, default `~/.local/state/cagent/human_token`);
`Identity` reworked to a class-tagged shape (`{"class": "node", "uuid",
"cert_serial"}` / `{"class": "human", "name"}`) with a derived
`owner_key()` (`"node:<uuid>"` / constant `"human"`); human sessions rule
is list-all/read-all, continue-own; UI routes live only on the human
listener; polling only, no SSE, per the plan's explicit recommendation.
Full text in `p4/contract.md`.

## Reachability facts (live, command node = agstudio)

- `hostname`: `agstudio.home.arpa` (LAN name, unrelated to the tailnet).
- `tailscale status`: agstudio is on the tailnet at `100.94.61.95`.
  `iphone181` (the phone) is enrolled but showed `offline, last seen 65d
  ago` at check time — expected, not required for Step 0-3 (only Step 4
  needs it actually reachable).
- `tailscale status --json` → `CurrentTailnet.MagicDNSEnabled: true`,
  `MagicDNSSuffix: tailab7641.ts.net`.
- `dscacheutil -q host -a name agstudio` resolves to
  `agstudio.tailab7641.ts.net` → `100.94.61.95`; `ping agstudio` round-trips
  in <1ms against the same address. Confirms the MagicDNS search-domain
  mechanism resolves the bare hostname `agstudio` — the same mechanism
  will apply on the phone once it reconnects to the tailnet, per Tailscale's
  documented behavior (every enrolled device shares the same MagicDNS
  config). Expected human URL: **`https://agstudio:8789`**.
- Current server cert (`.local/cagent-ca/server_cert.pem`): SANs are
  `DNS:agstudio.local, IP Address:192.168.0.100` exactly as the plan
  anticipated — bare `agstudio` is **not** covered. `notAfter=2027-08-02`.
  Re-issue with an added `--dns agstudio` SAN is deferred to Step 1 (local
  proof) / re-verified in Step 4, per the contract.
- `.local/cagent-ca/` and `~/.local/state/cagent/{evidence,ledger}` already
  exist and are populated from prior phases (evidence has 18 entries, an
  archived p1 evidence dir, and a ledger dir) — nothing to initialize here.

## Deviations from the plan

None. `report0.md`'s job (per the plan) was the contract + the one live
fact it hangs on; both done without surprises.

## State

No code changed this step. No processes started or stopped.

## Next

Step 1 — `TokenAuthenticator`, the second listener in `main.py`, the
`Identity`/evidence rework in `store.py`, ownership rules in `server.py`,
and unit tests via the fake-authenticate seam.
