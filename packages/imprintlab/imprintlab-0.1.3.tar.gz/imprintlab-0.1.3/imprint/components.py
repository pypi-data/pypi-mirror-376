from pydantic import BaseModel, field_validator
from typing import Any, Tuple, Optional, Union, Dict, Callable


class Img(BaseModel):
    _position: Optional[Tuple[int, int]] = (0, 0)
    _dimension: Optional[Tuple[int, int]] = (100, 100)
    _path: Optional[Optional[str]] = None

    def get_position(self) -> Tuple[int, int]:
        return self._position

    def set_position(self, value: Tuple[int, int]):
        if not isinstance(value, tuple) or len(value) != 2:
            raise ValueError("position deve ser uma tupla (x, y)")
        if not all(isinstance(v, int) for v in value):
            raise ValueError("position deve conter apenas inteiros")
        self._position = value
        return self  # permite encadeamento (fluent API)

    def get_dimension(self) -> Tuple[int, int]:
        return self._dimension

    def set_dimension(self, value: Tuple[int, int]):
        if not isinstance(value, tuple) or len(value) != 2:
            raise ValueError("dimension deve ser uma tupla (largura, altura)")
        if not all(isinstance(v, int) and v >= 0 for v in value):
            raise ValueError("dimension deve conter apenas inteiros >= 0")
        self._dimension = value
        return self

    def get_path(self) -> Optional[str]:
        return self._path

    def set_path(self, value: Optional[str]):
        self._path = value
        return self

    def set_value(self, value: Optional[str]):
        self._path = value
        return self

class Text(BaseModel):
    _color: Optional[Tuple[int, int, int]] = (0, 0, 0)
    _size: Optional[int] = 12
    _position: Optional[Tuple[int, int]] = (0, 0)
    _value: Optional[str] = ""
    _dimension_r: Optional[int] = 0
    _font: Optional[Union[str, None]] = None

    def get_color(self) -> Tuple[int, int, int]:
        return self._color

    def set_color(self, value: Tuple[int, int, int]):
        if not isinstance(value, tuple) or len(value) != 3:
            raise ValueError("color deve ser uma tupla (R, G, B)")
        if any(not (0 <= c <= 255) for c in value):
            raise ValueError("Cada componente da cor deve estar entre 0 e 255")
        self._color = value
        return self

    def get_size(self) -> int:
        return self._size

    def set_size(self, value: int):
        if not isinstance(value, int) or value <= 0:
            raise ValueError("size deve ser um inteiro positivo")
        self._size = value
        return self

    def get_position(self) -> Tuple[int, int]:
        return self._position

    def set_position(self, value: Tuple[int, int]):
        if not isinstance(value, tuple) or len(value) != 2:
            raise ValueError("position deve ser uma tupla (x, y)")
        if not all(isinstance(v, int) for v in value):
            raise ValueError("position deve conter apenas inteiros")
        self._position = value
        return self

    def get_value(self) -> Optional[str]:
        return self._value

    def set_value(self, text: Optional[str]):
        if text is not None and not isinstance(text, str):
            raise ValueError("value deve ser uma string ou None")
        self._value = text
        return self

    def get_dimension_r(self) -> int:
        return self._dimension_r

    def set_dimension_r(self, value: int):
        if not isinstance(value, int) or value < 0:
            raise ValueError("dimension_r deve ser um inteiro >= 0")
        self._dimension_r = value
        return self

    def get_font(self):
        return self._font
    
    def set_font(self, path: str):
        self._font = path
        return self

COMPONENTS = Union[Text, Img]

# mapeamento de fábricas
MAPPING_COMPONENTS: Dict[str, Callable[[], COMPONENTS]] = {
    "text": lambda: Text(),
    "img": lambda: Img(),
}

def get_component(name: str) -> COMPONENTS:
    factory = MAPPING_COMPONENTS.get(name)
    if not factory:
        raise ValueError(f"Componente '{name}' não encontrado")
    return factory()
