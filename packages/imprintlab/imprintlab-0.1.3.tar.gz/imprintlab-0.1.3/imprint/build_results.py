# build_results.py
from abc import ABC, abstractmethod
from typing import List, Optional
from PIL import Image
import os
import tempfile
import webbrowser

class BuildResultBase(ABC):
    """Interface comum para os resultados do processo de build."""
    @abstractmethod
    def save(self, path: str) -> None:
        """Salvar o resultado num caminho (implementação engine-specific)."""
        raise NotImplementedError

    @abstractmethod
    def to_bytes(self) -> bytes:
        """Retornar bytes binários do output (PDF bytes, PNG bytes, ...)."""
        raise NotImplementedError

    def show(self) -> None:
        """Exibir o resultado. Implementação padrão cria um arquivo temporário e abre."""
        # opcional; engines podem sobrescrever com um método mais apropriado
        data = self.to_bytes()
        # detect fallback: escreve em temp e abre
        suffix = getattr(self, "_default_suffix", ".bin")
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        try:
            tmp.write(data)
            tmp.flush()
            tmp.close()
            webbrowser.open(f"file://{tmp.name}")
        finally:
            pass


class ImageBuildResult(BuildResultBase):
    def __init__(self, pages: List[Image.Image]):
        self.pages = pages
        self._default_suffix = ".png"

    # baixo nível
    def to_images(self) -> List[Image.Image]:
        return self.pages

    def to_image(self) -> Image.Image:
        if len(self.pages) != 1:
            raise ValueError("Use to_images() quando houver múltiplas páginas")
        return self.pages[0]

    # alto nível
    def save(self, path: str) -> None:
        if len(self.pages) == 0:
            raise ValueError("Nenhuma página para salvar.")
        looks_like_dir = path.endswith(os.sep) or os.path.isdir(path)
        if len(self.pages) == 1:
            if looks_like_dir:
                os.makedirs(path, exist_ok=True)
                out_path = os.path.join(path, "page_1.png")
            else:
                parent = os.path.dirname(path)
                if parent:
                    os.makedirs(parent, exist_ok=True)
                out_path = path
            self.pages[0].save(out_path)
            return

        # múltiplas páginas
        if path.lower().endswith(".pdf"):
            pages_rgb = [p.convert("RGB") for p in self.pages]
            parent = os.path.dirname(path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            pages_rgb[0].save(path, save_all=True, append_images=pages_rgb[1:])
        else:
            os.makedirs(path, exist_ok=True)
            for idx, p in enumerate(self.pages, start=1):
                p.save(os.path.join(path, f"page_{idx}.png"))

    def to_bytes(self) -> bytes:
        # retorna bytes da primeira página por padrão (útil p/ APIs)
        from io import BytesIO
        if len(self.pages) == 0:
            return b""
        buf = BytesIO()
        self.pages[0].save(buf, format="PNG")
        return buf.getvalue()


class PDFBuildResult(BuildResultBase):
    def __init__(self, pdf_bytes: bytes):
        self.pdf_bytes = pdf_bytes
        self._default_suffix = ".pdf"

    def save(self, path: str) -> None:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "wb") as f:
            f.write(self.pdf_bytes)

    def to_bytes(self) -> bytes:
        return self.pdf_bytes

    def show(self) -> None:
        # abre um arquivo temporário .pdf usando o viewer do sistema
        import tempfile, webbrowser
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.write(self.pdf_bytes)
        tmp.flush()
        tmp.close()
        webbrowser.open(f"file://{tmp.name}")
