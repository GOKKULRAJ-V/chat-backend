

## backend/tests/test_api.py (fixed):
# python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert response.headers["x-api-version"] == "v1"

def test_chat_endpoint_success():
    test_data = {
        "message": "Need a quote for 2 centrifuges in Texas",
        "context": {
            "email": "test@example.com",
            "channel": "web"
        }
    }
    
    response = client.post("/chat", json=test_data)
    assert response.status_code == 200
    assert response.headers["x-api-version"] == "v1"
    
    data = response.json()
    
    # Check response structure
    assert "reply" in data
    assert "triage" in data
    assert "meta" in data
    
    # Check triage structure
    triage = data["triage"]
    assert "intent" in triage
    assert "confidence" in triage
    assert "fields" in triage
    assert "summary" in triage
    
    # Check fields structure
    fields = triage["fields"]
    assert "company" in fields
    assert "contact_email" in fields
    assert "region" in fields
    assert "product" in fields
    assert "quantity" in fields
    assert "urgency" in fields
    
    # Check meta structure
    meta = data["meta"]
    assert "model" in meta
    assert "latency_ms" in meta
    assert meta["model"] == "mock-v1"

def test_chat_endpoint_empty_message():
    test_data = {
        "message": "",
        "context": {
            "email": "test@example.com",
            "channel": "web"
        }
    }
    
    response = client.post("/chat", json=test_data)
    assert response.status_code == 422  # Pydantic validation error
    assert response.headers["x-api-version"] == "v1"

def test_chat_endpoint_missing_message():
    test_data = {
        "context": {
            "email": "test@example.com",
            "channel": "web"
        }
    }
    
    response = client.post("/chat", json=test_data)
    assert response.status_code == 422  # Pydantic validation error
    assert response.headers["x-api-version"] == "v1"

def test_chat_endpoint_different_intents():
    test_cases = [
        ("I need support with my machine", "support"),
        ("What's the status of my order?", "followup"),
        ("Need maintenance service", "maintenance"),
        ("Hello there", "other"),
    ]
    
    for message, expected_intent in test_cases:
        test_data = {
            "message": message,
            "context": {
                "email": "test@example.com",
                "channel": "web"
            }
        }
        
        response = client.post("/chat", json=test_data)
        assert response.status_code == 200
        data = response.json()
        assert data["triage"]["intent"] == expected_intent