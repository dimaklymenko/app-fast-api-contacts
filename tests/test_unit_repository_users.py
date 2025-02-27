import unittest
from unittest.mock import MagicMock, AsyncMock

from src.repository.users import *


class TestAsyncTodo(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        # self.user = User(id=1, username="test_user", email="test@gmail.com", password="qwerty")
        self.session = AsyncMock(spec=AsyncSession)

    async def test_get_user_by_email(self):
        self.user = User(id=1, username="test_user", email="test@gmail.com", password="qwerty")
        mocked_users = MagicMock()
        mocked_users.scalar_one_or_none.return_value = self.user
        self.session.execute.return_value = mocked_users
        result = await get_user_by_email("test@gmail.com", self.session)
        self.assertEqual(result, self.user)

    async def test_get_user_by_email_none(self):
        mocked_users = MagicMock()
        mocked_users.scalar_one_or_none.return_value = None
        self.session.execute.return_value = mocked_users
        result = await get_user_by_email("test@gmail.com", self.session)
        self.assertIsNone(result)


    async def test_create_user(self):
        body = UserSchema(username="test_user", email="test@gmail.com", password="qwerty")

        self.session.add = MagicMock()
        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()

        result = await create_user(body, self.session)

        self.session.add.assert_called_once()
        self.session.commit.assert_awaited_once()
        self.session.refresh.assert_awaited_once_with(result)

        self.assertEqual(result.username, body.username)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.password, body.password)
        self.assertTrue(hasattr(result, "avatar"))  # Перевіряємо, що є avatar



    async def test_update_token(self):
        self.user = User(id=1, username="test_user", email="test@gmail.com", password="qwerty", refresh_token="token1")
        self.session.commit = AsyncMock()
        await update_token(self.user,"token", self.session)
        self.session.commit.assert_awaited_once()
        self.assertEqual(self.user.refresh_token, "token")

    async def test_confirmed_email(self):
        self.user = User(id=1, username="test_user", email="test@gmail.com", password="qwerty", confirmed=False)
        mocked_users = MagicMock()
        mocked_users.scalar_one_or_none.return_value = self.user
        self.session.execute.return_value = mocked_users
        self.session.commit = AsyncMock()
        await confirmed_email(self.user.email, self.session)
        self.session.commit.assert_awaited_once()
        self.assertTrue(self.user.confirmed)


    async def test_update_avatar_url(self) -> User:
        self.user = User(id=1, username="test_user", email="test@gmail.com", password="qwerty", avatar=None)
        mocked_users = MagicMock()
        mocked_users.scalar_one_or_none.return_value = self.user
        self.session.execute.return_value = mocked_users
        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()
        new_avatar_url = "https://example.com/avatar.jpg"
        result = await update_avatar_url(self.user.email, new_avatar_url, self.session)
        self.session.commit.assert_awaited_once()
        self.session.refresh.assert_awaited_once_with(result)

        self.assertEqual(result.avatar, new_avatar_url)
        self.assertEqual(self.user.avatar, new_avatar_url)



if __name__ == "__main__":
    unittest.main()
