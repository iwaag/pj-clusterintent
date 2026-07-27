# P0 Step 0 — tuple freeze

Status: complete.

- Evidence root: `.local/nctl-modularization/p0/20260727T141512Z/` (directories `0700`, files `0600`).
- Frozen tuple: superproject `46ff7c17bc80b6701e4e82be403f25f345e3d887`; `nctl` `55f1a4bad9baffc998203a5003eee1cbcc005462`; `nintent` `055496d3e28d2ea6536f660a3ae352b8594279f3`; `nauto` `6dab422a725a2e2e4e24e98079e992d1111c0ef1`; `nodeutils` `775ed7fad5110a96186a737147b87d3bf450ced2`; `ansible_agdev` `66b31c89986d1b2ecfa187a72209d8bd96838fd4`.
- Status: all submodules clean; the only superproject untracked path was this planned P0 documentation directory.
- Recorded: governing inputs, branch/upstream/submodule tuple, environment versions, and SHA-256 set for 194 tracked Python files in `nctl` and `nintent`.
- Deviation: host `pytest` is not installed and Python 3.14's `unittest` has no `--version`; suite commands use their prescribed project environments in later steps.
