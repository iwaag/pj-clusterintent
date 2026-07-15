# Phase 3 Report — Step 1 (dashboard renderer)

Date: 2026-07-16. Implements [p3/plan.md](plan.md) Step 1. nctl commit: `p3s1`.

## What was built

`nctl_core/dashboard/` — the pure renderer:

- `html.py` — `render_dashboard_html(envelope: Envelope[DriftData]) -> str`. Python's only
  job is embedding the envelope JSON safely into the template; it performs no fetch and no
  drift computation (plan Decision 1). Embedding hardening: `json.dumps(..., ensure_ascii=True)`
  keeps U+2028/U+2029 escaped, and every `</` is rewritten to the equivalent JSON escape
  `<\/` so no payload string (e.g. a hostile `</script>` inside a diff message) can close the
  `<script type="application/json" id="nctl-drift">` block early.
- `template.html` — one self-contained page (inline CSS + vanilla inline JS, no external
  assets, works as a `file://` open). All layout/interaction is client-side JS reading the
  embedded envelope — one rendering code path, per the Phase 0 "text is a rendering of the
  JSON" convention. Contents as planned:
  - header strip: `generated_at`, status count chips, severity count chips;
  - target tiles (native `<details>`, so click-to-expand needs no JS state): kind label,
    slug/name, status word, diff count; expanded body lists each diff's severity badge,
    `code`, prose `message`, `desired`/`actual` evidence (rendered via `textContent`/`<pre>`,
    never innerHTML of payload strings), and `sources`;
  - tile order: nodes first, then services, then open-set kinds; the sort is stable so the
    engine's deterministic order is preserved within a kind;
  - sources footer: fetch timestamp, observed dump count, dump errors;
  - failed-run rendering: an `ok: false` envelope shows a "drift run failed" panel with the
    envelope errors instead of silently presenting empty/stale greens.

Colors follow plan Decision 5: green = `converged`, yellow = `converging`, red = `drifting`,
gray = `unknown`.

## Tests

`tests/test_dashboard_html.py`, 5 tests:

- embedded JSON round-trips exactly (extract script block → parse → equals `envelope.to_json()`);
- a hostile `</script>` in a diff message survives only as `<\/script>` — no literal
  `</script` inside the embedded block;
- a failed envelope still renders, with its errors embedded and the error panel present;
- self-containment: no `http(s)://`, no `src=`, no stylesheet links; style and script inline;
- CSS classes exist for all four statuses (tile and chip variants).

Full nctl suite after the step: **241 passed** (236 from Phase 2 + 5 new).
