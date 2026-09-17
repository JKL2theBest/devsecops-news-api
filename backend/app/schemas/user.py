import datetime
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr

from .role import UserRole


class UserBase(BaseModel):
    name: str
    email: EmailStr
    avatar_url: str | None = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: str | None = None
    avatar_url: str | None = None


class UserResponse(UserBase):
    id: uuid.UUID
    registered_at: datetime.datetime
    role: UserRole

    model_config = ConfigDict(
        from_attributes=True
    )  # Позволяет Pydantic читать данные и из атрибутов объекта (из ORM-модели SQLAlchemy)
