# Step 2 Report — APT observation prerequisite

Status: complete.

The existing `ansible_agdev/roles/git_client` APT repair was retained and covered:

- `Refresh APT package cache before installing Git` runs only for
  `ansible_pkg_mgr == "apt"`, precedes the generic package installation, and uses
  `cache_valid_time: 3600`.
- Generic `ansible.builtin.package` installation remains unchanged for all Linux package managers.
- Added two role contract tests covering ordering/cache bounds and the non-APT guard. The bounded
  cache interval is the role's repeat-run/idempotency condition: a valid cache makes the APT task
  unchanged rather than refreshing it again.

Verification, from `ansible_agdev`:

```text
python3 -m unittest discover -s roles/git_client/tests  -> 2 passed
ansible-playbook --syntax-check playbooks/nautobot/run_nodeutils_collect.yml -> passed
```

No SSH, guest package installation, or external target was contacted.

