import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from backend.app import app, Base, get_db

# Use the DATABASE_URL from environment — your pipeline sets this
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5433/ecommerce")

engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables before tests run
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override the app's database dependency with the test one
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    """Wipe tables before every test so tests don't bleed into each other"""
    yield
    db = TestingSessionLocal()
    db.execute(text("DELETE FROM order_items"))
    db.execute(text("DELETE FROM orders"))
    db.execute(text("DELETE FROM products"))
    db.commit()
    db.close()