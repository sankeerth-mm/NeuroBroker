import pytest
import pytest_asyncio
from backend.app.database import init_db

@pytest_asyncio.fixture(autouse=True)
async def setup_test_database():
    """Ensure database tables are created before running tests."""
    await init_db()
    yield
