from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from src.schemas.user import UserResponse




class ContactSchema(BaseModel):
    first_name : str = Field(max_length=50)
    last_name : str = Field(max_length=50)
    email : EmailStr
    phone_number : str = Field(max_length=50)
    birthday : date

class ContactUpdateSchema(ContactSchema):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: date

class ContactResponse(BaseModel):
    id: int = 1
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: date
    created_at: datetime | None
    updated_at: datetime | None
    user: UserResponse | None

    class Config:
        from_attributes = True









