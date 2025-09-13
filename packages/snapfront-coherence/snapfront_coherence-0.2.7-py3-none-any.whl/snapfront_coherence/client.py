from __future__ import annotations
from typing import Sequence, Optional, List, Dict, Any, Tuple
import time
import json
import math
import hashlib
import requests

from .errors import (
    SnapfrontError, AuthenticationError, RateLimitError, ServerError, ClientError
)

_RETRIABLE = {429, 502, 503, 504}

class Client:
    """
    Minimal coherence API client.
    - wct_phi(deltas) -> dict with 'wct', 'band', 'receipt'
    - coherence_band(deltas) -> dict
    - score_series(series, mode, window) -> list[dict]
    Helpers:
    - save_receipt(resp, path) -> str
    - verify_hashes(resp, request_bytes=None, response_bytes=None) -> bool
    """
    def __init__(
        self,
        api_key: str,
        base_url: str = "http://127.0.0.1:8000",
        connect_timeout_s: float = 3.0,
        read_timeout_s: float = 5.0,
        retries: int = 2,  # total retries on _RETRIABLE
        session: Optional[requests.Session] = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.connect_timeout_s = connect_timeout_s
        self.read_timeout_s = read_timeout_s
        self.retries = retries
        self._session = session or requests.Session()

    # -------------------------
    # Public API
    # -------------------------
    def wct_phi(self, deltas: Sequence[float]) -> Dict[str, Any]:
        """Compute WCT_φ for a sequence of deltas (finite floats)."""
        self._validate_deltas(deltas)
        return self._post_json("/v1/wct_phi", {"deltas": list(deltas)})

    def coherence_band(self, deltas: Sequence[float]) -> Dict[str, Any]:
        """Return the band classification (and wct) for a sequence of deltas."""
        self._validate_deltas(deltas)
        return self._post_json("/v1/coherence-band", {"deltas": list(deltas)})

    def score_series(
        self,
        series: Sequence[float],
        mode: str = "absolute",
        window: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Convenience helper to transform a raw series into deltas and score it.
        mode: 'absolute' or 'relative' ((a-b)/|b|), window: sliding window size for deltas.
        """
        if not isinstance(series, Sequence) or len(series) < 2:
            raise ValueError("series must be a sequence with length >= 2")
        if mode not in ("absolute", "relative"):
            raise ValueError("mode must be 'absolute' or 'relative'")
        # compute deltas
        def rel(a: float, b: float) -> float:
            denom = b if b != 0 else 1e-12
            return (a - b) / abs(denom)
        raw = list(series)
        if mode == "absolute":
            deltas = [raw[i] - raw[i-1] for i in range(1, len(raw))]
        else:
            deltas = [rel(raw[i], raw[i-1]) for i in range(1, len(raw))]
        # windowing
        if window is None or window <= 1:
            return [self._post_json("/v1/wct_phi", {"deltas": deltas})]
        out: List[Dict[str, Any]] = []
        for i in range(window, len(series)):
            seg = deltas[i-window:i]
            out.append(self._post_json("/v1/wct_phi", {"deltas": seg}))
        return out

    # -------------------------
    # Receipt helpers
    # -------------------------
    @staticmethod
    def save_receipt(resp: Dict[str, Any], path: str) -> str:
        """
        Save the 'receipt' object from a response to a JSON file.
        Returns the filepath. Raises if receipt missing.
        """
        if not isinstance(resp, dict) or "receipt" not in resp:
            raise ValueError("response does not contain a 'receipt' object")
        from pathlib import Path
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as f:
            json.dump(resp["receipt"], f, indent=2)
        return str(p)

    @staticmethod
    def verify_hashes(resp: Dict[str, Any],
                      request_bytes: Optional[bytes] = None,
                      response_bytes: Optional[bytes] = None) -> bool:
        """
        Verify receipt.request_sha256 and receipt.response_sha256 against provided bytes.
        If one side isn't provided, only the other side is checked.
        Returns True only if all provided comparisons match; False otherwise.
        """
        if not isinstance(resp, dict) or "receipt" not in resp:
            return False
        r = resp["receipt"]
        ok = True
        if request_bytes is not None:
            want = r.get("request_sha256")
            have = hashlib.sha256(request_bytes).hexdigest()
            ok = ok and (want is None or want == have)
        if response_bytes is not None:
            want = r.get("response_sha256")
            have = hashlib.sha256(response_bytes).hexdigest()
            ok = ok and (want is None or want == have)
        return ok

    # -------------------------
    # Internals
    # -------------------------
    def _validate_deltas(self, deltas: Sequence[float]) -> None:
        if not isinstance(deltas, Sequence) or len(deltas) == 0:
            raise ValueError("deltas must be a non-empty sequence of finite floats")
        for x in deltas:
            if not isinstance(x, (int, float)):
                raise ValueError("deltas must contain only numbers")
            if math.isnan(x) or math.isinf(x):
                raise ValueError("deltas must be finite")

    def _post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = self.base_url + path
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        timeout: Tuple[float, float] = (self.connect_timeout_s, self.read_timeout_s)
        # naive exponential backoff: 0.2, 0.4 on two retries (unless server supplies Retry-After)
        attempt = 0
        backoff = 0.2
        last_err: Exception | None = None
        while True:
            try:
                resp = self._session.post(url, headers=headers, data=body_bytes, timeout=timeout)
                if resp.status_code == 200:
                    # Optionally verify response hash if present
                    try:
                        data = resp.json()
                    except Exception as e:
                        raise SnapfrontError(f"Invalid JSON in response: {e}")
                    return data
                if resp.status_code == 401:
                    raise AuthenticationError(f"Unauthorized: {resp.text}")
                if resp.status_code in _RETRIABLE:
                    # use Retry-After headers if present
                    retry_after_ms = None
                    # Header (ms) takes precedence, then seconds, then JSON body
                    h_ms = resp.headers.get("Retry-After-Ms")
                    if h_ms is not None:
                        try:
                            retry_after_ms = int(h_ms)
                        except Exception:
                            retry_after_ms = None
                    if retry_after_ms is None:
                        h_s = resp.headers.get("Retry-After")
                        if h_s is not None:
                            try:
                                retry_after_ms = int(float(h_s) * 1000.0)
                            except Exception:
                                retry_after_ms = None
                    if retry_after_ms is None:
                        try:
                            body = resp.json()
                            retry_after_ms = body.get("detail", {}).get("retry_after_ms")
                        except Exception:
                            retry_after_ms = None
                    # sleep strategy
                    sleep_s = (retry_after_ms / 1000.0) if isinstance(retry_after_ms, (int, float)) else backoff
                    if attempt < self.retries:
                        time.sleep(max(0.0, float(sleep_s)))
                        attempt += 1
                        backoff *= 2
                        continue
                    raise RateLimitError(f"Rate limited or transient server error ({resp.status_code})", retry_after_ms)
                if 400 <= resp.status_code < 500:
                    try:
                        detail = resp.json().get("detail")
                    except Exception:
                        detail = resp.text
                    raise ClientError(f"Client error {resp.status_code}: {detail}")
                if 500 <= resp.status_code:
                    raise ServerError(f"Server error {resp.status_code}: {resp.text}")
                raise SnapfrontError(f"Unexpected status {resp.status_code}")
            except (AuthenticationError, RateLimitError, ClientError, ServerError):
                raise
            except Exception as e:
                last_err = e
                if attempt < self.retries:
                    time.sleep(backoff)
                    attempt += 1
                    backoff *= 2
                    continue
                raise SnapfrontError(f"Request failed: {e}") from e
