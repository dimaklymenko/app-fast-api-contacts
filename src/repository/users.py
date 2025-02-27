from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.database.db import get_db
from src.entity.models import User
from src.schemas.user import UserSchema



async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieves a user by their email address.

    :param email:   email (str): The email address of the user.
    :param db:  db (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_db).
    :return:    User: The user object if found, otherwise None.
    """
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    return user


async def create_user(body: UserSchema, db: AsyncSession = Depends(get_db)):
    """
    Creates a new user with an optional Gravatar avatar.
    Details:
    The function attempts to fetch a Gravatar image for the user's email. If successful, it sets the avatar field;
    otherwise, it logs the error and proceeds without an avatar.

    :param body:    body (UserSchema): The user data to create.
    :param db:  db (AsyncSession, optional): The asynchronous database session. Defaults to Depends(get_db).
    :return:    User: The newly created user.
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as err:
        print(err)

    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: AsyncSession):
    """
    Updates the refresh token for a user.

    :param user:    user (User): The user object to update.
    :param token:   token (str | None): The new refresh token (or None to clear the token).
    :param db:  db (AsyncSession): The asynchronous database session.
    :return:    None
    """
    user.refresh_token = token
    await db.commit()

async def confirmed_email(email: str, db: AsyncSession) -> None:
    """
    Marks a user's email as confirmed.

    :param email:   email (str): The email address of the user.
    :param db:  db (AsyncSession): The asynchronous database session.
    :return:    None
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()


async def update_avatar_url(email: str, url: str | None, db: AsyncSession) -> User:
    """
    Updates the avatar URL for a user.

    :param email:   email (str): The email address of the user.
    :param url:     url (str | None): The new avatar URL (or None to clear the URL).
    :param db:      db (AsyncSession): The asynchronous database session.
    :return:    User: The updated user object.
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user
