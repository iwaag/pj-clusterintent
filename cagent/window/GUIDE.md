# cluster-agent — window guide

The capability card the window answers from. Re-read from disk on every
request: edit it and the next answer changes, no restart. Served raw at
`GET /guide` on the window port.

## What this is

The cluster-agent's unauthenticated door. Ask it about this cluster's desired
and actual state — status, drift, relations, past operations, "is X really
up" — and **report it when one of its answers turns out to be wrong**. That
report is the reason this door exists.

## Reporting a wrong answer or a defect

Just say it, in your own words: "you told me node X was up, it is not". The
window records the report as a file and replies with where it went. It will
not try to repair anything in that turn, and it will not argue: recording
comes first, diagnosis is a separate, human-triggered step.

Records live under `.local/cagent/incidents/` on the command node, one file
per report, containing your wording verbatim plus who/where/when. Ask "what
has been reported lately" to see the recent ones.

## Doors

- `POST /window` `{"text": "..."}` — this window, the only conversational
  door here. Answers `202 {"request_id", "session_id", "state"}`; poll
  `GET /requests/{request_id}` until `state` is `completed` and read
  `response`. States: `queued | running | completed | failed | cancelled |
  interrupted`.
- `GET /guide` — this file, raw.
- `GET /healthz` — `{"ok": true}`.

The Cagent bot in Zulip is the same door: a direct message to it becomes one
`POST /window`.

## What it can do, and what it cannot

Can: read-only `nctl` — `status`, `drift`, `relations`, `actual`, `ops list`,
`ops show` — read files in the repository, and record incidents.

Cannot: change anything. `reconcile`, `desired apply`, `apply`, `prune`,
`lifecycle`, Ansible, SSH and every file write are simply not among this
door's tools — there is no shell here at all — so a request for a change
comes back as a refusal naming what *is* available, however it is phrased.
That is the safety story here: the tool set, not a promise in prose.

Cluster changes go through the authenticated entrances instead — the human
entrance's chat UI, or the node entrance with a client certificate. Their
capability card is `GET /llms.txt` on those ports.

## What it costs

Every message costs a real model turn. `GET /requests/{request_id}` carries
`cost_usd` for the turn, and `backend` naming the role, profile, harness,
provider and model that served it — those are the live numbers, the ones
below are measurements, not quotes.

- **Money: `cost_usd` is `null` on the default backend.** The window runs on
  a local model behind an endpoint that charges nothing and reports nothing,
  so the field says "not measured" rather than claiming the turn was free.
  If this door is moved onto a paid backend, that backend's own figure
  appears there instead — read `backend` rather than assuming.
- Time: a few seconds for a single read or a recorded report; a
  multi-command answer can take minutes. Poll, do not block on a short
  timeout.
- Cluster side effects: none. This door cannot cause any.
