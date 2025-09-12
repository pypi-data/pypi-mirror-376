from pydantic import BaseModel
from typing import Dict, Optional, Any, Union, List
from .page import Page, PageOptions
from .engines.pillow import PillowMotor
from .engines.repository import Engine
from dataclasses import dataclass, field
from PIL.Image import Image


class Model(BaseModel):
    name: str
    _pages: Optional[Dict[str, Page]] = {}

    @classmethod
    def new(cls, name: str):
        """
        Esta função é responsável por criar uma instancia apenas com o nome
        """
        return cls(name=name)
    
    def new_page(self, name: str) -> Page:
        """
        Esta função é responsável por criar uma nova página apenas com o nome
        e já atribuir a lista de paginas do modelo 'pai'
        """
        page = Page(options=PageOptions(
            name=name,
            width=0,
            height=0,
        ))
        if name in self._pages:
            raise Exception("")
        self._pages[name] = page
        return page

    def get_form(self) -> Dict:
        form = {}
        for page in self._pages:
            for field in page.fields:
                form[field.name] = ""
        return form
    
    def build(self, form: Dict):
        return Builder(self, form)


@dataclass
class Builder:
    _model: Model
    _form: Dict[str, Any]
    _engine: Optional[Engine] = field(default_factory=PillowMotor)

    def _build(self):
        _instances = []
        if len(self._model._pages.keys()) < 1:
            raise Exception("Nenhuma página criada!")
        for _, page in self._model._pages.items():
            # Criar uma nova página
            ctx_page = self._engine.new_page(page.options)
            for _, field in page._fields.items():
                # Obtém o valor do formulário
                if field.form_key:
                    field_value = self._form.get(field.form_key)
                    field.component.set_value(field_value)
                self._engine.make_component(ctx_page, field.component)
            _instances.append(self._engine.get_instance(ctx_page))
        return _instances

    def make_images(self, transparent=False) -> Union[Image, List[Image]]:
        if not isinstance(self._engine, PillowMotor):
            self._engine = PillowMotor()
        pages = self._build()
        if not transparent:
            pages = [page.convert("RGB") for page in pages]
        if len(pages) == 1:
            return pages[0]
        return pages
