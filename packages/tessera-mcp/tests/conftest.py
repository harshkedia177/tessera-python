import pytest

from tessera_memory import AsyncTessera

BASE_URL = "https://api.tessera.test"
API_KEY = "tsk_test_key"


@pytest.fixture
async def client():
    c = AsyncTessera(api_key=API_KEY, base_url=BASE_URL)
    yield c
    await c.aclose()
