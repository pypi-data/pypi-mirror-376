from typing import Optional
from notionary.blocks.markdown.markdown_node import MarkdownNode


class CalloutMarkdownNode(MarkdownNode):
    """
    Enhanced Callout node with Pydantic integration.
    Programmatic interface for creating Notion-style callout Markdown blocks.
    Example: [callout](This is important "⚠️")
    """

    text: str
    emoji: Optional[str] = None

    def to_markdown(self) -> str:
        if self.emoji and self.emoji != "💡":
            return f'[callout]({self.text} "{self.emoji}")'
        else:
            return f"[callout]({self.text})"
