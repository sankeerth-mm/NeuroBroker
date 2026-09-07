import io
import zipfile
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from backend.app.database import get_db
from backend.app.config import settings, BASE_DIR
from backend.app.models.node import VolunteerNode, NodeMetricHistory
from backend.app.schemas.node import (
    NodeRegisterRequest,
    NodeHeartbeatRequest,
    NodeBenchmarkScoreUpdate,
    NodeResponse,
    NodeListResponse,
)
from backend.app.monitoring.anomaly_detector import anomaly_detector
from backend.app.logging.logger import log_event
from backend.app.ws.user_ws import user_ws_manager

router = APIRouter(prefix="/api/nodes", tags=["Volunteer Nodes"])

@router.post("/register", response_model=NodeResponse)
async def register_node(payload: NodeRegisterRequest, db: AsyncSession = Depends(get_db)):
    # Verify registration token
    if payload.token != settings.VOLUNTEER_REGISTRATION_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid volunteer registration token."
        )
    
    # Generate node_id if not provided
    node_id = payload.node_id
    if not node_id:
        count_res = await db.execute(select(func.count(VolunteerNode.id)))
        node_num = (count_res.scalar() or 0) + 1
        node_id = f"NODE-{node_num:02d}"
    
    # Check if node already registered
    query = select(VolunteerNode).where(VolunteerNode.node_id == node_id)
    result = await db.execute(query)
    existing_node = result.scalars().first()
    
    if existing_node:
        # Update specs
        existing_node.hostname = payload.hostname or existing_node.hostname
        existing_node.ip_address = payload.ip_address or existing_node.ip_address
        existing_node.cpu_name = payload.cpu_name or existing_node.cpu_name
        existing_node.cpu_cores = payload.cpu_cores
        existing_node.ram_total_mb = payload.ram_total_mb
        existing_node.gpu_name = payload.gpu_name or "CPU Only"
        existing_node.gpu_memory_total_mb = payload.gpu_memory_total_mb
        existing_node.disk_total_gb = payload.disk_total_gb
        existing_node.os_info = payload.os_info
        existing_node.python_version = payload.python_version
        existing_node.pytorch_version = payload.pytorch_version
        existing_node.cuda_available = payload.cuda_available
        existing_node.cuda_version = payload.cuda_version
        existing_node.status = "ONLINE"
        existing_node.last_heartbeat = datetime.utcnow()
        node = existing_node
    else:
        node = VolunteerNode(
            node_id=node_id,
            hostname=payload.hostname,
            ip_address=payload.ip_address,
            cpu_name=payload.cpu_name,
            cpu_cores=payload.cpu_cores,
            ram_total_mb=payload.ram_total_mb,
            ram_available_mb=payload.ram_total_mb * 0.8,
            gpu_name=payload.gpu_name or "CPU Only",
            gpu_memory_total_mb=payload.gpu_memory_total_mb,
            gpu_memory_available_mb=payload.gpu_memory_total_mb,
            disk_total_gb=payload.disk_total_gb,
            disk_available_gb=payload.disk_total_gb * 0.9,
            os_info=payload.os_info,
            python_version=payload.python_version,
            pytorch_version=payload.pytorch_version,
            cuda_available=payload.cuda_available,
            cuda_version=payload.cuda_version,
            status="ONLINE",
            last_heartbeat=datetime.utcnow()
        )
        db.add(node)
    
    await db.commit()
    await db.refresh(node)
    
    await log_event(
        level="INFO",
        component="volunteer",
        message=f"Volunteer node {node.node_id} registered ({node.cpu_name or 'CPU'}, GPU: {node.gpu_name})",
        node_id=node.node_id,
        db_session=db
    )
    
    # Broadcast to dashboard
    await user_ws_manager.broadcast("node_registered", {
        "node_id": node.node_id,
        "status": node.status,
        "gpu_name": node.gpu_name,
        "cpu_cores": node.cpu_cores
    })
    
    return node

@router.post("/heartbeat")
async def receive_heartbeat(payload: NodeHeartbeatRequest, db: AsyncSession = Depends(get_db)):
    query = select(VolunteerNode).where(VolunteerNode.node_id == payload.node_id)
    result = await db.execute(query)
    node = result.scalars().first()
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {payload.node_id} not registered."
        )
    
    # Update telemetry
    node.cpu_usage = payload.cpu_usage
    node.ram_usage_percent = payload.ram_usage_percent
    node.ram_available_mb = payload.ram_available_mb
    node.gpu_usage_percent = payload.gpu_usage_percent or 0.0
    node.gpu_memory_available_mb = payload.gpu_memory_available_mb or 0.0
    node.disk_available_gb = payload.disk_available_gb or node.disk_available_gb
    node.network_upload_mbps = payload.network_upload_mbps or node.network_upload_mbps
    node.network_download_mbps = payload.network_download_mbps or node.network_download_mbps
    node.latency_ms = payload.latency_ms or node.latency_ms
    node.last_heartbeat = datetime.utcnow()
    
    # Anomaly evaluation
    is_anomaly, anomaly_reason = anomaly_detector.evaluate_node_health(node)
    if is_anomaly:
        node.status = "UNHEALTHY"
        await log_event(
            level="WARNING",
            component="monitoring",
            message=f"Anomaly detected on {node.node_id}: {anomaly_reason}",
            node_id=node.node_id,
            db_session=db
        )
    elif node.status in ("OFFLINE", "UNHEALTHY") and not is_anomaly:
        node.status = "BUSY" if node.current_task_id else "ONLINE"
    
    # Record history
    history = NodeMetricHistory(
        node_id=node.node_id,
        cpu_usage=node.cpu_usage,
        ram_usage_percent=node.ram_usage_percent,
        gpu_usage_percent=node.gpu_usage_percent,
        latency_ms=node.latency_ms,
        timestamp=datetime.utcnow()
    )
    db.add(history)
    await db.commit()
    
    # Broadcast live telemetry
    await user_ws_manager.broadcast("node_telemetry", {
        "node_id": node.node_id,
        "cpu_usage": node.cpu_usage,
        "ram_usage_percent": node.ram_usage_percent,
        "gpu_usage_percent": node.gpu_usage_percent,
        "latency_ms": node.latency_ms,
        "status": node.status,
        "current_task_id": node.current_task_id,
        "timestamp": node.last_heartbeat.isoformat()
    })
    
    return {"status": "ok", "node_status": node.status}

