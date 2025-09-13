from typing import Protocol, Any, List
from ..page import PageOptions
from ..components import COMPONENTS
from ..build_results import BuildResultBase


class Engine(Protocol):

    def new_page(self, options: PageOptions) -> Any:
        ...

    def make_component(self, page: Any, component: COMPONENTS):
        ...

    def get_instance(self, ctx_page: Any) -> Any:
        """
        Retorna a "instância" que representa a página após renderizar.
        Para Pillow: PIL.Image
        Para PDF engine: algum ctx/page ou bytes dependendo da implementação.
        """
        ...

    def build_result(self, instances: List[Any]) -> BuildResultBase:
        """
        Recebe o resultado do get_instance(...) para todas páginas e retorna
        um BuildResultBase específico do engine (ImageBuildResult ou PDFBuildResult).
        """
        ...