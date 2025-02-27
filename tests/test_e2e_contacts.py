from unittest.mock import  patch, AsyncMock
from src.services.auth import auth_service



def test_read_all_contacts(client, get_token, monkeypatch):
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/contacts", headers=headers)
        assert response.status_code == 200, response.text
        data = response.json()
        print(response.json())
        assert len(data) == 0


def test_create_contact(client, get_token, monkeypatch):
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/contacts", headers=headers, json={
            "first_name": "test",
            "last_name": "test",
            "email": "test@gmail.com",
            "phone_number": "0123456",
            "birthday": "2020-02-25"
        })
        assert response.status_code == 201, response.text
        data = response.json()
        assert "id" in data
        assert data["first_name"] == "test"
        assert data["last_name"] == "test"
        assert data["email"] == "test@gmail.com"
        assert data["phone_number"] == "0123456"
        assert data["birthday"] == "2020-02-25"


def test_read_birthday(client, get_token, monkeypatch):
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/contacts/birthdays", headers=headers)

        assert response.status_code == 200, response.text


def test_read_by_contact_id(client, get_token, monkeypatch):
    contact_id = 1
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/contacts/{contact_id}", headers=headers)

        assert response.status_code == 200, response.text
        data = response.json()
        assert "id" in data
        assert data["first_name"] == "test"
        assert data["last_name"] == "test"
        assert data["email"] == "test@gmail.com"
        assert data["phone_number"] == "0123456"
        assert data["birthday"] == "2020-02-25"

def test_read_by_contact_id_none_or_not(client, get_token, monkeypatch):
    contact_id = 10
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/contacts/{contact_id}", headers=headers)

        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "Contact not found"
def test_read_contact_first_name(client, get_token, monkeypatch):
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/contacts/first_name/", headers=headers, params={"contact_first_name": "test"})

        assert response.status_code == 200, response.text

def test_read_contact_first_name_none_or_not(client, get_token, monkeypatch):
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/contacts/first_name/", headers=headers, params={"contact_first_name": "test123"})

        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "Contact not found"

def test_read_contact_last_name(client, get_token, monkeypatch):
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/contacts/last_name/", headers=headers, params={"contact_last_name": "test"})

        assert response.status_code == 200, response.text

def test_read_contact_last_name_none_or_not(client, get_token, monkeypatch):
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/contacts/last_name/", headers=headers, params={"contact_last_name": "test123"})

        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "Contact not found"

def test_read_contact_email(client, get_token, monkeypatch):
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/contacts/email/", headers=headers, params={"contact_email": "test@gmail.com"})

        assert response.status_code == 200, response.text

def test_read_contact_email_none_or_not(client, get_token, monkeypatch):
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/contacts/email/", headers=headers, params={"contact_email": "test123@gmail.com"})

        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "Contact not found"

def test_update_contact(client, get_token, monkeypatch):
    contact_id = 1
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put(f"/api/contacts/{contact_id}", headers=headers, json={
            "first_name": "test1",
            "last_name": "test1",
            "email": "test@gmail.com",
            "phone_number": "0123456",
            "birthday": "2020-02-25"
        })
        assert response.status_code == 200, response.text
        data = response.json()
        assert "id" in data
        assert data["first_name"] == "test1"
        assert data["last_name"] == "test1"
        assert data["email"] == "test@gmail.com"
        assert data["phone_number"] == "0123456"
        assert data["birthday"] == "2020-02-25"


def test_update_contact_none_or_not(client, get_token, monkeypatch):
    contact_id = 10
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put(f"/api/contacts/{contact_id}", headers=headers, json={
            "first_name": "test1",
            "last_name": "test1",
            "email": "test@gmail.com",
            "phone_number": "0123456",
            "birthday": "2020-02-25"
        })
        assert response.status_code == 404, response.text

def test_delete_contact(client, get_token, monkeypatch):
    contact_id = 1
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(f"/api/contacts/{contact_id}", headers=headers, params={"contact_id": 1})
        assert response.status_code == 204, response.text