@router.post("/{node_id}/benchmark", response_model=NodeResponse)
async def update_node_benchmark(node_id: str, payload: NodeBenchmarkScoreUpdate, db: AsyncSession = Depends(get_db)):
    query = select(VolunteerNode).where(VolunteerNode.node_id == node_id)
    result = await db.execute(query)
    node = result.scalars().first()
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    node.compute_score = payload.compute_score
    node.memory_score = payload.memory_score
    node.gpu_score = payload.gpu_score
    node.network_score = payload.network_score
    node.overall_capability_score = payload.overall_capability_score
    
    await db.commit()
    await db.refresh(node)
    
    await log_event(
        level="INFO",
        component="volunteer",
        message=f"Node {node_id} benchmark updated. Overall capability score: {node.overall_capability_score:.2f}",
        node_id=node_id,
        db_session=db
    )
    return node

@router.get("", response_model=NodeListResponse)
async def list_nodes(db: AsyncSession = Depends(get_db)):
    # Check for nodes that haven't sent heartbeats recently
    cutoff = datetime.utcnow() - timedelta(seconds=settings.HEARTBEAT_TIMEOUT_SECONDS)
    
    query = select(VolunteerNode).order_by(VolunteerNode.node_id.asc())
    result = await db.execute(query)
    nodes = result.scalars().all()
    
    updated_nodes = []
    online = busy = idle = unhealthy = offline = 0
    
    for n in nodes:
        if n.last_heartbeat < cutoff and n.status != "OFFLINE":
            n.status = "OFFLINE"
            await log_event(
                level="WARNING",
                component="monitoring",
                message=f"Node {n.node_id} marked OFFLINE (heartbeat timed out)",
                node_id=n.node_id,
                db_session=db
            )
        
        if n.status == "OFFLINE":
            offline += 1
        elif n.status == "UNHEALTHY":
            unhealthy += 1
        elif n.status == "BUSY":
            busy += 1
        elif n.status == "ONLINE":
            online += 1
            idle += 1
        else:
            idle += 1
            
        updated_nodes.append(n)
    
    await db.commit()
    
    return NodeListResponse(
        total=len(updated_nodes),
        online_count=online + busy,
        busy_count=busy,
        idle_count=idle,
        unhealthy_count=unhealthy,
        offline_count=offline,
        nodes=[NodeResponse.model_validate(n) for n in updated_nodes]
    )

@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(node_id: str, db: AsyncSession = Depends(get_db)):
    query = select(VolunteerNode).where(VolunteerNode.node_id == node_id)
    result = await db.execute(query)
    node = result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node

@router.get("/{node_id}/history")
async def get_node_metric_history(node_id: str, limit: int = 50, db: AsyncSession = Depends(get_db)):
    query = (
        select(NodeMetricHistory)
        .where(NodeMetricHistory.node_id == node_id)
        .order_by(desc(NodeMetricHistory.timestamp))
        .limit(limit)
    )
    result = await db.execute(query)
    records = result.scalars().all()
    return list(reversed([
        {
            "cpu_usage": r.cpu_usage,
            "ram_usage_percent": r.ram_usage_percent,
            "gpu_usage_percent": r.gpu_usage_percent,
            "latency_ms": r.latency_ms,
            "timestamp": r.timestamp.isoformat()
        }
        for r in records
    ]))

@router.get("/client/download")
async def download_volunteer_client():
    """Package and stream the entire standalone volunteer_node directory as a zip."""
    volunteer_dir = BASE_DIR / "volunteer_node"
    if not volunteer_dir.exists():
        raise HTTPException(status_code=404, detail="Volunteer node package directory not found.")
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in volunteer_dir.rglob("*"):
            if file_path.is_file() and not file_path.name.endswith(".pyc") and "__pycache__" not in str(file_path):
                arcname = file_path.relative_to(volunteer_dir.parent)
                zip_file.write(file_path, arcname)
    
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=neurobroker_volunteer_client.zip"}
    )
