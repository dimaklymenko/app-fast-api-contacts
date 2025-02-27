import datetime
import unittest
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.schemas.contact import ContactSchema
from src.repository.contacts import (
    get_contacts,
    get_contact_id,
    get_contact_first_name,
    get_contact_last_name,
    get_contact_email,
    get_contact_birthday,
    create_contact,
    update_contact,
    remove_contact,
)


class TestAsyncTodo(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.user = User(id=1, username="test_user", password="qwerty", confirmed=True)
        self.session = AsyncMock(spec=AsyncSession)

    async def test_get_contacts(self):
        limit = 10
        offset = 0
        contacts = [
            Contact(
                id=1,
                first_name="first_name",
                last_name="last_name",
                email="test@gmail.com",
                phone_number="7777777777",
                birthday=datetime.date(1990, 5, 15),
                user=self.user,
            ),
            Contact(
                id=2,
                first_name="first_name2",
                last_name="last_name2",
                email="test2@gmail.com",
                phone_number="17777777777",
                birthday=datetime.date(1990, 5, 16),
                user=self.user,
            ),
        ]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts
        result = await get_contacts(limit, offset, self.session, self.user)
        self.assertEqual(result, contacts)


    async def test_get_contact_id(self):
        contacts = [
            Contact(
                id=1,
                first_name="first_name",
                last_name="last_name",
                email="test@gmail.com",
                phone_number="7777777777",
                birthday=datetime.date(1990, 5, 15),
                user=self.user,
            )
        ]
        mocked_contacts = MagicMock()
        mocked_contacts.scalar_one_or_none.return_value = contacts

        self.session.execute.return_value = mocked_contacts
        result = await get_contact_id(1, self.session, self.user)
        self.assertEqual(result, contacts)


    async def test_get_contact_id_none(self):
        mocked_contacts = MagicMock()
        mocked_contacts.scalar_one_or_none.return_value = None
        self.session.execute.return_value = mocked_contacts
        result = await get_contact_id(2, self.session, self.user)
        self.assertIsNone(result)

    async def test_get_contact_first_name(self):
        contact_first_name = "FIRst_name"
        contacts = [
            Contact(
                id=1,
                first_name="first_NAme",
                last_name="last_name",
                email="test@gmail.com",
                phone_number="7777777777",
                birthday="01.01.2001",
                user=self.user,
            ),
            Contact(
                id=2,
                first_name="first_name2",
                last_name="last_name2",
                email="test2@gmail.com",
                phone_number="17777777777",
                birthday="02.01.2001",
                user=self.user,
            ),
        ]

        # Мокаємо повернення результату
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = [
            contact
            for contact in contacts
            if contact.first_name.lower() == contact_first_name.lower()
        ]
        self.session.execute.return_value = mocked_contacts

        # Викликаємо функцію
        result = await get_contact_first_name(
            contact_first_name.lower(), self.session, self.user
        )

        # Перевіряємо, чи повертаються лише контакти з правильним last_name
        result_first_names = [c.first_name.lower() for c in result]

        self.assertListEqual(result_first_names, ["first_name"])

    async def test_get_contact_last_name(self):
        contact_last_name = "LAST_Name"
        contacts = [
            Contact(
                id=1,
                first_name="first_name",
                last_name="last_name",
                email="test@gmail.com",
                phone_number="7777777777",
                birthday="01.01.2001",
                user=self.user,
            ),
            Contact(
                id=2,
                first_name="first_name2",
                last_name="last_name2",
                email="test2@gmail.com",
                phone_number="17777777777",
                birthday="02.01.2001",
                user=self.user,
            ),
        ]

        # Мокаємо повернення результату
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = [
            contact
            for contact in contacts
            if contact.last_name.lower() == contact_last_name.lower()
        ]
        self.session.execute.return_value = mocked_contacts

        # Викликаємо функцію
        result = await get_contact_last_name(
            contact_last_name.lower(), self.session, self.user
        )

        # Перевіряємо, чи повертаються лише контакти з правильним last_name
        result_last_names = [c.last_name.lower() for c in result]

        self.assertListEqual(result_last_names, ["last_name"])

    async def test_get_contact_email(self):
        email = "TEST@GMAIL.COM"  # Введений email у верхньому регістрі

        contacts = [
            Contact(
                id=1,
                first_name="first_name",
                last_name="last_name",
                email="test@gmail.com",
                phone_number="7777777777",
                birthday="01.01.2001",
                user=self.user,
            ),
            Contact(
                id=2,
                first_name="first_name2",
                last_name="last_name2",
                email="test2@gmail.com",
                phone_number="17777777777",
                birthday="02.01.2001",
                user=self.user,
            ),
        ]

        # Мокаємо повернення правильного контакту
        mocked_contacts = MagicMock()
        mocked_contacts.scalar_one_or_none.return_value = next(
            (contact for contact in contacts if contact.email.lower() == email.lower()),
            None,
        )
        self.session.execute.return_value = mocked_contacts

        # Викликаємо функцію з `.lower()`
        result = await get_contact_email(email.lower(), self.session, self.user)

        # Перевіряємо, що результат містить тільки контакт із потрібним email
        expected_contact = next(
            (c for c in contacts if c.email.lower() == email.lower()), None
        )

        self.assertEqual(result, expected_contact)


    async def test_get_contact_email_none(self):
        mocked_contacts = MagicMock()
        mocked_contacts.scalar_one_or_none.return_value = None
        self.session.execute.return_value = mocked_contacts
        result = await get_contact_email("test@gmail.com", self.session, self.user)
        self.assertIsNone(result)

    async def test_get_contact_birthday(self):
        # Поточна дата
        today = datetime.datetime.today()
        seven_days_later = today + datetime.timedelta(days=7)

        # Створюємо тестові контакти
        contacts = [
            Contact(
                id=1,
                first_name="Alice",
                last_name="Smith",
                email="test1@gmail.com",
                phone_number="17777777777",
                birthday=(today + datetime.timedelta(days=3)).date(),
                user=self.user,
            ),
            Contact(
                id=2,
                first_name="Bob",
                last_name="Brown",
                email="test2@gmail.com",
                phone_number="27777777777",
                birthday=(today + datetime.timedelta(days=4)).date(),
                user=self.user,
            ),
            Contact(
                id=3,
                first_name="Charlie",
                last_name="Davis",
                email="test3@gmail.com",
                phone_number="37777777777",
                birthday=(today + datetime.timedelta(days=10)).date(),
                user=self.user,
            ),
        ]

        # Мокуємо базу даних
        mocked_contact = MagicMock()
        mocked_contact.scalars.return_value.all.return_value = [
            c for c in contacts if today.date() <= c.birthday <= seven_days_later.date()
        ]

        self.session.execute.return_value = mocked_contact

        # Викликаємо функцію
        result = await get_contact_birthday(self.session, self.user)

        # Перевіряємо, що повертаються тільки контакти в межах 7 днів
        expected_contacts = [contacts[0], contacts[1]]  # Очікувані контакти
        self.assertListEqual(result, expected_contacts)

    async def test_create_contact(self):
        body = ContactSchema(
            first_name="first_name",
            last_name="last_name",
            email="test@gmail.com",
            phone_number="7777777777",
            birthday=datetime.date(2000, 1, 1),
        )

        self.session.add = MagicMock()
        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()

        result = await create_contact(body, self.session, self.user)

        self.session.add.assert_called_once()
        self.session.commit.assert_awaited_once()
        self.session.refresh.assert_awaited_once_with(result)

        self.assertIsInstance(result, Contact)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone_number, body.phone_number)
        self.assertEqual(result.birthday, body.birthday)

    async def test_update_contact(self):
        contact = Contact(id=1, first_name="John", last_name="Doe", email="john@example.com", phone_number="1234567890",
                          birthday=datetime.date(1990, 5, 15), user=self.user)
        body = ContactSchema(
            first_name="first_name",
            last_name="last_name",
            email="test@gmail.com",
            phone_number="7777777777",
            birthday=datetime.date(2000, 1, 1),
        )
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = contact
        self.session.execute.return_value = mocked_contact
        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()

        result = await update_contact(1, body, self.session, self.user)

        self.session.commit.assert_awaited_once()
        self.session.refresh.assert_awaited_once_with(result)

        self.assertIsInstance(result, Contact)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone_number, body.phone_number)
        self.assertEqual(result.birthday, body.birthday)
        self.assertNotEqual(result.first_name, "old_name")

    async def test_update_contact_none(self):
        body = ContactSchema(
            first_name="first_name",
            last_name="last_name",
            email="test@gmail.com",
            phone_number="7777777777",
            birthday=datetime.date(2000, 1, 1),
        )
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = None
        self.session.execute.return_value = mocked_contact
        result = await update_contact(1, body, self.session, self.user)
        self.assertIsNone(result)

    async def test_remove_contact(self):
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = Contact(
            id=1,
            first_name="first_name",
            last_name="last_name",
            email="test@gmail.com",
            phone_number="7777777777",
            birthday=datetime.date(2001, 1, 1),
            user=self.user,
        )
        self.session.execute.return_value = mocked_contact
        self.session.delete = AsyncMock()
        self.session.commit = AsyncMock()

        result = await remove_contact(1, self.session, self.user)

        self.session.delete.assert_awaited_once()
        self.session.commit.assert_awaited_once()

        self.assertIsInstance(result, Contact)

    async def test_remove_contact_none(self):
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = None
        self.session.execute.return_value = mocked_contact

        result = await remove_contact(1, self.session, self.user)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
