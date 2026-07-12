FROM networktocode/nautobot:3.1.3-py3.12
RUN pip show nautobot | grep "^Version: " | sed -e 's/Version: /nautobot==/' > /tmp/constraints.txt && \
    pip install -c /tmp/constraints.txt git+https://github.com/iwaag/nprojects.git