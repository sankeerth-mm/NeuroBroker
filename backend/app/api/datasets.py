import os
import shutil
import zipfile
import csv
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.database import get_db
from backend.app.config import settings
from backend.app.models.user import User
from backend.app.models.dataset import Dataset, DatasetPartition
from backend.app.schemas.dataset import DatasetResponse, DatasetPartitionResponse
from backend.app.auth.dependencies import get_current_active_user
from backend.app.security.checksum import compute_sha256
from backend.app.partitioning.non_iid_detector import non_iid_detector
from backend.app.logging.logger import log_event

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])

@router.post("/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    dataset_type: str = Form("image_classification"), # image_classification or csv_classification
    label_column: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith((".zip", ".csv", ".tar.gz")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supported file formats: .zip, .csv"
        )
    
    # Save uploaded file
    timestamp_prefix = os.urandom(4).hex()
    saved_filename = f"{timestamp_prefix}_{file.filename}"
    saved_path = settings.DATASETS_DIR / saved_filename
    
    with open(saved_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
        
    checksum = compute_sha256(saved_path)
    file_size = saved_path.stat().st_size
    
    total_samples = 0
    class_distribution = {}
    is_non_iid_flag = False
    
    # Validate and inspect content instantly without full extraction
    if saved_path.suffix == ".zip":
        try:
            with zipfile.ZipFile(saved_path, "r") as z:
                for info in z.infolist():
                    if info.is_dir():
                        continue
                    name = info.filename.replace("\\", "/").strip("/")
                    if name.startswith((".", "__")) or "/." in name or "/__" in name:
                        continue
                    ext = Path(name).suffix.lower()
                    if ext in ('.png', '.jpg', '.jpeg', '.bmp', '.npy', '.csv'):
                        parts = name.split("/")
                        class_name = parts[-2] if len(parts) >= 2 else "default"
                        class_distribution[class_name] = class_distribution.get(class_name, 0) + 1
                        total_samples += 1
        except Exception as e:
            if saved_path.exists():
                saved_path.unlink()
            raise HTTPException(status_code=400, detail=f"Invalid zip archive: {str(e)}")
            
        if total_samples == 0:
            if saved_path.exists():
                saved_path.unlink()
            raise HTTPException(status_code=400, detail="No valid image or data files found inside uploaded zip.")
            
    elif saved_path.suffix == ".csv":
        dataset_type = "csv_classification"
        try:
            with open(saved_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                target_col = label_column if label_column in headers else headers[-1]
                label_column = target_col
                for row in reader:
                    lbl = str(row.get(target_col, "unknown"))
                    class_distribution[lbl] = class_distribution.get(lbl, 0) + 1
                    total_samples += 1
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid CSV file: {str(e)}")
            
    # Check for non-IID class imbalance
    is_non_iid_flag, skew_msg = non_iid_detector.is_skewed(class_distribution)
    
    dataset = Dataset(
        user_id=current_user.id,
        name=name,
        description=description,
        dataset_type=dataset_type,
        file_path=str(saved_path),
        total_samples=total_samples,
        total_size_bytes=file_size,
        class_distribution=class_distribution,
        label_column=label_column,
        checksum_sha256=checksum,
        is_validated=True,
        is_non_iid=is_non_iid_flag
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    
    await log_event(
        level="INFO",
        component="dataset",
        message=f"Dataset '{dataset.name}' uploaded ({total_samples} samples, {len(class_distribution)} classes). {skew_msg}",
        db_session=db
    )
    
    return dataset

@router.get("", response_model=List[DatasetResponse])
async def list_datasets(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Dataset).order_by(desc(Dataset.created_at))
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Dataset).where(Dataset.id == dataset_id)
    result = await db.execute(query)
    dataset = result.scalars().first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset

@router.get("/{dataset_id}/download")
async def download_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Dataset).where(Dataset.id == dataset_id)
    result = await db.execute(query)
    dataset = result.scalars().first()
    if not dataset or not Path(dataset.file_path).exists():
        raise HTTPException(status_code=404, detail="Dataset file not found")
    return FileResponse(dataset.file_path, filename=Path(dataset.file_path).name)

@router.get("/partitions/{partition_id}/download")
async def download_partition(partition_id: int, db: AsyncSession = Depends(get_db)):
    """Download specific partition file for volunteer worker execution."""
    query = select(DatasetPartition).where(DatasetPartition.id == partition_id)
    result = await db.execute(query)
    partition = result.scalars().first()
    if not partition or not Path(partition.file_path).exists():
        raise HTTPException(status_code=404, detail="Partition file not found")
    return FileResponse(partition.file_path, filename=Path(partition.file_path).name)
