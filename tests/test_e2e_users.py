from unittest.mock import patch, AsyncMock, MagicMock

import pytest
from fastapi import UploadFile


from src.routes.users import get_current_user
from src.services.auth import auth_service
from sqlalchemy.ext.asyncio import AsyncSession


def test_get_me(client, get_token, monkeypatch):
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("api/users/me", headers=headers)
        assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_get_current_user():
    # Моки для залежностей
    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = "fake_file_content"

    mock_user = MagicMock()
    mock_user.email = "test@example.com"

    mock_db = AsyncMock(spec=AsyncSession)

    # Моки для cloudinary
    mock_cloudinary_upload = MagicMock(return_value={"version": "123"})
    mock_cloudinary_image = MagicMock()
    mock_cloudinary_image.build_url.return_value = "http://example.com/avatar.jpg"

    # Моки для repositories_users
    mock_update_avatar_url = AsyncMock(return_value=mock_user)

    # Моки для auth_service
    mock_cache = MagicMock()
    mock_cache.set = MagicMock()
    mock_cache.expire = MagicMock()

    # Мок для pickle.dumps
    mock_pickle_dumps = MagicMock(return_value=b"mock_serialized_user")

    # Заміна реальних залежностей на моки
    with patch("cloudinary.uploader.upload", mock_cloudinary_upload), \
            patch("cloudinary.CloudinaryImage", return_value=mock_cloudinary_image), \
            patch("src.repository.users.update_avatar_url", mock_update_avatar_url), \
            patch("src.services.auth.auth_service.cache", mock_cache), \
            patch("src.services.auth.auth_service.get_current_user", return_value=mock_user), \
            patch("pickle.dumps", mock_pickle_dumps):  # Додаємо мок для pickle.dumps

        # Виклик тестованої функції
        result = await get_current_user(file=mock_file, user=mock_user, db=mock_db)

        # Перевірка результатів
        mock_cloudinary_upload.assert_called_once_with("fake_file_content", public_id="Web16/test@example.com",
                                                       owerite=True)
        mock_cloudinary_image.build_url.assert_called_once_with(width=250, height=250, crop="fill", version="123")
        mock_update_avatar_url.assert_called_once_with("test@example.com", "http://example.com/avatar.jpg", mock_db)
        mock_cache.set.assert_called_once_with("test@example.com",
                                               b"mock_serialized_user")  # Використовуємо мокований результат
        mock_cache.expire.assert_called_once_with("test@example.com", 300)

        assert result == mock_user


