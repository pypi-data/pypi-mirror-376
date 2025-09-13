from pydantic import BaseModel
from typing import Dict, Optional, Any,List
from .page import Page, PageOptions
from .engines.pillow import PillowMotor
from .engines.repository import Engine
from .build_results import BuildResultBase


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
        pages = list(self._pages.values())
        for page in pages:
            for field in getattr(page, "_fields", {}).values():
                form[field.form_key] = ""
        return form
    
    def get_schema(self) -> Dict:
        form = {}
        for page_name, page in self._pages.items():
            form[page_name] = {}
            for field in getattr(page, "_fields", {}).values():
                form[page_name][field.form_key] = ""
        return form
    
    def build(self, form: Dict):
        return Builder(self, form)



class Builder:
    def __init__(self, model: Model, form, engine: Optional[Engine] = None):
        self._model = model
        self._form = form
        self._engine = engine or PillowMotor()

    def _build(self) -> List[Any]:
        instances = []
        pages = list(self._model._pages.values())
        if not pages:
            raise RuntimeError("Nenhuma página criada")
        for page in pages:
            ctx = self._engine.new_page(page.options)
            # iterar campos...
            for field in getattr(page, "_fields", {}).values():
                if getattr(field, "form_key", None):
                    field.component.set_value(self._form.get(field.form_key))
                self._engine.make_component(ctx, field.component)
            instances.append(self._engine.get_instance(ctx))
        return instances

    def render(self) -> BuildResultBase:
        instances = self._build()
        # delega ao engine para encapsular no BuildResult adequado
        result = self._engine.build_result(instances)
        return result

    # aliases
    def make_images(self, transparent: bool = False):
        # compat layer: if engine is PillowMotor, user expects image behavior
        return self.render()
