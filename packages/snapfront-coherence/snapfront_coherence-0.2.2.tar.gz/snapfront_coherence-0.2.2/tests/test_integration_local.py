import json, math
import pytest
from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient as FastAPITestClient

from snapfront_coherence import Client

# Minimal in-process API for integration test (no network binding)
def make_app():
    app = FastAPI()

    @app.post("/v1/wct_phi")
    def wct_phi(body: dict, x_api_key: str = Header(None)):
        if x_api_key != "TESTKEY":
            raise HTTPException(status_code=401, detail="Invalid API key")
        deltas = body.get("deltas", [])
        if not deltas:
            raise HTTPException(status_code=400, detail="deltas required")
        # deterministic scoring consistent with Day-2 spec
        phi2 = 2.618034
        sabs = sum(abs(x) for x in deltas)
        import math as _math
        w = 1.0 / (1.0 + _math.exp(-sabs / phi2))
        band = "Defensive"
        if w >= 0.70:
            band = "Coherent"
        elif w >= 0.50:
            band = "Caution"
        # headers + body
        return {
            "wct_phi": w,
            "band": band,
            "sum_abs": sabs,
            "phi2": phi2,
            "thresholds": {"coherent":0.70,"caution":0.50},
            "receipt": {"id": "TEST-RECPT-123"}
        }

    @app.post("/v1/coherence-band")
    def coherence_band(body: dict, x_api_key: str = Header(None)):
        res = wct_phi(body, x_api_key)  # reuse logic
        return {"band": res["band"], "wct_phi": res["wct_phi"], "receipt": res["receipt"]}

    return app

def test_integration_with_inprocess_fastapi(monkeypatch):
    app = make_app()
    fa_client = FastAPITestClient(app)

    # Monkeypatch requests.Session.post used by SDK to hit the FastAPI client
    import requests

    def _fake_post(self, url, headers=None, data=None, timeout=None):
        # translate requests call -> fastapi testclient call
        path = url.split("://",1)[-1]
        idx = path.find("/")
        if idx != -1:
            path = path[idx:]
        method = "POST"
        resp = fa_client.request(method, path, headers=headers, data=data)
        # Build a requests.Response-like object
        r = requests.Response()
        r.status_code = resp.status_code
        r._content = resp.content
        r.headers.update(resp.headers)
        r.url = url
        return r

    monkeypatch.setattr("requests.Session.post", _fake_post, raising=True)

    client = Client(api_key="TESTKEY", base_url="http://testserver")
    out = client.wct_phi([0.8,1.1,-0.5])
    assert out["receipt"]["id"] == "TEST-RECPT-123"
    assert out["band"] in ("Coherent","Caution","Defensive")
