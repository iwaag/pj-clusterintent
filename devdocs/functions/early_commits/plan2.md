# GPU Inventory Implementation Plan

## Goal

Add GPU information to the existing Nautobot self-registration flow.

The host-side `nodeutils` script should collect GPU details where possible and send a compact GPU summary to Nautobot. The Nautobot-side `nauto` seed job should create the required Device custom fields, and the AI resource review job should include GPU facts in its prompt inputs.

## Design

Keep the current inventory pattern:

- Store searchable, scheduler-friendly GPU facts as Device custom fields.
- Store detailed GPU discovery output inside `inventory_raw_json`.
- Avoid failing self-registration when GPU tools are missing or return partial data.
- Do not infer that a host has no GPU unless detection positively finds none; missing tools should simply produce no GPU fields.

## Custom Fields

Add these Device custom fields in `nauto/seed/home_cluster.yaml`:

- `gpu_count`: integer count of detected GPU devices.
- `gpu_models`: text list of detected GPU model names.
- `gpu_memory_gb`: text total detected dedicated GPU memory, when available.
- `gpu_accelerator_summary`: compact human-readable GPU summary for schedulers and AI review.

## Host Detection

Implement best-effort detection in `nodeutils/nautobot_self_register.py`:

1. Linux NVIDIA:
   - Use `nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits`.
   - Capture model name, memory MiB converted to GB, driver version, and source.
2. Linux generic fallback:
   - Use `lspci -mm`.
   - Capture VGA / 3D / Display controller names for NVIDIA, AMD, Intel, or other GPUs.
   - Avoid duplicate devices already reported by `nvidia-smi`.
3. macOS:
   - Use `system_profiler SPDisplaysDataType`.
   - Capture chipset/model names and VRAM text where present.
   - Treat Apple Silicon unified memory conservatively; do not convert it to dedicated GPU memory.

## Data Shape

Add these keys to collected inventory:

- `gpu`: detailed list and summary.
- `gpu_count`
- `gpu_models`
- `gpu_memory_gb`
- `gpu_accelerator_summary`

Add `gpu` to `inventory_raw_json`.

Add `gpu_accelerator_summary` to `ai_resource_summary`.

## AI Review

Add the GPU custom fields to `INPUT_CUSTOM_FIELDS` in `jobs/ai_resource_review.py`:

- `gpu_count`
- `gpu_models`
- `gpu_memory_gb`
- `gpu_accelerator_summary`

This makes the source hash change when GPU facts change, causing the review to regenerate once.

## Documentation

Update both README files:

- `nauto/README.md`: list the new Device custom fields.
- `nodeutils/README.md`: mention GPU collection behavior and supported detection tools.

## Verification

Run local checks:

- `uv run ruff check .` in `nodeutils`
- `uv run python -m py_compile nautobot_self_register.py` in `nodeutils`
- `python3 -m py_compile jobs/*.py` in `nauto`

Manual Nautobot verification after deployment:

1. Sync the `nauto` Git Repository.
2. Run `Seed Home Cluster` with `dry_run=false`.
3. Run `uv run --env-file .env nautobot-self-register --json` on a GPU host.
4. Confirm GPU fields and `inventory_raw_json.gpu` are populated.
5. Confirm `AI Resource Review` regenerates after GPU facts first appear.
