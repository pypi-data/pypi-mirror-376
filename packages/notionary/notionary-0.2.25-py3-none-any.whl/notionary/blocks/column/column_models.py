from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from notionary.blocks.models import BlockCreateRequest


class ColumnBlock(BaseModel):
    width_ratio: Optional[float] = None
    children: list[BlockCreateRequest] = Field(default_factory=list)


class CreateColumnBlock(BaseModel):
    type: Literal["column"] = "column"
    column: ColumnBlock


class ColumnListBlock(BaseModel):
    children: list[CreateColumnBlock] = Field(default_factory=list)


class CreateColumnListBlock(BaseModel):
    type: Literal["column_list"] = "column_list"
    column_list: ColumnListBlock
