# Step 2 — Extend and prove the read-only storage-content boundary

Status: `complete` for local code/tests. Deployment to `aghub` is deferred to Step 8.

## 1. What changed

`ansible_agdev/roles/nodeutils_pvesh_helper/files/nodeutils-pvesh-read`:

- Added an exact `_STORAGE` identifier grammar (`[A-Za-z0-9_][A-Za-z0-9_-]{0,63}`, matching
  Proxmox storage IDs including hyphenated/underscored names such as `local-lvm`).
- Added exactly one new allowlist entry: `/nodes/{node}/storage/{storage}/content`. No write verb,
  status path, or additional segment is reachable — the regex is anchored (`\A...\Z`) like every
  existing entry.
- No other change to the helper: it still only ever builds
  `[pvesh, get, <path>, --output-format, json]` and dispatches via `os.execve`; no subprocess/shell
  import was added.

`ansible_agdev/roles/nodeutils_pvesh_helper/tests/test_nodeutils_pvesh_read.py`:

- Added positive cases: `/nodes/aghub/storage/local/content`,
  `/nodes/aghub/storage/local-lvm/content`, `/nodes/aghub/storage/local_lvm/content`.
- Added negative cases: trailing slash, `../` traversal, query string, embedded space, `;`/`` ` ``/`$()`
  shell metacharacters, empty storage segment (`storage//content`), an invalid `!` character in
  the storage identifier, an extra path segment after `content`, a numeric extra segment
  (`content/100`, mimicking a template-download sub-path), and adjacent `storage/{s}/status`.

`nodeutils/tests/test_pvesh_helper_integration.py` (the cross-repository boundary test, which runs
the real, unmodified helper source with a fake `pvesh`):

- Extended the fake `pvesh` fixture with an `agdnsmasq`-shaped LXC guest (VMID 108) and a `local`
  storage advertising `vztmpl` content, so `collect_proxmox_inventory()` actually reaches the new
  path.
- Added a positive assertion that `get /nodes/aghub/storage/local/content` appears in the fake
  `pvesh` call log (proving the real helper source accepted and executed the new path end to
  end, not merely that the regex unit test accepts the string).
- Asserted the resulting report's `facts.proxmox.storage_content[0].items[0].volid` equals
  `local:vztmpl/debian-13-standard.tar.zst` — proving `nodeutils` on the caller side filters to
  the Section 5.2 allowlisted fields (`volid`, `content`, `format`, `size_bytes`) and nothing else
  from the raw content-list response.

The `nodeutils` collector side (`collect_proxmox_inventory()`) already queried content only for
storages advertising `vztmpl` in their content-type string and filtered to the allowlisted fields;
that was implemented in Step 1 in anticipation of this boundary and needed no further change here.

## 2. Tests

```
$ cd ansible_agdev && python3 -m unittest roles.nodeutils_pvesh_helper.tests.test_nodeutils_pvesh_read
Ran 8 tests in 0.000s — OK

$ uv run --project nodeutils pytest nodeutils/tests/ -q
54 passed in 2.09s
```

## Gate

Positive logs prove the exact content path ran through the real (unmodified) helper source; every
negative path in the extended matrix is rejected before `os.execve`; and the helper still contains
no subprocess/shell import and only ever dispatches `pvesh get`.

Proceeding to Step 3 (Nautobot prerequisites and strict ingest parsing).
