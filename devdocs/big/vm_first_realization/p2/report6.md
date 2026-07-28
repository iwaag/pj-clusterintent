# Phase 2 — Step 6 report: deployed writer

Status: **complete**.

The operator pushed `nintent` commit `0eae8a0985f9c0cb66c4c0065055592dde3c9110`.
The Docker pin was advanced to that SHA, all Nautobot services were rebuilt with
`--no-cache` and recreated, and `build_info.json` plus the image label both
equal the pushed SHA. The seed pin remained `nauto` `1c78af8…`. Both compute
collections returned HTTP 200 using the configured API token. No seed change
or Proxmox mutation occurred.
