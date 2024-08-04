import pytest

from scraping_houses.utils import get_client


@pytest.fixture
def client():
    with get_client() as client:
        yield client
