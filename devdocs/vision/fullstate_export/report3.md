# Report — Step 3: bundle composition — optional `actual_detail.json`

Status: complete (2026-08-06)

## Changes ([nctl/docs/state-bundle.md](../../../nctl/docs/state-bundle.md))

- Canonical layout now lists an optional fifth payload file,
  `actual_detail.json`, produced by `nctl actual --json --detail`, with a
  paragraph stating: it is listed in `manifest.json` `contents` like the other
  files with its `schema` read from its own envelope header; a bundle without
  it remains valid, so the bundle schema stays **`nctl.bundle.v1`** (the
  manifest is already per-file self-describing). The size caveat is recorded:
  composers may prefer host-scoped detail files
  (`nctl actual HOST --json --detail`) on large clusters.
- Recipe gains the optional detail command line with a reminder to add its
  manifest entry.
- The `actual.json` layout annotation was corrected from `nctl.actual.v1` to
  `nctl.actual.v2` (Step 1 schema bump), and "the four read commands" wording
  adjusted to "four required views, plus optional detail".

No code changes in this step; verification of the whole set follows in
Step 4.
