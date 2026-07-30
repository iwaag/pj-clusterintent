FROM networktocode/nautobot:3.1.3-py3.12

# Exact revision tuple frozen by devdocs/big/nctl_modularization/p1/plan.md Section 3.4.
# Bump these two ARG defaults (and only these) when the plan's frozen tuple changes; do
# not install a mutable branch head.
ARG NINTENT_COMMIT=8ea7d4842c5fa778249ffb304668838fee9550f1
ARG NAUTO_COMMIT=6462ebcbd9b8033853b60473dbe7f18d400cdd0b

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

RUN printf '{"nintent_commit": "%s", "nauto_commit": "%s"}\n' "$NINTENT_COMMIT" "$NAUTO_COMMIT" > /opt/nautobot/build_info.json

LABEL org.clusterintent.nintent-commit="${NINTENT_COMMIT}"
LABEL org.clusterintent.nauto-commit="${NAUTO_COMMIT}"
