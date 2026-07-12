# Monitoring Memo

Prometheus/Grafana should handle live capacity and time-series monitoring, not Nautobot.

Use Nautobot for relatively stable placement and intent:

- `ollama` normally runs on `PC1`.
- `PC1` is an `ai-inference` host.
- The preferred endpoint is `http://pc1:11434`.
- The startup policy is `use_existing_first`.
- A new instance may be started only under an explicit fallback policy.

Use Prometheus/Grafana for current operational state:

- GPU utilization.
- VRAM used/free.
- CPU load.
- Memory pressure.
- Disk pressure.
- Container health.
- Ollama process health and latency if exported.
- Alerting and historical trends.

Scheduler flow:

1. Ask Nautobot where a service should normally be used.
2. Check Prometheus or another monitoring API for live capacity and health.
3. Use the existing endpoint when it is healthy and has enough room.
4. Fall back or start a new service only when policy and capacity checks both allow it.

Short version: Nautobot answers "where should this run?" Prometheus answers "is it safe to use right now?"
