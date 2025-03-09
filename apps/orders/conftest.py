import pytest
from django.core.cache import cache

# fmt: off
pytest_plugins = [
]
# fmt: on


@pytest.fixture(autouse=True)
def _cache():
    """Clear django cache after each test run."""
    yield
    cache.clear()
