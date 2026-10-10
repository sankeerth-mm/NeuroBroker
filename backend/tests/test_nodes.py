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

@pytest.mark.asyncio
async def test_pending_tasks_and_task_fail_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register node
        valid_reg = {
            "token": settings.VOLUNTEER_REGISTRATION_TOKEN,
            "node_id": "TEST-NODE-RECONNECT-01",
            "hostname": "test-box-beta",
            "cpu_cores": 4,
            "ram_total_mb": 8192.0
        }
        res = await client.post("/api/nodes/register", json=valid_reg)
        assert res.status_code == 200
        
        # Test pending tasks endpoint (should return empty list initially)
        pending_res = await client.get("/api/nodes/TEST-NODE-RECONNECT-01/tasks/pending")
        assert pending_res.status_code == 200
        assert pending_res.json()["tasks"] == []

        # Test heartbeat 404 on unregistered node
        hb_res = await client.post("/api/nodes/heartbeat", json={"node_id": "NON-EXISTENT-NODE", "cpu_usage": 10.0, "ram_usage_percent": 20.0, "ram_available_mb": 4096.0})
        assert hb_res.status_code == 404

def test_node_client_url_and_retries(tmp_path):
    from volunteer_node.node_client import NodeClient
    nc = NodeClient(server_url="http://192.168.1.100:8000/", token=settings.VOLUNTEER_REGISTRATION_TOKEN, node_id="TEST-NODE-UNIT")
    assert nc.server_url == "http://192.168.1.100:8000"
    assert nc.ws_url == "ws://192.168.1.100:8000/ws/volunteer"
    assert nc._build_url("/api/nodes/register") == "http://192.168.1.100:8000/api/nodes/register"
    assert nc._build_url("http://custom-domain.com/file.zip") == "http://custom-domain.com/file.zip"

