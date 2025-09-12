from pydantic import BaseModel
from typing import Dict, Union, Tuple, Optional, List
from .field import Field
from .components import get_component, COMPONENTS

class PageOptions(BaseModel):
    name: str
    width: int
    height: int
    background: Union[str, bytes, None] = None
    background_color: Optional[Tuple] = (0, 0, 0, 0)


class Page(BaseModel):
    options: PageOptions
    _fields: Optional[Dict[str, Field]] = {}

    def add_component(self, name: str, component: str, form_key: Optional[str]=None):
        if name in self._fields:
            raise Exception()
        field = Field(label=name, component=get_component(component), form_key=form_key)
        self._fields[name] = field
        return field.component

    def get_component(self, name: str) -> COMPONENTS:
        if not name in self._fields:
            raise Exception()
        return self._fields[name].component
    
    def set_width(self, width: int):
        self.options.width = width
        return self
    
    def set_height(self, height: int):
        self.options.height = height
        return self

    def set_dimension(self, width: int, height: int):
        self.set_width(width)
        self.set_height(height)
        return self

    def set_background(self, background: Union[str, Tuple[int, int, int]]):
        if isinstance(background, str):
            self.options.background = background
        elif isinstance(background, Tuple):
            self.options.background_color = background
        return self