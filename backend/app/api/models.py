import os
import shutil
import zipfile
import json
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.database import get_db
from backend.app.config import settings
from backend.app.models.user import User
from backend.app.models.model_pkg import ModelPackage, ModelVersion
from backend.app.models.job import TrainingJob
from backend.app.schemas.model_pkg import ModelPackageResponse, ModelVersionResponse
from backend.app.auth.dependencies import get_current_active_user
from backend.app.security.checksum import compute_sha256
from backend.app.logging.logger import log_event

router = APIRouter(prefix="/api/models", tags=["Model Packages"])

@router.post("/upload", response_model=ModelPackageResponse, status_code=status.HTTP_201_CREATED)
async def upload_model_package(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model package must be uploaded as a .zip file containing model.py, train.py, config.json"
        )
    
    timestamp_prefix = os.urandom(4).hex()
    saved_filename = f"{timestamp_prefix}_{file.filename}"
    saved_path = settings.MODEL_PACKAGES_DIR / saved_filename
    
    with open(saved_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
        
    checksum = compute_sha256(saved_path)
    
    # Validate package structure
    config_data = {}
    try:
        with zipfile.ZipFile(saved_path, "r") as z:
            namelist = [n.replace("\\", "/").strip("/") for n in z.namelist()]
            
            # Check for model.py and train.py anywhere in archive
            has_model = any(n.endswith("model.py") for n in namelist)
            has_train = any(n.endswith("train.py") for n in namelist)
            
            if not has_model:
                raise HTTPException(status_code=400, detail="model_package.zip is missing required file: model.py")
            if not has_train:
                raise HTTPException(status_code=400, detail="model_package.zip is missing required file: train.py")
            
            # Try reading config.json
            config_entry = next((n for n in z.namelist() if n.endswith("config.json")), None)
            if config_entry:
                with z.open(config_entry) as cf:
                    config_data = json.loads(cf.read().decode("utf-8"))
    except HTTPException:
        if saved_path.exists():
            saved_path.unlink()
        raise
    except Exception as e:
        if saved_path.exists():
            saved_path.unlink()
        raise HTTPException(status_code=400, detail=f"Failed to inspect model package: {str(e)}")
        
    model_pkg = ModelPackage(
        user_id=current_user.id,
        name=name,
        description=description,
        framework="pytorch",
        file_path=str(saved_path),
        config_json=config_data,
        checksum_sha256=checksum,
        is_validated=True
    )
    db.add(model_pkg)
    await db.commit()
    await db.refresh(model_pkg)
    
    await log_event(
        level="INFO",
        component="model",
        message=f"Model package '{model_pkg.name}' validated and uploaded.",
        db_session=db
    )
    
    return model_pkg

@router.get("", response_model=List[ModelPackageResponse])
async def list_model_packages(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(ModelPackage).order_by(desc(ModelPackage.created_at))
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{model_id}", response_model=ModelPackageResponse)
async def get_model_package(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(ModelPackage).where(ModelPackage.id == model_id)
    result = await db.execute(query)
    model = result.scalars().first()
    if not model:
        raise HTTPException(status_code=404, detail="Model package not found")
    return model

@router.get("/{model_id}/download")
async def download_model_package(model_id: int, db: AsyncSession = Depends(get_db)):
    query = select(ModelPackage).where(ModelPackage.id == model_id)
    result = await db.execute(query)
    model = result.scalars().first()
    if not model or not Path(model.file_path).exists():
        raise HTTPException(status_code=404, detail="Model package file not found")
    return FileResponse(model.file_path, filename=Path(model.file_path).name)

@router.get("/versions/{version_id}/download")
async def download_model_version_checkpoint(version_id: int, db: AsyncSession = Depends(get_db)):
    query = select(ModelVersion).where(ModelVersion.id == version_id)
    result = await db.execute(query)
    version = result.scalars().first()
    if not version or not Path(version.checkpoint_path).exists():
        raise HTTPException(status_code=404, detail="Checkpoint file not found")
    return FileResponse(version.checkpoint_path, filename=Path(version.checkpoint_path).name)

@router.get("/jobs/{job_id}/final")
async def download_final_job_model(job_id: int, db: AsyncSession = Depends(get_db)):
    """Download the final aggregated global model .pth file for a job."""
    query = (
        select(ModelVersion)
        .where(ModelVersion.job_id == job_id)
        .order_by(desc(ModelVersion.round_number))
    )
    result = await db.execute(query)
    latest_version = result.scalars().first()
    
    if not latest_version or not Path(latest_version.checkpoint_path).exists():
        raise HTTPException(status_code=404, detail="No global model checkpoint found for this job.")
        
    return FileResponse(
        latest_version.checkpoint_path,
        filename=f"neurobroker_job_{job_id}_final_model.pth",
        media_type="application/octet-stream"
    )
