import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from backend.app.config import settings
from backend.app.database import init_db, AsyncSessionLocal
from backend.app.models.node import VolunteerNode
from backend.app.api.auth import router as auth_router
from backend.app.api.nodes import router as nodes_router
from backend.app.api.datasets import router as datasets_router
from backend.app.api.models import router as models_router
from backend.app.api.jobs import router as jobs_router
from backend.app.api.admin import router as admin_router
from backend.app.ws.user_ws import user_ws_manager
from backend.app.ws.volunteer_ws import volunteer_ws_manager
from backend.app.logging.logger import broker_logger, log_event

# Heartbeat watchdog task
async def heartbeat_watchdog():
    """Periodically check node heartbeats and mark inactive nodes as OFFLINE."""
    while True:
        try:
            await asyncio.sleep(5)
            cutoff = datetime.utcnow() - timedelta(seconds=settings.HEARTBEAT_TIMEOUT_SECONDS)
            async with AsyncSessionLocal() as db:
                query = select(VolunteerNode).where(
                    VolunteerNode.status.in_(["ONLINE", "IDLE", "BUSY", "UNHEALTHY"]),
                    VolunteerNode.last_heartbeat < cutoff
                )
                res = await db.execute(query)
                stale_nodes = res.scalars().all()
                for node in stale_nodes:
                    node.status = "OFFLINE"
                    node.current_task_id = None
                    await log_event(
                        "WARNING", "monitoring",
                        f"Node {node.node_id} marked OFFLINE due to missed heartbeats.",
                        node_id=node.node_id, db_session=db
                    )
                    await user_ws_manager.broadcast("node_status_change", {
                        "node_id": node.node_id,
                        "status": "OFFLINE"
                    })
                if stale_nodes:
                    await db.commit()
        except asyncio.CancelledError:
            break
        except Exception as e:
            broker_logger.error(f"Error in heartbeat watchdog: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database and Tables
    broker_logger.info("Initializing NeuroBroker Database and file storage...")
    await init_db()
    
    # Start heartbeat watchdog in background
    watchdog_task = asyncio.create_task(heartbeat_watchdog())
    broker_logger.info("NeuroBroker Server initialized and ready.")
    
    yield
    
    # Shutdown
    watchdog_task.cancel()
    broker_logger.info("NeuroBroker Server shutdown.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Resource-Aware Centralized Compute Brokerage Engine for Volunteer Distributed Deep Learning Training",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST Routers
app.include_router(auth_router)
app.include_router(nodes_router)
app.include_router(datasets_router)
app.include_router(models_router)
app.include_router(jobs_router)
app.include_router(admin_router)

# WebSocket Endpoint for Dashboard Users
@app.websocket("/ws/user/{user_id}")
async def websocket_user_endpoint(websocket: WebSocket, user_id: str):
    await user_ws_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle client ping or subscription if needed
            await websocket.send_json({"event": "pong", "data": "received"})
    except WebSocketDisconnect:
        await user_ws_manager.disconnect(websocket, user_id)
    except Exception:
        await user_ws_manager.disconnect(websocket, user_id)

# WebSocket Endpoint for Volunteer Nodes
@app.websocket("/ws/volunteer")
async def websocket_volunteer_endpoint(websocket: WebSocket):
    # Wait for initial registration or identify message
    await websocket.accept()
    node_id = None
    try:
        init_data = await websocket.receive_json()
        node_id = init_data.get("node_id")
        if not node_id:
            await websocket.close(code=1008, reason="Missing node_id in init payload")
            return
            
        await volunteer_ws_manager.connect(node_id, websocket)
        
        while True:
            message = await websocket.receive_json()
            msg_type = message.get("type")
            payload = message.get("data", {})
            
            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
            elif msg_type == "task_progress":
                # Forward to user dashboards
                await user_ws_manager.broadcast("task_progress", payload)
            elif msg_type == "task_complete":
                await user_ws_manager.broadcast("task_completed", payload)
                
    except WebSocketDisconnect:
        if node_id:
            await volunteer_ws_manager.disconnect(node_id, websocket)
    except Exception as e:
        broker_logger.error(f"Volunteer WebSocket error: {e}")
        if node_id:
            await volunteer_ws_manager.disconnect(node_id, websocket)

@app.get("/")
async def root_status():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "ONLINE",
        "timestamp": datetime.utcnow().isoformat()
    }
