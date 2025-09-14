import json
import pytest
import httpx
from app.main import app

@pytest.mark.asyncio
async def test_p3_relationships(tmp_path):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        # Object + two contexts
        r = await ac.post("/objects", json={"object_type": "dataset"})
        oid = r.json()["object_id"]

        r = await ac.post(f"/objects/{oid}/contexts", content=json.dumps({"a":1}), headers={"Content-Type":"application/json"})
        ctx1 = r.json()["context_id"]
        r = await ac.post(f"/objects/{oid}/contexts", content=json.dumps({"b":2}), headers={"Content-Type":"application/json"})
        ctx2 = r.json()["context_id"]

        # Link ctx1 -> ctx2 via relationships
        r = await ac.post(f"/relationships?from_type=context&from_id={ctx1}&to_type=context&to_id={ctx2}&rel_type=derived_from")
        assert r.status_code == 200
        rel_id = r.json()["rel_id"]
        assert rel_id

        # Query relationships for ctx1
        r = await ac.get(f"/relationships?node_type=context&node_id={ctx1}")
        assert r.status_code == 200
        rels = r.json()["relationships"]
        assert any(rel["rel_type"] == "derived_from" and rel["from"]["id"] == ctx1 for rel in rels)
