# Advice for Adding a Future Compute Provider

The VM-platform roadmap intentionally implements Proxmox only. Do not add AWS, Azure, or a
nominally generic provider to nintent until there is a concrete cluster use case that can be
followed from desired state through fresh actual observation and reconciliation.

When another provider is needed:

1. Start from one real resource to create or reconcile. Record the provider's stable identity,
   fresh actual-state source, minimum desired choices, and safe actuator before changing the
   shared models.
2. Reuse an existing common field only when its semantics and units genuinely match. Keep
   provider concepts such as an AWS instance type or Azure resource group in a strict,
   versioned provider schema rather than forcing them into a misleading Proxmox-shaped
   abstraction.
3. Add only fields with a named drift, planning, actuation, or safe-identification consumer.
   Do not mirror the provider API, SDK, or every configuration option into nintent.
4. Treat a field as common only after at least two implemented providers show the same intent
   semantics. Similar spelling is not sufficient.
5. Keep credentials and executable connection details outside nintent. Desired state should
   refer to a stable non-secret platform identity that nctl or Ansible configuration resolves
   to the approved adapter and secret.
6. Build the actual-state adapter and freshness contract before claiming convergence. Provider
   inventory cached without an observation time must not be treated as current.
7. Preserve provider-specific safety rules. Create, resize, stop, replace, move, and delete are
   separate capabilities and need separate plans, evidence, and tests; support for one must not
   imply support for the others.
8. Extend mixed-provider tests so one provider's unavailable credential, malformed payload, or
   bad target remains correctly scoped and does not block unrelated platforms or nodes.

Prefer a small shared platform/instance envelope plus a closed provider-specific schema over
either extreme: duplicated end-to-end provider models or one unrestricted generic JSON bag.
