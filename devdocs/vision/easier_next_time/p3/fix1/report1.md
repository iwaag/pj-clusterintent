# Fix 1 — Step 1 report: fix the batch example and strengthen the skill precondition

Status: **complete**.

## What was done

`nctl/README.md` §"Retiring one Proxmox LXC": added `dry_run: true` as the
first field of the canonical retirement document. The two operations are
unchanged.

`.claude/skills/retire-proxmox-lxc/SKILL.md`:

- added `dry_run: true` to the embedded retirement YAML;
- bumped `version: 1` → `2` (executor behavior changes: a new precondition
  and two new stop branches);
- replaced `prerequisites: [existing_desired_node]` with
  `prerequisites: [existing_realized_compute_instance]`, and added a
  prerequisite paragraph before Step 1 stating the guest's Proxmox
  realization must already be observed/ingested/linked in a **prior
  session** — this skill does not create, observe, or link a VM;
- added `compute_instance_missing` and a link-only/zero-destroy-action plan
  to the `manual_review` branch table as explicit **precondition failures**
  (stop, return to a human/capable model) — no recovery commands were added,
  per the plan's instruction not to turn the skill into a
  creation/observation-recovery/linking runbook;
- added the same two conditions to the "Stop conditions" list;
- kept `last_verified` and `verified_against` at `null`, and updated the
  "Unverified" note to point at `fix1/plan.md` Step 5/6 instead of the
  superseded `p3/plan.md` Step 2/3.

## Static checks performed

1. Parsed the skill frontmatter as YAML — valid, `version: 2`,
   `prerequisites: [existing_realized_compute_instance]`,
   `last_verified`/`verified_against` still `null`.
2. Extracted and parsed both retirement YAML examples (SKILL.md and
   `nctl/README.md`) — each has exactly `dry_run` and `operations`, with
   `dry_run: true`. (Script and output kept in this report; not a persisted
   test file, since this is a doc/skill static check, not a code test.)
3. Diffed the skill body: the "Permitted commands" list and every `--yes`
   "STOP — user approval required" line are unchanged from `version: 1` —
   confirmed by inspection, only the frontmatter, the prerequisite note, the
   embedded YAML, and the branch/stop-condition tables changed.
4. The skill already appears in this session's available-skills listing
   (`retire-proxmox-lxc: Retire one Proxmox LXC guest ...`), confirming a
   fresh listing still exposes its name and description after the edit.

## Verification script

```python
import re, yaml

text = open(".claude/skills/retire-proxmox-lxc/SKILL.md").read()
fm = yaml.safe_load(re.match(r"^---\n(.*?)\n---\n", text, re.S).group(1))

def check_envelope(doc_text, label):
    doc = yaml.safe_load(doc_text)
    assert set(doc.keys()) == {"dry_run", "operations"}
    assert doc["dry_run"] is True
    print(f"{label}: OK")

retirement_block = [b for b in re.findall(r"```yaml\n(.*?)```", text, re.S) if "desired_node" in b][0]
check_envelope(retirement_block, "SKILL.md retirement example")

readme_text = open("nctl/README.md").read()
m2 = re.search(r"### Retiring one Proxmox LXC.*?```yaml\n(.*?)```", readme_text, re.S)
check_envelope(m2.group(1), "nctl/README.md retirement example")
```

Output: frontmatter OK; both retirement examples OK.

## Commit

This documentation/skill correction is committed before any cluster work, per
the plan.

## Next

Step 2: repair the host-scoped observation contract in `nctl` (the
`--refresh-observation aghub` widening into `agpc`/`agstudio`), with focused
regression tests. No cluster contact in that step either.
