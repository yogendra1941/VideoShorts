"""Security hardening: SSRF guard, URL validation, and filename sanitization.

Prevents Server-Side Request Forgery (SSRF) by blocking private/link-local/loopback
IP ranges, restricts URL schemes, and sanitizes filenames to prevent path traversal
and null-byte injection.
"""

import ipaddress
import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger("VideoShorts.Security")

# RFC 1918 private ranges + link-local + loopback + reserved.
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),   # link-local
    ipaddress.ip_network("127.0.0.0/8"),       # loopback
    ipaddress.ip_network("100.64.0.0/10"),     # CGNAT shared
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("224.0.0.0/4"),       # multicast
]


def is_blocked_ip(host: str) -> bool:
    """Return True if host (IP, hostname, or dotted-quad) resolves to a blocked network."""
    if not host:
        return True
    host = host.strip().strip("[]")  # strip IPv6 brackets
    # If it's already an IP literal, check it directly.
    try:
        addr = ipaddress.ip_address(host)
        return any(addr in net for net in _BLOCKED_NETWORKS)
    except ValueError:
        pass
    # Otherwise resolve hostname. If resolution fails, be safe and block it,
    # but allow plain 'localhost'-style names only through loopback check.
    try:
        import socket
        infos = socket.getaddrinfo(host, None)
    except Exception:
        logger.warning("SSRF guard: could not resolve host %r; blocking", host)
        return True
    for info in infos:
        try:
            addr = ipaddress.ip_address(info[4][0])
        except ValueError:
            continue
        if any(addr in net for net in _BLOCKED_NETWORKS):
            return True
    return False


def validate_source_url(url: str) -> str:
    """Validate a remote ingestion URL. Returns the sanitized URL or raises ValueError.

    - Scheme must be http/https.
    - Host must not resolve to a private/link-local/loopback address.
    """
    url = (url or "").strip()
    if not url:
        raise ValueError("Empty URL")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"URL scheme '{parsed.scheme}' not allowed (http/https only)")
    if not parsed.hostname:
        raise ValueError("URL has no host")
    if is_blocked_ip(parsed.hostname):
        raise ValueError(f"URL host '{parsed.hostname}' resolves to a blocked private/local address")
    return url


SAFE_FILENAME_RE = re.compile(r"[^a-zA-Z0-9_.-]")


def sanitize_filename(filename: str) -> str:
    """Strip path traversal and unsafe characters from a user-supplied filename."""
    if not filename:
        return "clip"
    # Remove any path components
    base = filename.replace("\\", "/").split("/")[-1]
    # Remove null bytes
    base = base.replace("\x00", "")
    base = SAFE_FILENAME_RE.sub("_", base)
    base = base.strip("._")
    return base or "clip"
