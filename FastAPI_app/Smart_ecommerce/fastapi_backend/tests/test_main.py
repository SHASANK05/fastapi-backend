import pytest
from fastapi.testclient import TestClient

# Import app with fallback for flat or nested structures
try:
    from app.main import app
except (ImportError, ModuleNotFoundError):
    from main import app

client = TestClient(app)


def test_health_check_or_root():
    """Verify that the API root or docs respond properly."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_list_products():
    """Verify that the products listing and discovery endpoint works."""
    response = client.get("/products")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_product_search_and_filter():
    """Verify keyword search returns a list with expected structure."""
    response = client.get("/products?search=Mechanical")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_single_product_and_popularity():
    """Verify fetching product ID 2 succeeds and contains expected keys."""
    response = client.get("/products/2")
    # In case product 2 exists in database
    if response.status_code == 200:
        data = response.json()
        assert data["id"] == 2
        assert "popularity" in data
        assert "price" in data
    else:
        # If product 2 doesn't exist yet, it should return 404
        assert response.status_code == 404


def test_unauthorized_checkout():
    """Verify that checking out without a token is blocked."""
    response = client.post("/cart/checkout")
    assert response.status_code in [401, 403]