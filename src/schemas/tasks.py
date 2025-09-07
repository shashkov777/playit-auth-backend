from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from src.utils.enums import StatusEnum


class TaskCreateSchema(BaseModel):
    user_id: int
    description: int
    status: StatusEnum


class TaskUpdateSchema(BaseModel):
    user_id: Optional[int]
    description: Optional[int]
    status: Optional[StatusEnum]


class TaskSchema(BaseModel):
    id: int
    user_id: int
    description: str
    photo_path: str
    value: int
    status: StatusEnum
