from __future__ import annotations

import re
from typing import Optional

from notionary.blocks.base_block_element import BaseBlockElement
from notionary.blocks.syntax_prompt_builder import BlockElementMarkdownInformation
from notionary.blocks.models import Block, BlockCreateResult
from notionary.blocks.rich_text.rich_text_models import RichTextObject
from notionary.blocks.rich_text.text_inline_formatter import TextInlineFormatter
from notionary.blocks.table.table_models import (
    CreateTableBlock,
    TableBlock,
    CreateTableRowBlock,
    TableRowBlock,
)
from notionary.blocks.types import BlockType


class TableElement(BaseBlockElement):
    """
    Handles conversion between Markdown tables and Notion table blocks.
    Now integrated into the LineProcessor stack system.

    Markdown table syntax:
    | Header 1 | Header 2 | Header 3 |
    | -------- | -------- | -------- |
    | Cell 1   | Cell 2   | Cell 3   |
    """

    ROW_PATTERN = re.compile(r"^\s*\|(.+)\|\s*$")
    SEPARATOR_PATTERN = re.compile(r"^\s*\|([\s\-:|]+)\|\s*$")

    @classmethod
    def match_notion(cls, block: Block) -> bool:
        """Check if block is a Notion table."""
        return block.type == BlockType.TABLE and block.table

    @classmethod
    async def markdown_to_notion(cls, text: str) -> BlockCreateResult:
        """Convert opening table row to Notion table block."""
        if not cls.ROW_PATTERN.match(text.strip()):
            return None

        # Parse the header row to determine column count
        header_cells = cls._parse_table_row(text)
        col_count = len(header_cells)

        table_block = TableBlock(
            table_width=col_count,
            has_column_header=True,
            has_row_header=False,
            children=[],  # Will be populated by stack processor
        )

        return CreateTableBlock(table=table_block)

    @classmethod
    async def create_from_markdown_table(
        cls, table_lines: list[str]
    ) -> BlockCreateResult:
        """
        Create a complete table block from markdown table lines.
        """
        if not table_lines:
            return None

        first_row = None
        for line in table_lines:
            line = line.strip()
            if line and cls.ROW_PATTERN.match(line):
                first_row = line
                break

        if not first_row:
            return None

        # Parse header row to determine column count
        header_cells = cls._parse_table_row(first_row)
        col_count = len(header_cells)

        # Process all table lines
        table_rows, separator_found = await cls._process_table_lines(table_lines)

        # Create complete TableBlock
        table_block = TableBlock(
            table_width=col_count,
            has_column_header=separator_found,
            has_row_header=False,
            children=table_rows,
        )

        return CreateTableBlock(table=table_block)

    @classmethod
    async def _process_table_lines(
        cls, table_lines: list[str]
    ) -> tuple[list[CreateTableRowBlock], bool]:
        """Process all table lines and return rows and separator status."""
        table_rows = []
        separator_found = False

        for line in table_lines:
            line = line.strip()
            if not line:
                continue

            if cls._is_separator_line(line):
                separator_found = True
                continue

            if cls.ROW_PATTERN.match(line):
                table_row = await cls._create_table_row_from_line(line)
                table_rows.append(table_row)

        return table_rows, separator_found

    @classmethod
    def _is_separator_line(cls, line: str) -> bool:
        """Check if line is a table separator (|---|---|)."""
        return cls.SEPARATOR_PATTERN.match(line) is not None

    @classmethod
    async def _create_table_row_from_line(cls, line: str) -> CreateTableRowBlock:
        """Create a table row block from a markdown line."""
        cells = cls._parse_table_row(line)
        rich_text_cells = []
        for cell in cells:
            rich_text_cell = await cls._convert_cell_to_rich_text(cell)
            rich_text_cells.append(rich_text_cell)
        table_row = TableRowBlock(cells=rich_text_cells)
        return CreateTableRowBlock(table_row=table_row)

    @classmethod
    async def _convert_cell_to_rich_text(cls, cell: str) -> list[RichTextObject]:
        """Convert cell text to rich text objects."""
        rich_text = await TextInlineFormatter.parse_inline_formatting(cell)
        if not rich_text:
            rich_text = [RichTextObject.from_plain_text(cell)]
        return rich_text

    @classmethod
    async def notion_to_markdown(cls, block: Block) -> Optional[str]:
        """Convert Notion table block to markdown table."""
        if block.type != BlockType.TABLE:
            return None

        if not block.table:
            return None

        table_data = block.table
        children = block.children or []

        if not children:
            table_width = table_data.table_width or 3
            header = (
                "| " + " | ".join([f"Column {i+1}" for i in range(table_width)]) + " |"
            )
            separator = (
                "| " + " | ".join(["--------" for _ in range(table_width)]) + " |"
            )
            data_row = (
                "| " + " | ".join(["        " for _ in range(table_width)]) + " |"
            )
            table_rows = [header, separator, data_row]
            return "\n".join(table_rows)

        table_rows = []
        header_processed = False

        for child in children:
            if child.type != BlockType.TABLE_ROW:
                continue

            if not child.table_row:
                continue

            row_data = child.table_row
            cells = row_data.cells or []

            row_cells = []
            for cell in cells:
                cell_text = await TextInlineFormatter.extract_text_with_formatting(cell)
                row_cells.append(cell_text or "")

            row = "| " + " | ".join(row_cells) + " |"
            table_rows.append(row)

            if not header_processed and table_data.has_column_header:
                header_processed = True
                separator = (
                    "| " + " | ".join(["--------" for _ in range(len(cells))]) + " |"
                )
                table_rows.append(separator)

        return "\n".join(table_rows)

    @classmethod
    def _parse_table_row(cls, row_text: str) -> list[str]:
        """Convert table row text to cell contents."""
        row_content = row_text.strip()

        if row_content.startswith("|"):
            row_content = row_content[1:]
        if row_content.endswith("|"):
            row_content = row_content[:-1]

        return [cell.strip() for cell in row_content.split("|")]

    @classmethod
    def is_table_row(cls, line: str) -> bool:
        """Check if a line is a valid table row."""
        return bool(cls.ROW_PATTERN.match(line.strip()))

    @classmethod
    def get_system_prompt_information(cls) -> Optional[BlockElementMarkdownInformation]:
        """Get system prompt information for table blocks."""
        return BlockElementMarkdownInformation(
            block_type=cls.__name__,
            description="Table blocks create structured data in rows and columns with headers",
            syntax_examples=[
                "| Name | Age | City |\n| -------- | -------- | -------- |\n| Alice | 25 | Berlin |\n| Bob | 30 | Munich |"
            ],
            usage_guidelines="Use for structured data presentation. First row is header, second row is separator with dashes, following rows are data. Cells are separated by | characters.",
        )
