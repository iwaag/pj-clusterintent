"""mTLS identity extraction + connect-time checks (p2/contract.md).

`CertAuthenticator` is the production `authenticate` callable
`server.make_handler` calls per request. It is the only place that reads
`getpeercert()`; everything downstream (store, evidence) just sees a
`store.Identity`. Tests inject a different `authenticate` callable
entirely (see `tests/fakes.py`) so unit tests never need a real TLS
handshake — only the Step 5a conformance test exercises this class against
a real socket.

Check order matches contract.md exactly: TLS handshake already happened by
the time this runs (proven by `getpeercert()` returning a verified cert at
all — an unverified/expired/untrusted cert never reaches here, the
handshake itself fails first). This class only does step 2 (ledger) and
step 3 (DesiredNode validity).
"""

from __future__ import annotations

from .ledger import Ledger
from .node_resolver import NodeResolverError
from .store import Identity

NODE_URN_PREFIX = "urn:clusterintent:node:"


class AuthError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def extract_node_identity(peercert: dict | None) -> tuple[str, str]:
    """Return (node_uuid, cert_serial_lowercase_hex) from a verified peer cert.

    Raises AuthError if no cert was presented or it carries no clusterintent
    node URI SAN. In production this should be unreachable — the TLS
    context requires and verifies a client cert before the handler ever
    runs — but the check stays here rather than being assumed, since a
    misconfigured `verify_mode` should fail loudly, not authenticate as
    nothing.
    """
    if not peercert:
        raise AuthError(401, "unauthorized", "no client certificate presented")

    serial = peercert.get("serialNumber")
    if not serial:
        raise AuthError(401, "unauthorized", "client certificate has no serial number")

    for san_type, value in peercert.get("subjectAltName", ()):
        if san_type == "URI" and value.startswith(NODE_URN_PREFIX):
            node_uuid = value[len(NODE_URN_PREFIX):]
            return node_uuid, serial.lower()

    raise AuthError(401, "unauthorized", "client certificate has no clusterintent node URI SAN")


class CertAuthenticator:
    def __init__(self, ledger: Ledger, node_resolver) -> None:
        self._ledger = ledger
        self._node_resolver = node_resolver

    def __call__(self, handler) -> Identity:
        peercert = handler.connection.getpeercert()
        node_uuid, cert_serial = extract_node_identity(peercert)

        entry = self._ledger.get(cert_serial)
        if entry is None or entry.state != "active":
            raise AuthError(403, "forbidden", "certificate not registered or revoked")

        try:
            valid = self._node_resolver.is_valid(node_uuid)
        except NodeResolverError as exc:
            raise AuthError(502, "nautobot_unavailable", str(exc)) from exc
        if not valid:
            raise AuthError(403, "forbidden", "DesiredNode no longer exists or is not active")

        return Identity(identity_class="node", uuid=node_uuid, cert_serial=cert_serial)
