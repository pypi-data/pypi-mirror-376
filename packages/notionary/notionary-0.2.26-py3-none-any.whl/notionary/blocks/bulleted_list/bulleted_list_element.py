from __future__ import annotations

import re
from typing import Optional

from notionary.blocks.base_block_element import BaseBlockElement
from notionary.blocks.bulleted_list.bulleted_list_models import (
    BulletedListItemBlock,
    CreateBulletedListItemBlock,
)
from notionary.blocks.syntax_prompt_builder import BlockElementMarkdownInformation
from notionary.blocks.models import Block, BlockCreateResult, BlockType
from notionary.blocks.rich_text.text_inline_formatter import TextInlineFormatter


class BulletedListElement(BaseBlockElement):
    """Class for converting between Markdown bullet lists and Notion bulleted list items."""

    # Regex for markdown bullets (excluding todo items [ ] or [x])
    PATTERN = re.compile(r"^(\s*)[*\-+]\s+(?!\[[ x]\])(.+)$")

    @classmethod
    def match_notion(cls, block: Block) -> bool:
        """Check if this element can handle the given Notion block."""
        return block.type == BlockType.BULLETED_LIST_ITEM and block.bulleted_list_item

    @classmethod
    async def markdown_to_notion(cls, text: str) -> BlockCreateResult:
        """
        Convert a markdown bulleted list item into a Notion BulletedListItemBlock.
        """
        if not (match := cls.PATTERN.match(text.strip())):
            return None

        # Extract the content part (second capture group)
        content = match.group(2)

        # Parse inline markdown formatting into RichTextObject list
        rich_text = await TextInlineFormatter.parse_inline_formatting(content)

        # Return a properly typed Notion block
        bulleted_list_content = BulletedListItemBlock(
            rich_text=rich_text, color="default"
        )
        return CreateBulletedListItemBlock(bulleted_list_item=bulleted_list_content)

    @classmethod
    async def notion_to_markdown(cls, block: Block) -> Optional[str]:
        """Convert Notion bulleted_list_item block to Markdown."""
        if block.type != BlockType.BULLETED_LIST_ITEM or not block.bulleted_list_item:
            return None

        rich_list = block.bulleted_list_item.rich_text
        if not rich_list:
            return "-"

        text = await TextInlineFormatter.extract_text_with_formatting(rich_list)
        return f"- {text}"

    @classmethod
    def get_system_prompt_information(cls) -> Optional[BlockElementMarkdownInformation]:
        """Get system prompt information for bulleted list blocks."""
        return BlockElementMarkdownInformation(
            block_type=cls.__name__,
            description="Bulleted list items create unordered lists with bullet points",
            syntax_examples=[
                "- First item",
                "* Second item",
                "+ Third item",
                "- Item with **bold text**",
                "- Item with *italic text*",
            ],
            usage_guidelines="Use -, *, or + to create bullet points. Supports inline formatting like bold, italic, and links. Do not use for todo items (use [ ] or [x] for those).",
        )
