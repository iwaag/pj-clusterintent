#!/usr/bin/env python3
"""Launcher for the Cagent bot's Zulip listener (`cagent_api.zulip_window`).

    uv run --project cagent cagent/service/zulip_listener.py

Credentials: `.local/zulip/cagent.env`. Set `CAGENT_ZULIP_LOG_ONLY=1` to watch
DMs without spending a window turn on them.
"""

from cagent_api.zulip_window import main


if __name__ == "__main__":
    main()
