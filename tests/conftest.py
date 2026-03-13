import os
import pytest

@pytest.fixture(autouse=True)
def setup_test_env():
    """Asegura que las variables de entorno necesarias estén presentes para los tests."""
    os.environ["API_KEY"] = "dummy-key-for-testing-purposes-only-32-chars"
    os.environ["ALLOWED_ORIGINS"] = '["*"]'
