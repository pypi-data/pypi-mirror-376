from __future__ import annotations

import re
from typing import Optional

from notionary.blocks.base_block_element import BaseBlockElement
from notionary.blocks.file.file_element_models import (
    ExternalFile,
    FileBlock,
    FileType,
    FileUploadFile,
)
from notionary.blocks.mixins.captions import CaptionMixin
from notionary.blocks.mixins.file_upload.file_upload_mixin import FileUploadMixin
from notionary.blocks.syntax_prompt_builder import BlockElementMarkdownInformation
from notionary.blocks.models import Block, BlockCreateResult, BlockType
from notionary.blocks.pdf.pdf_models import CreatePdfBlock


class PdfElement(BaseBlockElement, CaptionMixin, FileUploadMixin):
    r"""
    Handles conversion between Markdown PDF embeds and Notion PDF blocks.

    Supports both external URLs and local PDF file uploads.

    Markdown PDF syntax:
    - [pdf](https://example.com/document.pdf) - External URL
    - [pdf](./local/document.pdf) - Local PDF file (will be uploaded)
    - [pdf](C:\Documents\report.pdf) - Absolute local path (will be uploaded)
    - [pdf](https://example.com/document.pdf)(caption:Annual Report 2024) - With caption
    - [pdf](notion://file_id_here)(caption:Notion hosted file) - Notion hosted file
    - [pdf](upload://upload_id_here)(caption:File upload) - File upload
    """

    PDF_PATTERN = re.compile(r"\[pdf\]\(([^)]+)\)")

    @classmethod
    def match_notion(cls, block: Block) -> bool:
        """Match Notion PDF blocks."""
        return block.type == BlockType.PDF and block.pdf

    @classmethod
    async def markdown_to_notion(cls, text: str) -> Optional[BlockCreateResult]:
        """Convert markdown PDF link to Notion PDF block."""
        pdf_path = cls._extract_pdf_path(text.strip())

        if not pdf_path:
            return None

        cls.logger.info(f"Processing PDF: {pdf_path}")

        # Extract caption
        caption_text = cls.extract_caption(text.strip())
        caption_rich_text = cls.build_caption_rich_text(caption_text or "")

        # Handle different types of PDF sources
        if pdf_path.startswith(("notion://", "upload://")):
            # Handle special Notion schemes (existing functionality)
            cls.logger.info(f"Using special scheme: {pdf_path}")
            pdf_block = FileBlock(
                type=FileType.EXTERNAL,
                external=ExternalFile(url=pdf_path),
                caption=caption_rich_text,
            )

        elif cls._is_local_file_path(pdf_path):
            # Handle local PDF file upload using mixin
            cls.logger.debug(f"Detected local PDF file: {pdf_path}")

            # Upload the local PDF file with PDF category validation
            file_upload_id = await cls._upload_local_file(pdf_path, "pdf")
            if not file_upload_id:
                cls.logger.error(f"Failed to upload PDF: {pdf_path}")
                return None

            # Create FILE_UPLOAD block
            pdf_block = FileBlock(
                type=FileType.FILE_UPLOAD,
                file_upload=FileUploadFile(id=file_upload_id),
                caption=caption_rich_text,
            )

        else:
            # Handle external URL
            cls.logger.debug(f"Using external PDF URL: {pdf_path}")

            pdf_block = FileBlock(
                type=FileType.EXTERNAL,
                external=ExternalFile(url=pdf_path),
                caption=caption_rich_text,
            )

        return CreatePdfBlock(pdf=pdf_block)

    @classmethod
    async def notion_to_markdown(cls, block: Block) -> Optional[str]:
        """Convert Notion PDF block to markdown."""
        if block.type != BlockType.PDF or not block.pdf:
            return None

        pb: FileBlock = block.pdf

        # Determine the source for markdown
        if pb.type == FileType.EXTERNAL and pb.external:
            source = pb.external.url
        elif pb.type == FileType.FILE and pb.file:
            source = pb.file.url
        else:
            return None

        result = f"[pdf]({source})"

        # Add caption if present
        caption_markdown = await cls.format_caption_for_markdown(pb.caption or [])
        if caption_markdown:
            result += caption_markdown

        return result

    @classmethod
    def get_system_prompt_information(cls) -> Optional[BlockElementMarkdownInformation]:
        """Get system prompt information for PDF blocks."""
        return BlockElementMarkdownInformation(
            block_type=cls.__name__,
            description="PDF blocks embed and display PDF documents from external URLs or upload local PDF files with optional captions",
            syntax_examples=[
                "[pdf](https://example.com/document.pdf)",
                "[pdf](./local/report.pdf)",
                "[pdf](C:\\Documents\\manual.pdf)",
                "[pdf](https://example.com/report.pdf)(caption:Annual Report 2024)",
                "(caption:User Manual)[pdf](./manual.pdf)",
                "[pdf](./guide.pdf)(caption:**Important** documentation)",
            ],
            usage_guidelines="Use for embedding PDF documents that can be viewed inline. Supports both external URLs and local PDF file uploads. Local PDF files will be automatically uploaded to Notion. Caption supports rich text formatting and should describe the PDF content.",
        )

    @classmethod
    def _extract_pdf_path(cls, text: str) -> Optional[str]:
        """Extract PDF path/URL from text, handling caption patterns."""
        clean_text = cls.remove_caption(text)

        match = cls.PDF_PATTERN.search(clean_text)
        if match:
            return match.group(1).strip()

        return None
