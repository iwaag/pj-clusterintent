# nctl Modularization Phase 2 Report

Status: complete.

Phase 2 separated compute source-domain policy from GraphQL transport into
the pure `nctl_core.compute` package, reduced actual source handling to
allowlisted fact decoding, and split Braindump into REST transport, operations,
error vocabulary, and presentation. Code-only Braindump, lifecycle, and
session subclasses were folded into code-carrying base errors; public envelope
codes, messages, details, and CLI exit behavior were retained.

The full offline matrix passed, including nctl (970), compute conformance,
nintent Django-free (236 with 14 expected skips), nauto (110), nodeutils (54),
Ansible helper (4), privileged helper (1), and OpenSSH/Ansible conformance
(3). Runtime tests passed 299/299 in both clean (48.522s) and keepdb
(49.324s) modes. The named prose-authority and post-mutation-evidence runtime
boundaries passed.

The user explicitly authorized the one required nintent change: its runtime
test now imports Braindump envelope builders from `nctl_core.braindump_render`
rather than the superseded operations module. No compatibility re-export was
added. Compute remains inert, and Phase 3 retains responsibility for executor
action seams and reconcile/SSH error families.
