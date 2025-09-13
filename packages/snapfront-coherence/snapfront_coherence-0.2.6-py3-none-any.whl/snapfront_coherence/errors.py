class SnapfrontError(Exception):
    """Base error for Snapfront Coherence SDK."""

class AuthenticationError(SnapfrontError):
    """401 Unauthorized."""

class RateLimitError(SnapfrontError):
    """429 Too Many Requests."""
    def __init__(self, message: str, retry_after_ms: int | None = None):
        super().__init__(message)
        self.retry_after_ms = retry_after_ms

class ServerError(SnapfrontError):
    """5xx server errors."""

class ClientError(SnapfrontError):
    """4xx client errors (other than 401/429)."""
