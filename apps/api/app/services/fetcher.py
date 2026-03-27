from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib import robotparser
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import FetchLog, Source
from app.services.url_safety import ensure_public_url

settings = get_settings()
_LAST_REQUEST_BY_DOMAIN: dict[str, float] = {}


@dataclass
class FetchResult:
    url: str
    status_code: int
    content_type: str
    text: str | None
    bytes_content: bytes
    headers: dict[str, str]
    content_hash: str
    fetched_at: datetime
    snapshot_path: str | None


def _respect_rate_limit(url: str, min_interval_seconds: float = 0.5) -> None:
    host = urlparse(url).hostname or ""
    last_request = _LAST_REQUEST_BY_DOMAIN.get(host)
    if last_request:
        elapsed = time.time() - last_request
        if elapsed < min_interval_seconds:
            time.sleep(min_interval_seconds - elapsed)
    _LAST_REQUEST_BY_DOMAIN[host] = time.time()


def _robots_allowed(url: str, client: httpx.Client) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = robotparser.RobotFileParser()
    try:
        response = client.get(robots_url, timeout=settings.fetch_timeout_seconds)
        if response.status_code >= 400:
            return True
        parser.parse(response.text.splitlines())
        return parser.can_fetch(settings.user_agent_string, url)
    except httpx.HTTPError:
        return True


def _store_snapshot(content_hash: str, content: bytes) -> str:
    settings.snapshot_path.mkdir(parents=True, exist_ok=True)
    path = Path(settings.snapshot_path) / f"{content_hash}.bin"
    path.write_bytes(content)
    return str(path)


def fetch_url(db: Session, url: str, source: Source | None = None, allow_robots_check: bool = True) -> FetchResult:
    ensure_public_url(url)
    headers = {"User-Agent": settings.user_agent_string}
    started = time.time()
    with httpx.Client(follow_redirects=True, headers=headers) as client:
        robots_checked = False
        if allow_robots_check:
            robots_checked = True
            if not _robots_allowed(url, client):
                log_fetch(db, source.id if source else None, url, None, None, None, robots_checked, "Blocked by robots.txt")
                raise PermissionError("robots.txt disallows this fetch.")
        _respect_rate_limit(url)
        response = client.get(url, timeout=settings.fetch_timeout_seconds)
    duration_ms = int((time.time() - started) * 1000)
    content_type = response.headers.get("content-type", "application/octet-stream").split(";")[0]
    payload = response.content
    content_hash = hashlib.sha256(payload).hexdigest()
    snapshot_path = _store_snapshot(content_hash, payload)
    text: str | None = None
    if "text" in content_type or "html" in content_type or "json" in content_type:
        response.encoding = response.encoding or "utf-8"
        text = response.text
    result = FetchResult(
        url=str(response.url),
        status_code=response.status_code,
        content_type=content_type,
        text=text,
        bytes_content=payload,
        headers=dict(response.headers),
        content_hash=content_hash,
        fetched_at=datetime.utcnow(),
        snapshot_path=snapshot_path,
    )
    log_fetch(db, source.id if source else None, str(response.url), response.status_code, duration_ms, content_type, robots_checked, None)
    return result


def log_fetch(
    db: Session,
    source_id: str | None,
    request_url: str,
    response_status: int | None,
    response_time_ms: int | None,
    content_type: str | None,
    robots_checked: bool,
    error_message: str | None,
) -> None:
    db.add(
        FetchLog(
            source_id=source_id,
            request_url=request_url,
            response_status=response_status,
            response_time_ms=response_time_ms,
            content_type=content_type,
            robots_checked=robots_checked,
            error_message=error_message,
        )
    )
    db.commit()

