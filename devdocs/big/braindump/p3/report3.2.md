# Step 3.2 — Exercise the direct named-host case in one AI-mediated interaction

Status: complete.

## 1. Braindump and review

- Braindump: `3049fd77-253a-4ca4-a062-864e34a303ac`
- Title: `クラスターPCとサービス配置の希望`
- Authorship: `user_direct`
- Review: `bbd8f745-53f6-416b-a4a6-1b9d4cbe1a16`

The supplied source was stored byte-for-byte through the Phase 2 file-input path. The initial
Alignment Review was created in the same interaction after reading all staged Braindumps and current
desired/actual/drift evidence. Later evidence from Step 3.4 replaced the review in the same review
row; no review-history row was created.

## 2. Grounding result

- `agstudio` and `agpc` are active desired nodes with the user-described reserved addresses and mDNS
  endpoints.
- The desired catalog contains no Ollama/Qwen service or placement. The review therefore does not
  claim that the named workload is implemented or managed.
- The actual observations for both hosts were stale. The review treats hardware/workload assertions
  from the user as Braindump context, not current actual-state facts.
- The review asks for the bounded decisions required before a future structured service proposal:
  availability semantics, model/version policy, deployment-profile ownership, network exposure, and
  whether the placement is fixed or conditional.

## 3. Safety boundary

No DesiredService, DesiredServicePlacement, DNS/DHCP intent, lifecycle, Ansible service action, or
host deployment was written by creating or reviewing this diary row.

## Discrepancies

None for the direct named-host review. The later inability to refresh `agpc` actual state is recorded
in `report3.4.md` and reflected by an in-place review replacement.
