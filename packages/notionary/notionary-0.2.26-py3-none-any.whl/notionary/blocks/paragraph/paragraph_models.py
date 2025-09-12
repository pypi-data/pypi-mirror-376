from typing import Literal

from pydantic import BaseModel

from notionary.blocks.rich_text.rich_text_models import RichTextObject
from notionary.blocks.types import BlockColor


class ParagraphBlock(BaseModel):
    rich_text: list[RichTextObject]
    color: BlockColor = BlockColor.DEFAULT.value


class CreateParagraphBlock(BaseModel):
    type: Literal["paragraph"] = "paragraph"
    paragraph: ParagraphBlock
