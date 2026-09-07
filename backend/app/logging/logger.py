import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from backend.app.config import settings

# Setup standard python root logger
log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format=log_format,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.LOGS_DIR / "neurobroker.log")
    ]
)

# Silence excessively verbose 3rd party loggers that flood disk I/O
logging.getLogger("aiosqlite").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.INFO)

broker_logger = logging.getLogger("NeuroBroker")

async def log_event(
    level: str,
    component: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    job_id: Optional[int] = None,
    node_id: Optional[str] = None,
    db_session = None
):
    """Log to python logger and optionally save to DB system_logs asynchronously."""
    log_msg = f"[{component.upper()}] {message}"
    if level.upper() == "INFO":
        broker_logger.info(log_msg)
    elif level.upper() == "WARNING":
        broker_logger.warning(log_msg)
    elif level.upper() in ("ERROR", "CRITICAL"):
        broker_logger.error(log_msg)
    else:
        broker_logger.debug(log_msg)

    if db_session:
        try:
            from backend.app.models.log import SystemLog
            log_entry = SystemLog(
                level=level.upper(),
                component=component,
                message=message,
                details=details or {},
                job_id=job_id,
                node_id=node_id,
                timestamp=datetime.utcnow()
            )
            db_session.add(log_entry)
            await db_session.commit()
        except Exception as e:
            broker_logger.error(f"Failed to write log to DB: {e}")
