import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.config import settings

@pytest.mark.asyncio
async def test_node_registration_and_heartbeat():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Invalid token rejection
        bad_reg = {
            "token": "INVALID_TOKEN",
            "hostname": "test-box",
            "cpu_cores": 8,
            "ram_total_mb": 16384.0
        }
        res = await client.post("/api/nodes/register", json=bad_reg)
        assert res.status_code == 403
        
        # Valid registration
        valid_reg = {
            "token": settings.VOLUNTEER_REGISTRATION_TOKEN,
            "node_id": "TEST-NODE-01",
            "hostname": "test-box-alpha",
            "cpu_cores": 16,
            "cpu_name": "Apple M-Series",
            "ram_total_mb": 32768.0,
            "gpu_name": "Apple MPS",
            "gpu_memory_total_mb": 16384.0,
            "disk_total_gb": 500.0,
            "cuda_available": False
        }
        res = await client.post("/api/nodes/register", json=valid_reg)
        assert res.status_code == 200
        data = res.json()
        assert data["node_id"] == "TEST-NODE-01"
        assert data["status"] == "ONLINE"
        
        # Send Heartbeat
        hb_payload = {
            "node_id": "TEST-NODE-01",
            "cpu_usage": 25.5,
            "ram_usage_percent": 40.0,
            "ram_available_mb": 19000.0,
            "gpu_usage_percent": 15.0,
            "gpu_memory_available_mb": 12000.0,
            "disk_available_gb": 400.0,
            "network_upload_mbps": 120.0,
            "network_download_mbps": 200.0,
            "latency_ms": 12.0
        }
        hb_res = await client.post("/api/nodes/heartbeat", json=hb_payload)
        assert hb_res.status_code == 200
        assert hb_res.json()["status"] == "ok"
        
        # Get Node List
        list_res = await client.get("/api/nodes")
        assert list_res.status_code == 200
        nodes_data = list_res.json()
        assert nodes_data["total"] >= 1
        assert any(n["node_id"] == "TEST-NODE-01" for n in nodes_data["nodes"])
