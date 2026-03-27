from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse, urlunparse


class UnsafeURLError(ValueError):
    pass


ALLOWED_SCHEMES = {"http", "https"}


def normalize_url(raw_url: str) -> str:
    candidate = raw_url.strip()
    if "://" not in candidate:
        candidate = f"https://{candidate}"
    parsed = urlparse(candidate)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise UnsafeURLError("Unsupported URL scheme.")
    if not parsed.netloc:
        raise UnsafeURLError("Invalid URL.")
    hostname = parsed.hostname or ""
    if not hostname:
        raise UnsafeURLError("Invalid hostname.")
    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        fragment="",
        path=parsed.path or "/",
    )
    return urlunparse(normalized)


def canonical_domain(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def ensure_public_url(url: str) -> None:
    parsed = urlparse(url)
    host = parsed.hostname
    if not host:
        raise UnsafeURLError("Missing hostname.")
    if host in {"localhost"} or host.endswith(".local"):
        raise UnsafeURLError("Localhost targets are not allowed.")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)}
    except socket.gaierror as exc:
        raise UnsafeURLError(f"Unable to resolve host: {host}") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise UnsafeURLError("Private or non-public network targets are not allowed.")

