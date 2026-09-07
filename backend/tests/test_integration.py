import pytest
import io
import zipfile
import torch
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.config import settings, BASE_DIR
from backend.app.security.hashing import get_password_hash
from volunteer_node.model_loader import model_loader
from volunteer_node.dataset_loader import dataset_loader
from volunteer_node.trainer import local_trainer

@pytest.mark.asyncio
async def test_full_end_to_end_distributed_training_workflow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register / Login User
        reg_data = {
            "name": "Integration Tester",
            "email": "tester_e2e@neurobroker.org",
            "password": "Password123!",
            "role": "admin"
        }
        auth_res = await client.post("/auth/register", json=reg_data)
        if auth_res.status_code != 201:
            login_res = await client.post("/auth/login", json={"email": reg_data["email"], "password": reg_data["password"]})
            token = login_res.json()["access_token"]
        else:
            token = auth_res.json()["access_token"]
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Register Volunteer Node
        node_reg = {
            "token": settings.VOLUNTEER_REGISTRATION_TOKEN,
            "node_id": "TEST-E2E-NODE-01",
            "hostname": "e2e-worker",
            "cpu_cores": 8,
            "ram_total_mb": 16384.0,
            "gpu_name": "CPU/MPS",
            "cuda_available": False
        }
        n_res = await client.post("/api/nodes/register", json=node_reg)
        assert n_res.status_code == 200
        
        # 3. Upload Model Package
        model_pkg_zip = BASE_DIR / "example_models" / "mnist_cnn_package.zip"
        assert model_pkg_zip.exists()
        
        with open(model_pkg_zip, "rb") as mf:
            m_res = await client.post(
                "/api/models/upload",
                data={"name": "E2E_MNIST_CNN", "description": "Test CNN package"},
                files={"file": ("mnist_cnn_package.zip", mf, "application/zip")},
                headers=headers
            )
        assert m_res.status_code == 201
        model_pkg_id = m_res.json()["id"]
        
        # 4. Upload Dataset
        dataset_zip = BASE_DIR / "example_datasets" / "mnist_sample_dataset.zip"
        assert dataset_zip.exists()
        
        with open(dataset_zip, "rb") as df:
            d_res = await client.post(
                "/api/datasets/upload",
                data={"name": "E2E_MNIST_Data", "dataset_type": "image_classification"},
                files={"file": ("mnist_sample_dataset.zip", df, "application/zip")},
                headers=headers
            )
        assert d_res.status_code == 201
        dataset_id = d_res.json()["id"]
        
        # 5. Create Training Job
        job_payload = {
            "name": "E2E Integration Job",
            "model_package_id": model_pkg_id,
            "dataset_id": dataset_id,
            "max_rounds": 2,
            "local_epochs": 1,
            "batch_size": 16,
            "learning_rate": 0.01,
            "target_accuracy": 90.0,
            "min_volunteer_nodes": 1
        }
        job_res = await client.post("/api/jobs", json=job_payload, headers=headers)
        assert job_res.status_code == 201
        job_id = job_res.json()["id"]
        
        # 6. Test Local Model Loading & PyTorch Training
        model = model_loader.load_model_from_package(model_pkg_zip)
        dataloader, total_samples = dataset_loader.create_dataloader(dataset_zip, batch_size=16)
        
        state_dict, loss, acc, duration = local_trainer.train(
            model=model,
            dataloader=dataloader,
            global_state_dict=None,
            local_epochs=1,
            learning_rate=0.01
        )
        assert loss > 0.0
        assert acc >= 0.0
        assert len(state_dict) > 0
        
        # 7. Test loading resulting state dict back into PyTorch architecture
        eval_model = model_loader.load_model_from_package(model_pkg_zip)
        eval_model.load_state_dict(state_dict)
        eval_model.eval()
        
        # Perform test forward pass
        dummy_input = torch.randn(2, 1, 28, 28)
        output = eval_model(dummy_input)
        assert output.shape == (2, 10)
