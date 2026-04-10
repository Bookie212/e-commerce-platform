from fastapi import status


# ─────────────────────────────────────────
# Health check
# ─────────────────────────────────────────

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "healthy"


# ─────────────────────────────────────────
# Products
# ─────────────────────────────────────────

def test_create_product(client):
    response = client.post("/products", json={
        "name": "Test Product",
        "description": "A test product",
        "price": 29.99,
        "stock": 10
    })
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Test Product"
    assert data["price"] == 29.99
    assert data["stock"] == 10
    assert "id" in data


def test_create_product_missing_required_fields(client):
    response = client.post("/products", json={
        "description": "Missing name and price"
    })
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_products_empty(client):
    response = client.get("/products")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_get_products(client):
    # Create a product first
    client.post("/products", json={
        "name": "Product A",
        "price": 10.00,
        "stock": 5
    })
    response = client.get("/products")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_get_product_by_id(client):
    created = client.post("/products", json={
        "name": "Product B",
        "price": 15.00,
        "stock": 3
    }).json()

    response = client.get(f"/products/{created['id']}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Product B"


def test_get_product_not_found(client):
    response = client.get("/products/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_product(client):
    created = client.post("/products", json={
        "name": "Old Name",
        "price": 10.00,
        "stock": 5
    }).json()

    response = client.put(f"/products/{created['id']}", json={
        "name": "New Name",
        "price": 20.00,
        "stock": 8
    })
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "New Name"
    assert response.json()["price"] == 20.00


def test_update_product_not_found(client):
    response = client.put("/products/99999", json={
        "name": "Ghost",
        "price": 5.00,
        "stock": 1
    })
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_product(client):
    created = client.post("/products", json={
        "name": "To Delete",
        "price": 5.00,
        "stock": 1
    }).json()

    response = client.delete(f"/products/{created['id']}")
    assert response.status_code == status.HTTP_200_OK

    # Confirm it's gone
    response = client.get(f"/products/{created['id']}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_product_not_found(client):
    response = client.delete("/products/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ─────────────────────────────────────────
# Orders
# ─────────────────────────────────────────

def create_test_product(client, name="Test Product", price=10.00, stock=20):
    """Helper to create a product and return its id"""
    response = client.post("/products", json={
        "name": name,
        "price": price,
        "stock": stock
    })
    return response.json()


def test_create_order(client):
    product = create_test_product(client)

    response = client.post("/orders", json={
        "customer_name": "Bukola",
        "customer_email": "bukola@example.com",
        "items": [
            {"product_id": product["id"], "quantity": 2}
        ]
    })
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["customer_name"] == "Bukola"
    assert data["total_amount"] == 20.00   # 2 × 10.00
    assert data["status"] == "pending"
    assert len(data["items"]) == 1


def test_create_order_reduces_stock(client):
    product = create_test_product(client, stock=10)

    client.post("/orders", json={
        "customer_name": "Bukola",
        "customer_email": "bukola@example.com",
        "items": [{"product_id": product["id"], "quantity": 3}]
    })

    updated = client.get(f"/products/{product['id']}").json()
    assert updated["stock"] == 7   # 10 - 3


def test_create_order_insufficient_stock(client):
    product = create_test_product(client, stock=1)

    response = client.post("/orders", json={
        "customer_name": "Bukola",
        "customer_email": "bukola@example.com",
        "items": [{"product_id": product["id"], "quantity": 5}]
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Insufficient stock" in response.json()["detail"]


def test_create_order_product_not_found(client):
    response = client.post("/orders", json={
        "customer_name": "Bukola",
        "customer_email": "bukola@example.com",
        "items": [{"product_id": 99999, "quantity": 1}]
    })
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_orders_empty(client):
    response = client.get("/orders")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_get_order_by_id(client):
    product = create_test_product(client)
    created = client.post("/orders", json={
        "customer_name": "Bukola",
        "customer_email": "bukola@example.com",
        "items": [{"product_id": product["id"], "quantity": 1}]
    }).json()

    response = client.get(f"/orders/{created['id']}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == created["id"]


def test_get_order_not_found(client):
    response = client.get("/orders/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_order_status(client):
    product = create_test_product(client)
    created = client.post("/orders", json={
        "customer_name": "Bukola",
        "customer_email": "bukola@example.com",
        "items": [{"product_id": product["id"], "quantity": 1}]
    }).json()

    response = client.put(
        f"/orders/{created['id']}/status",
        params={"status": "shipped"}
    )
    assert response.status_code == status.HTTP_200_OK


def test_update_order_status_not_found(client):
    response = client.put(
        "/orders/99999/status",
        params={"status": "shipped"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ─────────────────────────────────────────
# Metrics endpoint
# ─────────────────────────────────────────

def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == status.HTTP_200_OK
    assert "api_requests_total" in response.text