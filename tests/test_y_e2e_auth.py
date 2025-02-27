from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User, PasswordResetToken

from src.routes.auth import refresh_token
from src.services.auth import auth_service
from src.services import email
from src.repository import users as repositories_users

from tests.conftest import TestingSessionLocal
from src.conf import messages

user_data = {"username": "agent007", "email": "agent007@gmail.com", "password": "12345678"}


def test_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response = client.post("/api/auth/signup", json=user_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "password" not in data
    assert "avatar" in data
    assert "id" in data


def test_repeat_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response = client.post("/api/auth/signup", json=user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == messages.ACCOUNT_EXIST


def test_not_confirmed_login(client):
    response = client.post("api/auth/login",
                           data={"username": user_data.get("email"), "password": user_data.get("password")})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.EMAIL_NOT_CONFIRMED




@pytest.mark.asyncio
async def test_login(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).where(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()

    response = client.post("api/auth/login",
                           data={"username": user_data.get("email"), "password": user_data.get("password")})
    assert response.status_code == 201, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data


def test_wrong_password_login(client):
    response = client.post("api/auth/login",
                           data={"username": user_data.get("email"), "password": "password"})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == messages.INVALID_PASSWORD


def test_wrong_email_login(client):
    response = client.post("api/auth/login",
                           data={"username": "email", "password": user_data.get("password")})
    assert response.status_code == 401, response.text
    data = response.json()
    print(data)
    assert data["detail"] == messages.INVALID_EMAIL


def test_validation_error_login(client):
    response = client.post("api/auth/login",
                           data={"password": user_data.get("password")})
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data




@pytest.mark.asyncio
async def test_refresh_token_success(client, get_token):
    # Мок-об'єкти для залежностей
    mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=get_token)
    mock_db = AsyncMock(spec=AsyncSession)

    # Мок-методи для сервісів та репозиторіїв
    with patch("src.repository.users.get_user_by_email", new_callable=AsyncMock) as mock_get_user_by_email:
        mock_get_user_by_email.return_value = MagicMock(refresh_token=get_token)

        auth_service.decode_refresh_token = AsyncMock(return_value=user_data.get("email"))
        auth_service.create_access_token = AsyncMock(return_value="new_access_token")
        auth_service.create_refresh_token = AsyncMock(return_value="new_refresh_token")

        # Виклик функції
        response = await refresh_token(credentials=mock_credentials, db=mock_db)

        # Перевірка результатів
        assert response == {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "token_type": "bearer"
        }
        mock_get_user_by_email.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_token_invalid_token(client, get_token):
    # Мок-об'єкти для залежностей
    mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_refresh_token")
    mock_db = AsyncMock(spec=AsyncSession)

    # Мок-методи для сервісів та репозиторіїв
    auth_service.decode_refresh_token = AsyncMock(return_value=user_data.get("email"))
    repositories_users.get_user_by_email = AsyncMock(return_value=MagicMock(refresh_token=get_token))
    repositories_users.update_token = AsyncMock()

    # Очікування винятку
    with pytest.raises(HTTPException) as exc_info:
        await refresh_token(credentials=mock_credentials, db=mock_db)

    # Перевірка винятку
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == messages.INVALID_REFRESH_TOKEN
    repositories_users.update_token.assert_called_once()


@pytest.mark.asyncio
async def test_confirmed_email_success(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).where(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()

        auth_service.get_email_from_token = AsyncMock(return_value=current_user.email)
        repositories_users.get_user_by_email = AsyncMock(return_value=current_user)

        if current_user.confirmed == False:
            await repositories_users.confirmed_email(current_user.email, session)
            await session.commit()

    # Перевірка результатів
    assert current_user.confirmed == True




@pytest.mark.asyncio
async def test_confirmed_email_already_confirmed(client, mocker):
    token = "test_token"
    email = "test@example.com"

    mocker.patch.object(auth_service, "get_email_from_token", AsyncMock(return_value=email))

    mock_user = MagicMock(spec=User)
    mock_user.email = email
    mock_user.confirmed = True

    mocker.patch.object(repositories_users, "get_user_by_email", AsyncMock(return_value=mock_user))

    response = client.get(f"api/auth/confirmed_email/{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Your email is already confirmed"}

@pytest.mark.asyncio
async def test_confirmed_email_success(client, mocker):
    token = "test_token"
    email = "test@example.com"

    mocker.patch.object(auth_service, "get_email_from_token", AsyncMock(return_value=email))


    mock_user = MagicMock(spec=User)
    mock_user.email = email
    mock_user.confirmed = False

    mocker.patch.object(repositories_users, "get_user_by_email", AsyncMock(return_value=mock_user))

    response = client.get(f"api/auth/confirmed_email/{token}")

    mocker.patch.object(repositories_users, "confirmed_email", AsyncMock())
    mock_user.confirmed = True

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Email confirmed"}
    assert mock_user.confirmed == True

@pytest.mark.asyncio
async def test_confirmed_email_user_not_found(client, mocker):
    token = "test_token"
    email = "test@example.com"

    mocker.patch.object(auth_service, "get_email_from_token", AsyncMock(return_value=email))
    mocker.patch.object(repositories_users, "get_user_by_email", AsyncMock(return_value=None))

    response = client.get(f"api/auth/confirmed_email/{token}")

    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == messages.VERIFICATION_ERROR



@pytest.mark.asyncio
async def test_request_email_already_confirmed(client, mocker):

    mock_user = MagicMock(spec=User)
    mocker.patch.object(repositories_users, "get_user_by_email", AsyncMock(return_value=mock_user))
    mock_user.confirmed = True

    response = client.post("api/auth/request_email",json={"email": "test@example.com"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Your email is already confirmed"}


@pytest.mark.asyncio
async def test_request_email_sends_email(client, mocker):
    mock_user = MagicMock(spec=User)
    mock_user.confirmed = False
    mock_user.email = "test@example.com"
    mocker.patch.object(repositories_users, "get_user_by_email", AsyncMock(return_value=mock_user))

    response = client.post("api/auth/request_email", json={"email": "test@example.com"})

    mocker.patch.object(email, "send_email", AsyncMock())


    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Check your email for confirmation."}


@pytest.mark.asyncio
async def test_password_reset_request(client, mocker):
    mock_user = MagicMock()
    mock_user.email = "test@example.com"

    mocker.patch.object(repositories_users, "get_user_by_email", return_value=mock_user)
    mocker.patch.object(auth_service, "generate_reset_token", return_value="mock_token")
    mocker.patch("src.services.email.send_password_reset_email", new_callable=AsyncMock)


    response = client.post("api/auth/password-reset-request", json={"email": "test@example.com"})


    assert response.status_code == 200
    assert response.json() == {"message": "Password reset link has been sent to your email."}

@pytest.mark.asyncio
async def test_password_reset_request_email_not_found(client, mocker):
    mocker.patch.object(repositories_users, "get_user_by_email", return_value=None)

    response = client.post("api/auth/password-reset-request", json={"email": "test@example.com"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Email not found"}




@pytest.mark.asyncio
async def test_reset_password_success(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).where(User.email == "deadpool@example.com"))
        current_user = current_user.scalar_one_or_none()
        c = PasswordResetToken(token="valid_token", email="deadpool@example.com",
                                    expiration=datetime.utcnow() + timedelta(hours=1))
        session.add(c)
        await session.commit()

    response = client.post("api/auth/reset-password", json={"token": "valid_token", "new_password": "1234567"})

    assert response.json() == {"message": "Password has been reset successfully."}



@pytest.mark.asyncio
async def test_reset_password_invalid_token(client):
    response = client.post("api/auth/reset-password", json={"token": "valid_token", "new_password": "1234567"})
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == messages.INVALID_OR_EXPIRED_TOKEN

@pytest.mark.asyncio
async def test_reset_password_invalid_expiration(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).where(User.email == "deadpool@example.com"))
        current_user = current_user.scalar_one_or_none()
        c = PasswordResetToken(token="valid_token", email="deadpool@example.com",
                                    expiration=datetime.utcnow() - timedelta(hours=2))
        session.add(c)
        await session.commit()

    response = client.post("api/auth/reset-password", json={"token": "valid_token", "new_password": "1234567"})

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == messages.INVALID_OR_EXPIRED_TOKEN


@pytest.mark.asyncio
async def test_reset_password_invalid_user(client):
    async with TestingSessionLocal() as session:
        await session.execute(delete(PasswordResetToken))
        await session.commit()
        current_user = await session.execute(select(User).where(User.email == "deadpool@example.com"))
        current_user = current_user.scalar_one_or_none()
        c = PasswordResetToken(token="valid_token", email="deadpool1@example.com",
                                    expiration=datetime.utcnow() + timedelta(hours=1))
        session.add(c)
        await session.commit()

    response = client.post("api/auth/reset-password", json={"token": "valid_token", "new_password": "1234567"})

    assert response.status_code == 404, response.text
