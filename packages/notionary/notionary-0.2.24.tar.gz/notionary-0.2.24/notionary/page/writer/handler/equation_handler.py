import re

from notionary.blocks.equation.equation_element import EquationElement
from notionary.page.writer.handler.line_handler import (
    LineHandler,
    LineProcessingContext,
)


class EquationHandler(LineHandler):
    """Handles equation block specific logic with batching.

    Markdown syntax:
    $$
    \sum_{i=1}^n i = \frac{n(n+1)}{2} \\
    \sum_{i=1}^n i^2 = \frac{n(n+1)(2n+1)}{6} \\
    \sum_{i=1}^n i^3 = \left(\frac{n(n+1)}{2}\right)^2
    $$
    """

    def __init__(self):
        super().__init__()
        self._equation_start_pattern = re.compile(r"^\$\$\s*$")
        self._equation_end_pattern = re.compile(r"^\$\$\s*$")

    def _can_handle(self, context: LineProcessingContext) -> bool:
        if self._is_inside_parent_context(context):
            return False
        return self._is_equation_start(context)

    async def _process(self, context: LineProcessingContext) -> None:
        if self._is_equation_start(context):
            await self._process_complete_equation_block(context)
            self._mark_processed(context)

    def _is_equation_start(self, context: LineProcessingContext) -> bool:
        """Check if this line starts an equation block."""
        return self._equation_start_pattern.match(context.line.strip()) is not None

    def _is_inside_parent_context(self, context: LineProcessingContext) -> bool:
        """Check if we're currently inside any parent context (toggle, heading, etc.)."""
        return len(context.parent_stack) > 0

    async def _process_complete_equation_block(
        self, context: LineProcessingContext
    ) -> None:
        """Process the entire equation block in one go using EquationElement."""
        equation_lines, lines_to_consume = self._collect_equation_lines(context)

        block = EquationElement.create_from_markdown_block(
            opening_line=context.line, equation_lines=equation_lines
        )

        if block:
            context.lines_consumed = lines_to_consume
            context.result_blocks.append(block)

    def _collect_equation_lines(
        self, context: LineProcessingContext
    ) -> tuple[list[str], int]:
        """Collect lines until closing $$ fence and return (lines, count_to_consume)."""
        lines = []
        for idx, ln in enumerate(context.get_remaining_lines()):
            if self._equation_end_pattern.match(ln.strip()):
                return lines, idx + 1
            lines.append(ln)
        # No closing fence: consume all remaining
        rem = context.get_remaining_lines()
        return rem, len(rem)

    def _mark_processed(self, context: LineProcessingContext) -> None:
        """Mark context as processed and continue."""
        context.was_processed = True
        context.should_continue = True
