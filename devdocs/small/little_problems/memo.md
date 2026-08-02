# Minor Problems Memo

## Tight Coupling and Hardcoding Issue in nodeutils Service Endpoint Probing

In `nodeutils/nodeutils_collect.py`, the `probe_service_endpoint` function, which evaluates service status via HTTP probing, exhibits the following issues:

- Health check paths and evaluation logic specific to individual services are hardcoded directly within `nodeutils_collect.py` (e.g., `if service_name == "ollama":` or `if service_name in ("swarmui", "comfyui"):`).
- As the number of monitored services increases, additional `if` conditional branches must be continually appended to a single collector script (`nodeutils_collect.py`), causing script bloat, tight coupling, and degraded maintainability and extensibility.
