FROM networktocode/nautobot:3.1.3-py3.12

# Exact revision tuple frozen by devdocs/big/nctl_modularization/p1/plan.md Section 3.4.
# Bump these two ARG defaults (and only these) when the plan's frozen tuple changes; do
# not install a mutable branch head.
ARG NINTENT_COMMIT=78f05e4d29e772ec16c6f55263ea69f5ece38d3f
ARG NAUTO_COMMIT=1c78af8bdbfc69cafdc293b4082f866de9f271b0

RUN test -n "$NINTENT_COMMIT" || (echo "NINTENT_COMMIT build arg is required" >&2 && exit 1)

RUN pip show nautobot | grep "^Version: " | sed -e 's/Version: /nautobot==/' > /tmp/constraints.txt && \
    pip install -c /tmp/constraints.txt "git+https://github.com/iwaag/nintent.git@${NINTENT_COMMIT}"

# Fail the build if pip resolved a different commit than requested (e.g. a moved/retagged ref).
RUN python3 -c "\
import json, importlib.metadata as m, sys; \
info = json.loads(m.distribution('nautobot-intent-catalog').read_text('direct_url.json')); \
commit = info.get('vcs_info', {}).get('commit_id'); \
expected = '${NINTENT_COMMIT}'; \
sys.exit(0) if commit == expected else sys.exit(f'installed commit {commit!r} != requested {expected!r}')"

# The exact nauto commit's canonical YAML, baked in read-only at one explicit path shared by
# web, worker, and scheduler (all three run this same image). Build context is the superproject
# root so this path resolves through the nauto submodule checkout.
COPY nauto/seed/intent_sources.yaml /opt/nautobot/intent_sources.yaml
RUN sha256sum /opt/nautobot/intent_sources.yaml > /opt/nautobot/intent_sources.yaml.sha256

RUN printf '{"nintent_commit": "%s", "nauto_commit": "%s"}\n' "$NINTENT_COMMIT" "$NAUTO_COMMIT" > /opt/nautobot/build_info.json

LABEL org.clusterintent.nintent-commit="${NINTENT_COMMIT}"
LABEL org.clusterintent.nauto-commit="${NAUTO_COMMIT}"
