from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

import jwt
from config import settings
from main import app, get_session
from src.models import Suggestion

# Test database setup
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def override_get_session():
        return session

    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def create_test_token(user_id: str = "test_user"):
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=30),
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return token


def test_read_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"hello": "world"}


def test_create_suggestion_without_auth(client: TestClient):
    response = client.post("/suggestions", json={"comment": "Test suggestion"})
    assert response.status_code == 403
    assert "Not authenticated" in response.json()["detail"]


def test_create_suggestion_with_auth(client: TestClient):
    token = create_test_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/suggestions", json={"comment": "Test suggestion"}, headers=headers
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["comment"] == "Test suggestion"
    assert "id" in data
    assert "created_at" in data
    assert data["is_solved"] is False


def test_read_suggestions(client: TestClient):
    # Create a suggestion first
    token = create_test_token()
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/suggestions", json={"comment": "Test suggestion"}, headers=headers)

    # Read suggestions
    response = client.get("/suggestions", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["comment"] == "Test suggestion"


def test_create_suggestion_with_expired_token(client: TestClient):
    # Create an expired token
    payload = {
        "sub": "test_user",
        "exp": datetime.utcnow() - timedelta(minutes=1),  # Expired 1 minute ago
        "iat": datetime.utcnow() - timedelta(minutes=10),
    }
    expired_token = jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.post(
        "/suggestions", json={"comment": "Test suggestion"}, headers=headers
    )
    assert response.status_code == 401
    assert "Token expired" in response.json()["detail"]


def test_create_suggestion_with_invalid_token(client: TestClient):
    # Create an invalid token (wrong signature)
    payload = {
        "sub": "test_user",
        "exp": datetime.utcnow() + timedelta(minutes=30),
        "iat": datetime.utcnow(),
    }
    invalid_token = jwt.encode(
        payload, "wrong_secret_key", algorithm=settings.JWT_ALGORITHM
    )
    headers = {"Authorization": f"Bearer {invalid_token}"}
    response = client.post(
        "/suggestions", json={"comment": "Test suggestion"}, headers=headers
    )
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]
