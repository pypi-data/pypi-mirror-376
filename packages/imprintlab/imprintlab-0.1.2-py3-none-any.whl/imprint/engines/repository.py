from typing import Protocol, Any, Optional
from ..page import PageOptions
from ..components import COMPONENTS



class Engine(Protocol):

    def new_page(self, options: PageOptions) -> Any:
        ...

    def make_component(self, page: Any, component: COMPONENTS, value: Optional[str]=None):
        ...

    def get_instance(self, page: Any) -> Any:
        ...