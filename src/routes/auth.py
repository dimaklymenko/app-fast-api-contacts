from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Request, Response
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf import messages
from src.database.db import get_db
from src.entity.models import User, PasswordResetToken
from src.repository import users as repositories_users
from src.schemas.user import UserSchema, TokenSchema, UserResponse, RequestEmail, PasswordResetRequest, PasswordReset
from src.services.auth import auth_service
from src.services.email import send_email, send_email_password, send_password_reset_email
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/auth', tags=['auth'])
get_refresh_token = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserSchema, bt: BackgroundTasks, request: Request, db: AsyncSession = Depends(get_db)):
    logger.info(f"Отримано запит на реєстрацію: {body.email}")

    exist_user = await repositories_users.get_user_by_email(body.email, db)
    if exist_user:
        logger.warning(f"Користувач з email {body.email} вже існує")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.ACCOUNT_EXIST)

    logger.info("Хешування пароля")
    body.password = auth_service.get_password_hash(body.password)

    logger.info("Створення нового користувача")
    try:
        new_user = await repositories_users.create_user(body, db)
    except Exception as e:
        logger.error(f"Помилка під час створення користувача: {e}")
        raise HTTPException(status_code=500, detail="Помилка створення користувача")

    logger.info(f"Додавання завдання у фон для відправки email: {new_user.email}")
    bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))

    logger.info(f"Користувач {new_user.email} успішно створений")
    return new_user

@router.post("/login",  response_model=TokenSchema, status_code=status.HTTP_201_CREATED)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    The login function authenticates a user and returns access and refresh tokens.
        It takes in an OAuth2PasswordRequestForm object, which contains the username (email) and password.
        If the email is not found, the email is not confirmed, or the password is invalid, it raises an HTTPException with status code 401 (Unauthorized).
        Otherwise, it generates JWT tokens and updates the user's refresh token in the database.

    :param body: OAuth2PasswordRequestForm: Validate the request body (username and password)
    :param db: AsyncSession: Get the database session
    :return: A dictionary containing access_token, refresh_token, and token_type
    """
    user = await repositories_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_EMAIL)
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.EMAIL_NOT_CONFIRMED)
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_PASSWORD)
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repositories_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/refresh_token',  response_model=TokenSchema)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(get_refresh_token),
                        db: AsyncSession = Depends(get_db)):
    """
    The refresh_token function generates a new access token using a valid refresh token.
        It takes in the refresh token from the authorization header.
        If the refresh token is invalid or does not match the user's stored refresh token, it raises an HTTPException with status code 401 (Unauthorized).
        Otherwise, it generates new access and refresh tokens and updates the user's refresh token in the database.

    :param credentials: HTTPAuthorizationCredentials: Extract the refresh token from the request headers
    :param db: AsyncSession: Get the database session
    :return: A dictionary containing access_token, refresh_token, and token_type
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repositories_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_REFRESH_TOKEN)

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repositories_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    The confirmed_email function confirms a user's email using a token sent to their email.
        It takes in a token as a path parameter and decodes it to get the user's email.
        If the user does not exist or the email is already confirmed, it raises an HTTPException with status code 400 (Bad Request).
        Otherwise, it marks the user's email as confirmed in the database.

    :param token: str: The confirmation token sent to the user's email
    :param db: AsyncSession: Get the database session
    :return: A message indicating whether the email was confirmed
    """
    email = await auth_service.get_email_from_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.VERIFICATION_ERROR)
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repositories_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: AsyncSession = Depends(get_db)):
    """
    The request_email function sends a confirmation email to the user if their email is not already confirmed.
        It takes in the user's email and checks if the email is already confirmed.
        If the email is not confirmed, it sends a confirmation email in the background.

    :param body: RequestEmail: Validate the request body (email)
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base URL of the application
    :param db: AsyncSession: Get the database session
    :return: A message indicating that the user should check their email for confirmation
    """
    user = await repositories_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, str(request.base_url))
    return {"message": "Check your email for confirmation."}


@router.get('/{username}')
async def request_email(username: str, response: Response, db: AsyncSession = Depends(get_db)):
    """
        The request_email function tracks when a user opens an email by logging the event and returning an image.
            It takes in the username of the user who opened the email and logs the event.
            It returns an image (open_check.png) to be displayed in the email.

        :param username: str: The username of the user who opened the email
        :param response: Response: The response object to return the image
        :param db: AsyncSession: Get the database session
        :return: An image file (open_check.png)
    """
    print('--------------------------------')
    print(f'{username} зберігаємо що він відкрив email в БД')
    print('--------------------------------')
    return FileResponse("src/static/open_check.png", media_type="image/png", content_disposition_type="inline")




@router.post("/password-reset-request")
async def password_reset_request(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
        The password_reset_request function handles the request to reset a user's password.
            It takes in the user's email, generates a reset token, and sends a password reset link to the user's email.
            If the email is not found in the database, it raises an HTTPException with status code 404 (Not Found).
            Otherwise, it generates a token, saves it in the database, and sends an email with the reset link.

        :param request: PasswordResetRequest: Validate the request body (email)
        :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
        :param db: AsyncSession: Get the database session
        :return: A message indicating that the password reset link has been sent
    """
    user = await repositories_users.get_user_by_email(request.email, db)
    if not user:
        raise HTTPException(status_code=404, detail=messages.EMAIL_NOT_FOUND)

    # Генерація токену
    token = auth_service.generate_reset_token()
    expiration = datetime.utcnow() + timedelta(hours=1)

    # Збереження токену в базі даних
    db_token = PasswordResetToken(email=request.email, token=token, expiration=expiration)
    db.add(db_token)
    await db.commit()

    # Надсилання листа з токеном
    background_tasks.add_task(send_password_reset_email, request.email, token)
    return {"message": "Password reset link has been sent to your email."}

# Ендпоінт для скидання паролю
@router.post("/reset-password")
async def reset_password(
    request: PasswordReset,
    db: AsyncSession = Depends(get_db),
):
    """
        The reset_password function handles the actual password reset process.
            It takes in the reset token and the new password, validates the token, and updates the user's password.
            If the token is invalid or expired, it raises an HTTPException with status code 400 (Bad Request).
            If the user is not found, it raises an HTTPException with status code 404 (Not Found).
            Otherwise, it updates the user's password and deletes the used token from the database.

        :param request: PasswordReset: Validate the request body (token and new_password)
        :param db: AsyncSession: Get the database session
        :return: A message indicating that the password has been reset successfully
    """

    # Перевірка токену
    stmt = select(PasswordResetToken).where(PasswordResetToken.token == request.token)
    result = await db.execute(stmt)
    db_token = result.scalar()


    if not db_token or db_token.expiration < datetime.utcnow():
        raise HTTPException(status_code=400, detail=messages.INVALID_OR_EXPIRED_TOKEN)

    # Оновлення паролю
    stmt_1 = select(User).where(User.email == db_token.email)
    result_1 = await db.execute(stmt_1)
    user = result_1.scalar()


    if not user:
        raise HTTPException(status_code=404, detail=messages.USER_NOT_FOUND)

    user.password = auth_service.get_password_hash(request.new_password)
    await db.commit()
    await db.refresh(user)

    # Видалення токену
    await db.delete(db_token)
    await db.commit()


    return {"message": "Password has been reset successfully."}




