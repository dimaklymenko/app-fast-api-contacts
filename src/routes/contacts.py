from typing import List
import logging

from fastapi import APIRouter, HTTPException, Depends, status, Path, Query , Response
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession


from src.database.db import get_db
from src.entity.models import User, Role
from src.schemas.contact import ContactSchema, ContactUpdateSchema, ContactResponse
from src.repository import contacts as repository_contacts
from src.services.auth import auth_service
from src.services.roles import RoleAccess

router = APIRouter(prefix='/contacts', tags=["contacts"])
router_one = APIRouter(prefix='/contacts', tags=["search_by"])

access_to_route_all = RoleAccess([Role.admin, Role.moderator])

logger = logging.getLogger(__name__)




@router.get("/", response_model=List[ContactResponse],dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def read_all_contacts(limit: int = Query(10, ge=10, le=500), offset: int = Query(0, ge=0),
                    db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
        The read_all_contacts function retrieves a paginated list of contacts for the current user.
            It takes in limit and offset parameters for pagination and returns a list of contacts.
            The endpoint is rate-limited to 1 request per 20 seconds.

        :param limit: int: Limit the number of contacts returned (default 10, min 10, max 500)
        :param offset: int: Offset for pagination (default 0, min 0)
        :param db: AsyncSession: Get the database session
        :param user: User: Get the current authenticated user
        :return: A list of contacts
    """
    logger.info(f"Fetching all contacts for user: {user.email}")
    contacts = await repository_contacts.get_contacts(offset, limit, db, user)
    return contacts

@router.get("/birthdays", response_model=List[ContactResponse],dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def read_birthday(db: AsyncSession = Depends(get_db),user: User = Depends(auth_service.get_current_user)):
    """
        The read_birthday function retrieves contacts with birthdays within the next 7 days for the current user.
            It returns a list of contacts whose birthdays are upcoming.
            The endpoint is rate-limited to 1 request per 20 seconds.

        :param db: AsyncSession: Get the database session
        :param user: User: Get the current authenticated user
        :return: A list of contacts with upcoming birthdays
    """
    logger.info(f"Fetching upcoming birthdays for user: {user.email}")
    contacts = await repository_contacts.get_contact_birthday(db, user)
    return contacts

@router.get("/{contact_id}", response_model=ContactResponse,dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def read_by_contact_id(contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db),user: User = Depends(auth_service.get_current_user)):
    """
        The read_by_contact_id function retrieves a single contact by its ID for the current user.
            It takes in a contact ID and returns the corresponding contact.
            If the contact is not found, it raises an HTTPException with status code 404 (Not Found).
            The endpoint is rate-limited to 1 request per 20 seconds.

        :param contact_id: int: The ID of the contact to retrieve (min 1)
        :param db: AsyncSession: Get the database session
        :param user: User: Get the current authenticated user
        :return: The contact object
    """

    logger.info(f"Fetching contact with ID {contact_id} for user: {user.email}")
    contact = await repository_contacts.get_contact_id(contact_id, db, user)
    if not contact:
        logger.warning(f"Contact with ID {contact_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact

@router_one.get("/first_name/", response_model=list[ContactResponse],dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def read_contact_first_name(contact_first_name: str , db: AsyncSession = Depends(get_db),user: User = Depends(auth_service.get_current_user)):
    """
      The read_contact_first_name function retrieves contacts by their first name for the current user.
          It takes in a first name and returns a list of contacts with matching first names.
          If no contacts are found, it raises an HTTPException with status code 404 (Not Found).
          The endpoint is rate-limited to 1 request per 20 seconds.

      :param contact_first_name: str: The first name to search for
      :param db: AsyncSession: Get the database session
      :param user: User: Get the current authenticated user
      :return: A list of contacts with matching first names
    """
    logger.info(f"Отримано запит на пошук контакту за ім'ям: {contact_first_name}")
    contacts = await repository_contacts.get_contact_first_name(contact_first_name, db, user)
    if not contacts:
        logger.warning(f"Контакт із ім'ям {contact_first_name} не знайдено")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    logger.info(f"Знайдено {len(contacts)} контакт(и)")
    return contacts

@router_one.get("/last_name/", response_model=list[ContactResponse],dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def read_contact_last_name(contact_last_name: str, db: AsyncSession = Depends(get_db),user: User = Depends(auth_service.get_current_user)):
    """
       The read_contact_last_name function retrieves contacts by their last name for the current user.
           It takes in a last name and returns a list of contacts with matching last names.
           If no contacts are found, it raises an HTTPException with status code 404 (Not Found).
           The endpoint is rate-limited to 1 request per 20 seconds.

       :param contact_last_name: str: The last name to search for
       :param db: AsyncSession: Get the database session
       :param user: User: Get the current authenticated user
       :return: A list of contacts with matching last names
       :doc-author: Trelent
    """
    logger.info(f"Отримано запит на пошук контакту за прізвищем: {contact_last_name}")
    contacts = await repository_contacts.get_contact_last_name(contact_last_name, db, user)
    if not contacts:
        logger.warning(f"Контакт із прізвищем {contact_last_name} не знайдено")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    logger.info(f"Знайдено {len(contacts)} контакт(и)")
    return contacts
@router_one.get("/email/", response_model=ContactResponse,dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def read_contact_email(contact_email: str , db: AsyncSession = Depends(get_db),user: User = Depends(auth_service.get_current_user)):
    """
        The read_contact_email function retrieves a contact by their email for the current user.
            It takes in an email and returns the corresponding contact.
            If the contact is not found, it raises an HTTPException with status code 404 (Not Found).
            The endpoint is rate-limited to 1 request per 20 seconds.

        :param contact_email: str: The email to search for
        :param db: AsyncSession: Get the database session
        :param user: User: Get the current authenticated user
        :return: The contact object
        """
    logger.info(f"Отримано запит на пошук контакту за email: {contact_email}")
    contact = await repository_contacts.get_contact_email(contact_email, db, user)
    if not contact:
        logger.warning(f"Контакт із email {contact_email} не знайдено")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    logger.info(f"Знайдено контакт: {contact.email}")
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED,dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def create_contact(body: ContactSchema, db: AsyncSession = Depends(get_db),user: User = Depends(auth_service.get_current_user)):
    """
        The create_contact function creates a new contact for the current user.
            It takes in contact details and returns the newly created contact.
            The endpoint is rate-limited to 1 request per 20 seconds.

        :param body: ContactSchema: Validate the request body (contact details)
        :param db: AsyncSession: Get the database session
        :param user: User: Get the current authenticated user
        :return: The newly created contact
        """
    logger.info(f"Creating new contact for user: {user.email}")
    contact = await repository_contacts.create_contact(body, db, user)
    logger.info(f"Contact created successfully: {contact.id}")
    return contact

@router.put("/{contact_id}", response_model=ContactResponse,dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def update_contact(body: ContactUpdateSchema, contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db),user: User = Depends(auth_service.get_current_user)):
    """
        The update_contact function updates an existing contact for the current user.
            It takes in the contact ID and updated details, and returns the updated contact.
            If the contact is not found, it raises an HTTPException with status code 404 (Not Found).
            The endpoint is rate-limited to 1 request per 20 seconds.

        :param body: ContactUpdateSchema: Validate the request body (updated contact details)
        :param contact_id: int: The ID of the contact to update (min 1)
        :param db: AsyncSession: Get the database session
        :param user: User: Get the current authenticated user
        :return: The updated contact
        """
    logger.info(f"Updating contact {contact_id} for user: {user.email}")
    contact = await repository_contacts.update_contact(contact_id, body, db, user)
    if not contact:
        logger.warning(f"Contact with ID {contact_id} not found for update")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT,dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def remove_contact(contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db),user: User = Depends(auth_service.get_current_user)):
    """
        The remove_contact function deletes a contact for the current user.
            It takes in the contact ID and deletes the corresponding contact.
            The endpoint is rate-limited to 1 request per 20 seconds.

        :param contact_id: int: The ID of the contact to delete (min 1)
        :param db: AsyncSession: Get the database session
        :param user: User: Get the current authenticated user
        :return: None
    """
    logger.info(f"Deleting contact {contact_id} for user: {user.email}")
    contact = await repository_contacts.remove_contact(contact_id, db, user)
    if not contact:
        logger.warning(f"Contact with ID {contact_id} not found for deletion")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
