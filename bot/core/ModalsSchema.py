from pydantic import BaseModel
from typing import Optional


class ModalFieldsSchema(BaseModel):
    label: str
    placeholder : Optional[str] = None
    required: bool = True
    min_length: int = 1
    max_length: int = 300
    style: int = 1
    default: Optional[str] = None
    custom_id: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True