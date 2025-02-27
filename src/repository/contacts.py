from typing import List
from datetime import datetime, timedelta

from fastapi import HTTPException , status
from sqlalchemy import select, and_, extract, or_
from sqlalchemy import  text, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.schemas.contact import ContactSchema , ContactUpdateSchema
import logging

logger = logging.getLogger(__name__)


async def get_contacts(offset: int, limit: int, db: AsyncSession, user: User) -> List[Contact]:
    """

    Retrieves a paginated list of contacts for a specific user.

    :param offset: (int): The offset for pagination.
    :param limit:  limit (int): The maximum number of contacts to retrieve.
    :param db:  db (AsyncSession): The asynchronous database session.
    :param user:    user (User): The user for whom the contacts are being retrieved.
    :return:    List[Contact]: A list of contacts.
    """
    stmt = select(Contact).filter_by(user=user).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()



async def get_contact_id(contact_id: int, db: AsyncSession, user: User) -> Contact:
    """
     Retrieves a single contact by its ID for a specific user.

    :param contact_id:  contact_id (int): The ID of the contact.
    :param db:  db (AsyncSession): The asynchronous database session.
    :param user:    user (User): The user for whom the contact is being retrieved.
    :return:    Contact: The contact object if found, otherwise None.
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(stmt)
    return contact.scalar_one_or_none()


async def get_contact_first_name(contact_first_name: str, db: AsyncSession, user: User):
    """
    Retrieves contacts by their first name (case-insensitive) for a specific user.

    :param contact_first_name:  contact_first_name (str): The first name of the contact.
    :param db:  db (AsyncSession): The asynchronous database session.
    :param user:    user (User): The user for whom the contacts are being retrieved.
    :return:    List[Contact]: A list of contacts with the specified first name.
    """
    stmt = select(Contact).filter(func.lower(Contact.first_name) == contact_first_name.lower(),Contact.user_id == user.id)
    result = await db.execute(stmt)
    return result.scalars().all()  # Повертає один результат або None


async def get_contact_last_name(contact_last_name: str, db: AsyncSession, user: User):
    """
    Retrieves contacts by their last name (case-insensitive) for a specific user.

    :param contact_last_name:   contact_last_name (str): The last name of the contact.
    :param db:  db (AsyncSession): The asynchronous database session.
    :param user:    user (User): The user for whom the contacts are being retrieved.
    :return:    List[Contact]: A list of contacts with the specified last name.
    """
    stmt = select(Contact).filter(func.lower(Contact.last_name) == contact_last_name.lower(), Contact.user_id == user.id)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_contact_email(contact_email: str, db: AsyncSession, user: User) -> Contact:
    """
    Retrieves a contact by their email (case-insensitive) for a specific user.

    :param contact_email:   contact_email (str): The email of the contact.
    :param db:  db (AsyncSession): The asynchronous database session.
    :param user:    user (User): The user for whom the contact is being retrieved.
    :return:    Contact: The contact object if found, otherwise None.
    """
    stmt = select(Contact).filter(func.lower(Contact.email) == contact_email.lower(), Contact.user_id == user.id)
    contact = await db.execute(stmt)
    contact = contact.scalar_one_or_none()

    logger.info(f"Searching for email: {contact_email}, found: {contact}")

    if contact is None:
        logger.warning(f"Contact with email {contact_email} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    return contact


async def get_contact_birthday(db: AsyncSession, user: User):
    """
    Retrieves contacts whose birthdays fall within the next 7 days for a specific user.

    :param db:  db (AsyncSession): The asynchronous database session.
    :param user:    user (User): The user for whom the contacts are being retrieved.
    :return:    List[Contact]: A list of contacts with birthdays in the next 7 days.
    """
    today = datetime.utcnow().date()
    seven_days_later = today + timedelta(days=7)

    stmt = select(Contact).where(
        and_(
            Contact.user_id == user.id,
            or_(
                and_(
                    func.date_part('month', Contact.birthday) == today.month,
                    func.date_part('day', Contact.birthday) >= today.day
                ),
                and_(
                    func.date_part('month', Contact.birthday) == seven_days_later.month,
                    func.date_part('day', Contact.birthday) <= seven_days_later.day
                )
            )
        )
    )

    result = await db.execute(stmt)
    return result.scalars().all()




async def create_contact(body: ContactSchema, db: AsyncSession, user: User) -> Contact:
    """
    Creates a new contact for a specific user.

    :param body:    body (ContactSchema): The contact data to create.
    :param db:  db (AsyncSession): The asynchronous database session.
    :param user:    user (User): The user for whom the contact is being created.
    :return:    Contact: The newly created contact.
    """
    contact = Contact(**body.model_dump(exclude_unset=True), user=user)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(contact_id: int, body: ContactUpdateSchema, db: AsyncSession, user: User) -> Contact | None:
    """
    Updates an existing contact for a specific user.

    :param contact_id:  contact_id (int): The ID of the contact to update.
    :param body:    body (ContactUpdateSchema): The updated contact data.
    :param db:  db (AsyncSession): The asynchronous database session.
    :param user:    user (User): The user for whom the contact is being updated.
    :return:    Contact | None: The updated contact object if found, otherwise None.
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if contact:
        contact.first_name = body.first_name
        contact.last_name = body.last_name
        contact.email = body.email
        contact.phone_number = body.phone_number
        contact.birthday = body.birthday
        await db.commit()
        await db.refresh(contact)
    return contact


async def remove_contact(contact_id: int, db: AsyncSession, user: User)  -> Contact | None:
    """
    Deletes a contact for a specific user.

    :param contact_id:  contact_id (int): The ID of the contact to delete.
    :param db:  db (AsyncSession): The asynchronous database session.
    :param user:    user (User): The user for whom the contact is being deleted.
    :return:    Contact | None: The deleted contact object if found, otherwise None.
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(stmt)
    contact = contact.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact
