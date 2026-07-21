# Step 2.7 — Document the public workflow and review the complete diff

Status: complete.

## 1. Documentation added

- `nctl/README.md`: a new `### braindump` section covering all seven commands, exact authorship
  meaning (no default, required on `create`), file/literal rules (`--file` reads
  `errors="strict"` UTF-8 exactly, no trimming/normalization/interpretation), create-or-replace
  review behavior (replace refreshes `last_updated` even for identical text; a create/create race
  is recovered automatically), destructive-confirmation behavior (`--yes`/interactive prompt/
  `--json` requiring `--yes`), and the three-state attention semantics. States explicitly the safe
  external-agent interaction sequence from plan.md Step 2.7: read `list`/`show --json`, read `nctl
  drift --json` separately for desired/actual evidence, ask the user about ambiguity, write only
  confirmed user words to a Braindump, publish AI prose via `review`, and use established
  desired-state/`reconcile` commands separately only after explicit user authority. The `Usage`
  code block gained one example line per command.
- `nctl/docs/output-format.md`: a `## nctl.braindump.*.v1` section with the three shared nested
  shapes, a table of all seven schemas' `data` fields, one full JSON example
  (`nctl.braindump.review.v1`), the error-code-to-exit-code mapping, and a note that
  `review_conflict` is a reserved but currently-unemitted code (the bounded race recovery resolves
  every uniqueness conflict internally).
- `nctl/docs/compatibility.md`: the seven new schemas added to the frozen `data`-model table,
  pointing at their `nctl_core.braindump` model classes.

All three documentation files use only synthetic example prose ("Home lab", "Keep Ollama on
agpc.") — no token, no real cluster data.

## 2. Full diff review (`f211c9e..HEAD`, the whole Phase 2 nctl diff)

```
git diff f211c9ec70c02141b8180f95132c7541a9b00cc1..HEAD --stat
 README.md                             |  63 +++
 docs/compatibility.md                 |   7 +
 docs/output-format.md                 |  72 +++
 src/nctl_core/braindump.py            | 858 ++++++
 src/nctl_core/cli/main.py             | 206 ++++
 src/nctl_core/nautobot.py             |  22 +-
 src/nctl_core/sources/braindump.py    | 139 ++++
 tests/test_braindump.py               | 688 +++++
 tests/test_cli_braindump.py           | 624 +++++
 tests/test_compatibility_snapshots.py |  19 +
 tests/test_nautobot.py                | 113 +++
 tests/test_sources_braindump.py       | 304 ++++
 12 files changed, 3113 insertions(+), 2 deletions(-)
```

Checked for each of the required concerns:

- **Aliases**: `grep -n "braindump_app.command"` shows exactly the seven frozen command names, no
  `edit`/`set`/plural/old-name alias.
- **Prose parsing**: no code in `braindump.py`/`sources/braindump.py` inspects `body`/`summary`
  content beyond `.strip()` (used only to test emptiness before the original string is sent to
  REST unchanged).
- **Hidden defaults**: `--authorship` has no default value on `create` (`typer.Option` required,
  no `= AuthorshipChoice.user_direct`); `update`'s optional authorship defaults to `None`, meaning
  "no change," never a value.
- **Source-snapshot coupling**: `grep -rn "SourceSnapshot\|serve\b\|llm\|LLM\|prompt\b\|scheduler\|
  webhook\|Job\b" src/nctl_core/braindump.py src/nctl_core/sources/braindump.py` — no output.
  `SourceSnapshot`, drift comparators/registry, reconcile classification, dashboard, `serve`, Jobs,
  and Ansible rendering remain untouched by this feature (also verified per-step in Steps
  2.2/2.3/2.4/2.5/2.6's isolation checks).
- **LLM/model dependencies**: none — no new dependency was added to `pyproject.toml`; the feature
  is REST/GraphQL plumbing only.
- **`serve` routes**: no route was added to `nctl_core/serve/`; the CLI is the only surface.
- **Secret/private-text logging**: `grep -n "token" src/nctl_core/braindump.py` shows the token
  flows only into `NautobotClient(cfg.nautobot.url, token)`; every error class truncates any server
  response text to 200 characters and never includes the token, the full request body, or
  arbitrary stored Braindump/review prose.

## 3. Local commit

`nctl` commit `d33c58e0a238b8113115800c523cffc2a002b7ae` (heads/main, local only — not pushed; per
`.local/localenv_memo.md` and this project's established convention, pushing is the user's own
step). The full Phase 2 nctl test suite is green at this commit (733 passed, Step 2.6's report).

## Discrepancies

None. The one previously noted item (`review_conflict` reserved but unemitted) is now documented in
`docs/output-format.md` rather than left implicit. Proceeding to Step 2.8, which requires the user's
explicit go-ahead before any live synthetic CRUD against the running Nautobot instance.
