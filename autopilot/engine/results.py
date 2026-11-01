"""Clips Kitty publishing result contracts. See PROVENANCE.md."""
from dataclasses import dataclass, field

@dataclass
class PlatformOutcome:
    """What happened on ONE destination of a fan-out."""

    platform: str
    state: str = "queued"  # queued | processing | published | failed | skipped
    post_id: str = ""
    post_url: str = ""
    error: str = ""

    @property
    def skipped(self) -> bool:
        return self.state == "skipped"

@dataclass
class FanOutResult:
    """One upload, several destinations.

    Deliberately not `PublishResult`. That type carries a single video_id and
    a single URL because a YouTube upload has exactly one of each, and
    flattening eight destinations into it would throw away the per-platform
    errors that are the main thing a user needs to see. It lives here rather
    than in publish/base.py because Upload-Post is currently the only provider
    that fans out; if a second one appears, move it.
    """

    request_id: str = ""
    outcomes: list[PlatformOutcome] = field(default_factory=list)

    @property
    def done(self) -> bool:
        return all(o.state in ("published", "failed", "skipped") for o in self.outcomes)

    @property
    def published(self) -> list[PlatformOutcome]:
        return [o for o in self.outcomes if o.state == "published"]

    @property
    def failed(self) -> list[PlatformOutcome]:
        return [o for o in self.outcomes if o.state == "failed"]
