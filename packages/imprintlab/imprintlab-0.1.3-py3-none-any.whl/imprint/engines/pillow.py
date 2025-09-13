
from typing import List, Any
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass
from .repository import Engine
from ..components import Text, Img
from ..build_results import ImageBuildResult

@dataclass
class CtxPillow:
    img: Image.Image
    draw: ImageDraw.ImageDraw
    desc: str

class PillowMotor(Engine):

    def new_page(self, options):
        if not options.background:
            if not options.width or not options.height:
                raise Exception(f"Defina a largura e altura para", options.name)
            # background personalizado (SEM IMAGEM)
            img = Image.new("RGBA",
                (options.width, options.height),
                options.background_color
            )
        else:
            # background com imagem
            img = Image.open(options.background)
            w, h = img.size
            if options.width:
                w = options.width
            if options.height:
                h = options.height
            img = img.resize((w, h))
        return CtxPillow(img, ImageDraw.Draw(img), desc=options.name)

    def make_component(self, page: CtxPillow, component):
        if isinstance(component, Text):
            # definir fonte
            font = component.get_font()
            if font:
                font = ImageFont.truetype(font, size=component.get_size())
            else:
                font = ImageFont.load_default(size=component.get_size())

            value = component.get_value()
            x, y = component.get_position()
            
            if component.get_dimension_r():
                text_size = page.draw.textlength(value, font)
                x = (x + component.get_dimension_r() - text_size) // 2

            page.draw.text(
                (x, y), # Position
                value, # Texto
                fill=component.get_color(), # Color
                font=font # Font
            )
            
        elif isinstance(component, Img):
            path = component.get_path()
            if not path:
                raise Exception("O caminho da imagem não foi denifido!")
            img = Image.open(path)
            img = img.resize(component.get_dimension(), Image.LANCZOS)
            page.img.paste(img, component.get_position())

    def get_instance(self, page: CtxPillow):
        return page.img
    
    def build_result(self, instances: List[Image.Image]):
        return ImageBuildResult(instances)