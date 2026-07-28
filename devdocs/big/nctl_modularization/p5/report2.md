# P5 Step 2 — Responsibility map

Status: complete.

- Replaced the README Layout stub with a responsibility map for all seven required packages and every post-Step-1 module at or above roughly 300 lines.
- Each entry states its owner, permitted dependency direction, and prohibited layer/concern. The map includes the new node and endpoint evaluators rather than preserving the obsolete `drift/evaluation.py` monolith as the owner.
- A mechanical existence check resolved all 29 named package/module paths. No runtime or observable contract changed.

