from pydantic import BaseModel
from typing import Optional, Tuple
from .components import COMPONENTS, Img


class Field(BaseModel):
    label: str
    component: COMPONENTS
    form_key: Optional[str] = None
    required: Optional[bool] = True
