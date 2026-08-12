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

import hmac

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
    node URI SAN. The node listener's TLS context is CERT_OPTIONAL, not
    CERT_REQUIRED (main.py's `_build_node_ssl_context`) — so the
    no-cert case is a real, reachable path in production (an unenrolled
    node hitting any route other than `GET /llms.txt`), not just a
    defense-in-depth check against a hypothetical misconfiguration. A
    presented cert is still fully chain-verified by the TLS layer before
    the handler ever runs; only "no cert at all" reaches this branch.
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


class TokenAuthenticator:
    """Human entrance authenticator (p4/contract.md): the human listener has
    no client cert (server-only TLS), so identity comes from a single
    static bearer token instead. Constant-time comparison
    (`hmac.compare_digest`) — this is the only production credential check
    that isn't a certificate chain, so it must not be vulnerable to a
    timing side-channel the TLS layer wouldn't otherwise expose."""

    def __init__(self, token: str, human_name: str = "operator") -> None:
        self._token = token
        self._human_name = human_name

    def __call__(self, handler) -> Identity:
        header = handler.headers.get("Authorization", "")
        prefix = "Bearer "
        if not header.startswith(prefix):
            raise AuthError(401, "unauthorized", "missing bearer token")
        provided = header[len(prefix):]
        if not hmac.compare_digest(provided, self._token):
            raise AuthError(401, "unauthorized", "invalid token")
        return Identity(identity_class="human", name=self._human_name)


class NoAuthenticator:
    """The window entrance: no credential of any kind, by design.

    The window is deliberately weaker than the authenticated entrances — its
    OpenCode instance can run read-only `nctl` and the incident script and
    nothing else — and that permission set, not an identity check, is what
    makes an anonymous door acceptable. Everything it accepts is recorded in
    evidence under one shared `window` identity, so there is a run record per
    answer even though there is no caller to name."""

    def __init__(self, name: str = "window") -> None:
        self._name = name

    def __call__(self, handler) -> Identity:
        return Identity(identity_class="window", name=self._name)
