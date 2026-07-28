# Phase 4 Step 3 Report

Status: **complete**.

Implemented `waiting_for_manual_initial_access`. It is emitted only when the compute instance links to a running observed LXC, the desired node has no realized Device, and no nodeutils observation exists for that node. Production composition excludes the node using that explicit reason, and the initial compute-create planner cannot re-plan it because the compute instance is linked.

Focused tests cover the positive predicate and each of the four negated conditions; removing any condition restores ordinary `no_realized_object` behavior where applicable.
