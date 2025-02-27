from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from jinja2 import Template
from pydantic import EmailStr

from src.services.auth import auth_service
from src.conf.config import config

conf = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_FROM=config.MAIL_USERNAME,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_FROM_NAME="TODO Systems",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',
)


async def send_email(email: EmailStr, username: str, host: str):
    try:
        token_verification = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email ",
            recipients=[email],
            template_body={"host": host, "username": username, "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as err:
        print(err)

async def send_email_password(email: EmailStr, username: str):
    try:
        token_verification = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Change Password ",
            recipients=[email],
            template_body={"username": username, "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="forget_password.html")
    except ConnectionErrors as err:
        print(err)

async def send_password_reset_email(email: str,  token: str, ):
    # Завантаження HTML-шаблону
    with open("src/services/templates/reset_password.html", "r") as file:
        template = Template(file.read())

    # Заповнення шаблону даними
    html_content = template.render(token=token, app_name="My Awesome App")

    # Створення листа
    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email],
        body=html_content,
        subtype="html",
    )

    # Надсилання листа
    fm = FastMail(conf)
    await fm.send_message(message)