FROM networktocode/nautobot:3.1.3-py3.12

ARG NINTENT_BRANCH=main

RUN pip show nautobot | grep "^Version: " | sed -e 's/Version: /nautobot==/' > /tmp/constraints.txt && \
    pip install --no-cache-dir -c /tmp/constraints.txt "git+https://github.com/iwaag/nintent.git@${NINTENT_BRANCH}"

RUN python3 -c "\
import json, importlib.metadata as m; \
info = json.loads(m.distribution('nautobot-intent-catalog').read_text('direct_url.json')); \
commit = info.get('vcs_info', {}).get('commit_id', 'unknown'); \
open('/opt/nautobot/build_info.json', 'w').write(f'{{\"nintent_commit\": \"{commit}\"}}\n')"
