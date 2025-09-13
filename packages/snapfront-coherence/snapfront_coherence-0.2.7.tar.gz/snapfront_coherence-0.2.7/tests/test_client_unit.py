import os, time
os.environ['API_KEYS']='TESTKEY1,TESTKEY2,LIMITKEY'
os.environ['RATE_LIMIT_RPS']='1'
os.environ['RATE_LIMIT_BURST']='1'
from fastapi.testclient import TestClient
from api.main import app

c = TestClient(app)

def test_health():
    r = c.get('/health')
    assert r.status_code==200

def test_auth():
    r = c.post('/v1/wct_phi', json={'deltas':[0.1]})
    assert r.status_code==401

def test_wct_headers_and_receipt():
    r = c.post('/v1/wct_phi', headers={'X-API-Key':'TESTKEY1'}, json={'deltas':[0.8,1.1,-0.5]})
    assert r.status_code==200
    j = r.json()
    assert j.get('band') in ('Coherent','Caution','Defensive')
    assert isinstance(j.get('receipt'), dict)
    assert 'X-WCT-Phi' in r.headers and 'X-Coherence-Band' in r.headers

def test_band_headers_and_receipt():
    r = c.post('/v1/coherence-band', headers={'X-API-Key':'TESTKEY2'}, json={'deltas':[0.2,-0.3,0.6]})
    assert r.status_code==200
    j = r.json()
    assert j.get('band') in ('Coherent','Caution','Defensive')
    assert isinstance(j.get('receipt'), dict)
    assert 'X-WCT-Phi' in r.headers and 'X-Coherence-Band' in r.headers

def test_rate_limit_429_headers():
    r1 = c.post('/v1/wct_phi', headers={'X-API-Key':'LIMITKEY'}, json={'deltas':[0.1, -0.1]})
    assert r1.status_code in (200, 429)
    r2 = c.post('/v1/wct_phi', headers={'X-API-Key':'LIMITKEY'}, json={'deltas':[0.1, -0.1]})
    assert r2.status_code == 429
    assert 'Retry-After' in r2.headers and 'Retry-After-Ms' in r2.headers
    assert int(float(r2.headers['Retry-After'])) >= 0
    assert int(r2.headers['Retry-After-Ms']) >= 0
    j = r2.json()
    assert isinstance(j.get('detail'), dict)
    assert 'retry_after_ms' in j['detail']
