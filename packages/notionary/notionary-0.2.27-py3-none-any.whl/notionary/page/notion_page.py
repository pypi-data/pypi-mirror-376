from __future__ import annotations

from ast import Dict
import asyncio
import random
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

from yaml import Token

from notionary.blocks.client import NotionBlockClient
from notionary.comments import CommentClient, Comment
from notionary.blocks.syntax_prompt_builder import SyntaxPromptBuilder
from notionary.blocks.models import DatabaseParent, ParentObject
from notionary.blocks.registry.block_registry import BlockRegistry
from notionary.database.client import NotionDatabaseClient
from notionary.file_upload.client import NotionFileUploadClient
from notionary.blocks.markdown.markdown_builder import MarkdownBuilder
from notionary.schemas import NotionContentSchema
from notionary.page import page_context
from notionary.page.client import NotionPageClient
from notionary.page.models import NotionPageResponse
from notionary.page.page_content_deleting_service import PageContentDeletingService
from notionary.page.page_content_writer import PageContentWriter
from notionary.page.page_context import PageContextProvider, page_context
from notionary.page.property_formatter import NotionPropertyFormatter
from notionary.page.reader.page_content_retriever import PageContentRetriever
from notionary.page.utils import extract_property_value
from notionary.util import LoggingMixin, extract_uuid, factory_only, format_uuid
from notionary.util.fuzzy import find_best_match

if TYPE_CHECKING:
    from notionary import NotionDatabase


class NotionPage(LoggingMixin):
    """
    Managing content and metadata of a Notion page.
    """

    @factory_only("from_page_id", "from_page_name", "from_url")
    def __init__(
        self,
        page_id: str,
        title: str,
        url: str,
        archived: bool,
        in_trash: bool,
        emoji_icon: Optional[str] = None,
        external_icon_url: Optional[str] = None,
        properties: Optional[dict[str, Any]] = None,
        parent_database: Optional[NotionDatabase] = None,
        token: Optional[str] = None,
    ):
        """
        Initialize the page manager with all metadata.
        """
        self._page_id = page_id
        self._title = title
        self._url = url
        self._is_archived = archived
        self._is_in_trash = in_trash
        self._emoji_icon = emoji_icon
        self._external_icon_url = external_icon_url
        self._properties = properties
        self._parent_database = parent_database

        self._client = NotionPageClient(token=token)
        self._block_client = NotionBlockClient(token=token)
        self._database_client = NotionDatabaseClient(token=token)
        self._comment_client = CommentClient(token=token)
        self._page_data = None

        self.block_element_registry = BlockRegistry.create_registry()

        self._page_content_writer = PageContentWriter(
            page_id=self._page_id,
            block_registry=self.block_element_registry,
        )

        self._page_content_deleting_service = PageContentDeletingService(
            page_id=self._page_id,
            block_registry=self.block_element_registry,
        )

        self._page_content_retriever = PageContentRetriever(
            block_registry=self.block_element_registry,
        )

        self.page_context_provider = self._setup_page_context_provider()

    @classmethod
    async def from_page_id(
        cls, page_id: str, token: Optional[str] = None
    ) -> NotionPage:
        """
        Create a NotionPage from a page ID.
        """
        formatted_id = format_uuid(page_id) or page_id

        async with NotionPageClient(token=token) as client:
            page_response = await client.get_page(formatted_id)
            return await cls._create_from_response(page_response, token)

    @classmethod
    async def from_page_name(
        cls, page_name: str, token: Optional[str] = None, min_similarity: float = 0.6
    ) -> NotionPage:
        """
        Create a NotionPage by finding a page with fuzzy matching on the title.
        Uses Notion's search API and fuzzy matching to find the best result.
        """
        from notionary.workspace import NotionWorkspace

        workspace = NotionWorkspace()

        try:
            search_results: list[NotionPage] = await workspace.search_pages(
                page_name, limit=5
            )

            if not search_results:
                cls.logger.warning("No pages found for name: %s", page_name)
                raise ValueError(f"No pages found for name: {page_name}")

            best_match = find_best_match(
                query=page_name,
                items=search_results,
                text_extractor=lambda page: page.title,
                min_similarity=min_similarity,
            )

            if not best_match:
                available_titles = [result.title for result in search_results[:5]]
                cls.logger.warning(
                    "No sufficiently similar page found for '%s' (min: %.3f). Available: %s",
                    page_name,
                    min_similarity,
                    available_titles,
                )
                raise ValueError(
                    f"No sufficiently similar page found for '{page_name}'"
                )

            async with NotionPageClient(token=token) as client:
                page_response = await client.get_page(page_id=best_match.item.id)
                instance = await cls._create_from_response(
                    page_response=page_response, token=token
                )
                return instance

        except Exception as e:
            cls.logger.error("Error finding page by name: %s", str(e))
            raise

    @classmethod
    async def from_url(cls, url: str, token: Optional[str] = None) -> NotionPage:
        """
        Create a NotionPage from a Notion page URL.
        """
        try:
            page_id = extract_uuid(url)
            if not page_id:
                raise ValueError(f"Could not extract page ID from URL: {url}")

            formatted_id = format_uuid(page_id) or page_id

            async with NotionPageClient(token=token) as client:
                page_response = await client.get_page(formatted_id)
                return await cls._create_from_response(page_response, token)

        except Exception as e:
            cls.logger.error("Error creating page from URL '%s': %s", url, str(e))
            raise

    @property
    def id(self) -> str:
        """
        Get the ID of the page.
        """
        return self._page_id

    @property
    def title(self) -> str:
        """
        Get the title of the page.
        """
        return self._title

    @property
    def url(self) -> str:
        """
        Get the URL of the page.
        If not set, generate it from the title and ID.
        """
        return self._url

    @property
    def external_icon_url(self) -> Optional[str]:
        """
        Get the icon of the page.
        """
        return self._external_icon_url

    @property
    def emoji_icon(self) -> Optional[str]:
        """
        Get the emoji icon of the page.
        """
        return self._emoji_icon

    @property
    def properties(self) -> Optional[dict[str, Any]]:
        """
        Get the properties of the page.
        """
        return self._properties

    @property
    def is_archived(self) -> bool:
        return self._is_archived

    @property
    def is_in_trash(self) -> bool:
        return self._is_in_trash

    def get_prompt_information(self) -> str:
        markdown_syntax_builder = SyntaxPromptBuilder()
        return markdown_syntax_builder.build_concise_reference()

    async def get_comments(self) -> list[Comment]:
        return await self._comment_client.list_all_comments_for_page(
            page_id=self._page_id
        )

    async def post_comment(
        self,
        content: str,
        *,
        discussion_id: Optional[str] = None,
        rich_text: Optional[list[dict[str, Any]]] = None,
    ) -> Optional[Comment]:
        """
        Post a comment on this page.

        Args:
            content: The plain text content of the comment
            discussion_id: Optional discussion ID to reply to an existing discussion
            rich_text: Optional rich text formatting for the comment content

        Returns:
            Comment: The created comment object, or None if creation failed
        """
        try:
            # Use the comment client to create the comment
            comment = await self._comment_client.create_comment(
                page_id=self._page_id,
                content=content,
                discussion_id=discussion_id,
                rich_text=rich_text,
            )
            self.logger.info(f"Successfully posted comment on page '{self._title}'")
            return comment
        except Exception as e:
            self.logger.error(
                f"Failed to post comment on page '{self._title}': {str(e)}"
            )
            return None

    async def set_title(self, title: str) -> str:
        """
        Set the title of the page.
        """
        try:
            data = {
                "properties": {
                    "title": {"title": [{"type": "text", "text": {"content": title}}]}
                }
            }

            await self._client.patch_page(self._page_id, data)

            self._title = title
            return title

        except Exception as e:
            self.logger.error("Error setting page title: %s", str(e))

    async def append_markdown(
        self,
        content: Union[
            str, Callable[[MarkdownBuilder], MarkdownBuilder], NotionContentSchema
        ],
    ) -> bool:
        """
        Append markdown content to the page using text, builder callback, MarkdownDocumentModel, or NotionContentSchema.
        """
        async with page_context(self.page_context_provider):
            result = await self._page_content_writer.append_markdown(
                content=content,
            )
            return result is not None

    async def replace_content(
        self,
        content: Union[
            str, Callable[[MarkdownBuilder], MarkdownBuilder], NotionContentSchema
        ],
    ) -> bool:
        """
        Replace the entire page content with new markdown content.

        Args:
            content: Either raw markdown text, a callback function that receives a MarkdownBuilder,
                    a MarkdownDocumentModel, or a NotionContentSchema

        Returns:
            bool: True if successful, False otherwise
        """
        clear_result = await self._page_content_deleting_service.clear_page_content()
        if not clear_result:
            self.logger.error("Failed to clear page content before replacement")

        result = await self._page_content_writer.append_markdown(
            content=content,
        )
        return result is not None

    async def clear_page_content(self) -> str:
        """
        Clear all content from the page.
        """
        return await self._page_content_deleting_service.clear_page_content()

    async def get_text_content(self) -> str:
        """
        Get the text content of the page.

        Returns:
            str: The text content of the page.
        """
        blocks = await self._block_client.get_blocks_by_page_id_recursively(
            page_id=self._page_id
        )
        return await self._page_content_retriever.convert_to_markdown(blocks=blocks)

    async def set_emoji_icon(self, emoji: str) -> Optional[str]:
        """
        Sets the page icon to an emoji.
        """
        try:
            icon = {"type": "emoji", "emoji": emoji}
            page_response = await self._client.patch_page(
                page_id=self._page_id, data={"icon": icon}
            )

            self._emoji = page_response.icon.emoji
            self._external_icon_url = None
            return page_response.icon.emoji
        except Exception as e:

            self.logger.error(f"Error updating page emoji: {str(e)}")
            return None

    async def set_external_icon(self, url: str) -> Optional[str]:
        """
        Sets the page icon to an external image.
        """
        try:
            icon = {"type": "external", "external": {"url": url}}
            page_response = await self._client.patch_page(
                page_id=self._page_id, data={"icon": icon}
            )

            self._icon = url
            self._emoji = None
            self.logger.info(f"Successfully updated page external icon to: {url}")
            return page_response.icon.external.url

        except Exception as e:
            self.logger.error(f"Error updating page external icon: {str(e)}")
            return None

    async def create_child_database(self, title: str) -> NotionDatabase:
        from notionary import NotionDatabase

        database_client = NotionDatabaseClient(token=self._client.token)

        create_database_response = await database_client.create_database(
            title=title,
            parent_page_id=self._page_id,
        )

        return await NotionDatabase.from_database_id(
            id=create_database_response.id, token=self._client.token
        )

    async def create_child_page(self, title: str) -> NotionPage:
        from notionary import NotionPage

        child_page_response = await self._client.create_page(
            parent_page_id=self._page_id,
            title=title,
        )

        return await NotionPage.from_page_id(
            page_id=child_page_response.id, token=self._client.token
        )

    async def set_external_icon(self, url: str) -> Optional[str]:
        """
        Sets the page icon to an external image.
        """
        try:
            icon = {"type": "external", "external": {"url": url}}
            page_response = await self._client.patch_page(
                page_id=self._page_id, data={"icon": icon}
            )

            # For external icons, we clear the emoji since we now have external icon
            self._emoji = None
            self.logger.info(f"Successfully updated page external icon to: {url}")
            return page_response.icon.external.url

        except Exception as e:
            self.logger.error(f"Error updating page external icon: {str(e)}")
            return None

    async def get_cover_url(self) -> Optional[str]:
        """
        Get the URL of the page cover image.
        """
        try:
            page_data = await self._client.get_page(self.id)
            if not page_data or not page_data.cover:
                return None
            if page_data.cover.type == "external":
                return page_data.cover.external.url
        except Exception as e:
            self.logger.error(f"Error fetching cover URL: {str(e)}")
            return None

    async def set_cover(self, external_url: str) -> Optional[str]:
        """
        Set the cover image for the page using an external URL.
        """
        data = {"cover": {"type": "external", "external": {"url": external_url}}}
        try:
            updated_page = await self._client.patch_page(self.id, data=data)
            return updated_page.cover.external.url
        except Exception as e:
            self.logger.error("Failed to set cover image: %s", str(e))
            return None

    async def set_random_gradient_cover(self) -> Optional[str]:
        """
        Set a random gradient as the page cover.
        """
        default_notion_covers = [
            f"https://www.notion.so/images/page-cover/gradients_{i}.png"
            for i in range(1, 10)
        ]
        random_cover_url = random.choice(default_notion_covers)
        return await self.set_cover(random_cover_url)

    async def get_property_value_by_name(self, property_name: str) -> Any:
        """
        Get the value of a specific property.
        """
        if property_name not in self._properties:
            self.logger.warning(
                "Property '%s' not found in page properties", property_name
            )
            return None

        property_schema: dict = self._properties.get(property_name)

        property_type = property_schema.get("type")

        if property_type == "relation":
            return await self._get_relation_property_values_by_name(property_name)

        return extract_property_value(property_schema)

    async def _get_relation_property_values_by_name(
        self, property_name: str
    ) -> list[str]:
        """
        Retrieve the titles of all related pages for a relation property.
        """
        page_property_schema = self._properties.get(property_name)
        relation_page_ids = [
            rel.get("id") for rel in page_property_schema.get("relation", [])
        ]
        notion_pages = [
            await NotionPage.from_page_id(page_id) for page_id in relation_page_ids
        ]
        return [page.title for page in notion_pages if page]

    async def get_options_for_property_by_name(self, property_name: str) -> list[str]:
        """
        Get the available options for a property (select, multi_select, status, relation).
        """
        if property_name not in self.properties:
            self.logger.warning(
                "Property '%s' not found in page properties", property_name
            )
            return []

        property_schema: dict = self.properties.get(property_name)
        property_type = property_schema.get("type")

        if property_type in ["select", "multi_select", "status"]:
            options = property_schema.get(property_type, {}).get("options", [])
            return [option.get("name", "") for option in options]

        if property_type == "relation" and self._parent_database:
            return await self._parent_database._get_relation_options(property_name)

        return []

    # Fix this for pages that do not ah
    async def set_property_value_by_name(self, property_name: str, value: Any) -> Any:
        """
        Set the value of a specific property by its name.
        """
        if not self._parent_database:
            return None

        property_type = self._parent_database.properties.get(property_name).get("type")

        if not property_type:
            return None

        if property_type == "relation":
            return await self.set_relation_property_values_by_name(
                property_name=property_name, page_titles=value
            )

        property_formatter = NotionPropertyFormatter()
        update_data = property_formatter.format_value(
            property_name=property_name, property_type=property_type, value=value
        )

        try:
            updated_page_response = await self._client.patch_page(
                page_id=self._page_id, data=update_data
            )
            self._properties = updated_page_response.properties
            return extract_property_value(self._properties.get(property_name))
        except Exception as e:
            self.logger.error(
                "Error setting property '%s' to value '%s': %s",
                property_name,
                value,
                str(e),
            )
            return None

    async def set_relation_property_values_by_name(
        self, property_name: str, page_titles: list[str]
    ) -> list[str]:
        """
        Add one or more relations to a relation property.
        """
        if not self._parent_database:
            return []

        property_type = self._parent_database.properties.get(property_name).get("type")

        # for direct calls
        if property_type != "relation":
            return []

        relation_pages = await asyncio.gather(
            *(
                NotionPage.from_page_name(page_name=page_title)
                for page_title in page_titles
            )
        )

        relation_page_ids = [page.id for page in relation_pages]

        property_formatter = NotionPropertyFormatter()

        update_data = property_formatter.format_value(
            property_name=property_name,
            property_type="relation",
            value=relation_page_ids,
        )

        try:
            updated_page_response = await self._client.patch_page(
                page_id=self._page_id, data=update_data
            )
            self._properties = updated_page_response.properties
            return page_titles
        except Exception as e:
            self.logger.error(
                "Error setting property '%s' to value '%s': %s",
                property_name,
                page_titles,
                str(e),
            )
            return []

    async def archive(self) -> bool:
        """
        Archive the page by moving it to the trash.
        """
        try:
            result = await self._client.patch_page(
                page_id=self._page_id, data={"archived": True}
            )
            return result is not None
        except Exception as e:
            self.logger.error("Error archiving page %s: %s", self._page_id, str(e))
            return False

    @classmethod
    async def _create_from_response(
        cls,
        page_response: NotionPageResponse,
        token: Optional[str],
    ) -> NotionPage:
        """
        Create NotionPage instance from API response.
        """
        from notionary.database.database import NotionDatabase

        title = cls._extract_title(page_response)
        emoji_icon = cls._extract_page_emoji_icon(page_response)
        external_icon_url = cls._extract_external_icon_url(page_response)
        parent_database_id = cls._extract_parent_database_id(page_response)

        parent_database = (
            await NotionDatabase.from_database_id(id=parent_database_id, token=token)
            if parent_database_id
            else None
        )

        instance = cls(
            page_id=page_response.id,
            title=title,
            url=page_response.url,
            emoji_icon=emoji_icon,
            external_icon_url=external_icon_url,
            archived=page_response.archived,
            in_trash=page_response.in_trash,
            properties=page_response.properties,
            parent_database=parent_database,
            token=token,
        )

        cls.logger.info("Created page manager: '%s' (ID: %s)", title, page_response.id)
        return instance

    @staticmethod
    def _extract_title(page_response: NotionPageResponse) -> str:
        """Extract title from page response. Returns empty string if not found."""

        if not page_response.properties:
            return ""

        title_property = next(
            (
                prop
                for prop in page_response.properties.values()
                if isinstance(prop, dict) and prop.get("type") == "title"
            ),
            None,
        )

        if not title_property or "title" not in title_property:
            return ""

        try:
            title_parts = title_property["title"]
            return "".join(part.get("plain_text", "") for part in title_parts)
        except (KeyError, TypeError, AttributeError):
            return ""

    @staticmethod
    def _extract_page_emoji_icon(page_response: NotionPageResponse) -> Optional[str]:
        """Extract external icon URL from page response."""
        if not page_response.icon:
            return None

        if page_response.icon.type == "emoji":
            return page_response.icon.emoji

    @staticmethod
    def _extract_external_icon_url(page_response: NotionPageResponse) -> Optional[str]:
        """Extract emoji from database response."""
        if not page_response.icon:
            return None

        if page_response.icon.type == "external":
            return page_response.icon.external.url

    @staticmethod
    def _extract_parent_database_id(page_response: NotionPageResponse) -> Optional[str]:
        """Extract parent database ID from page response."""
        parent = page_response.parent
        if isinstance(parent, DatabaseParent):
            return parent.database_id

    def _setup_page_context_provider(self) -> PageContextProvider:
        return PageContextProvider(
            page_id=self._page_id,
            database_client=NotionDatabaseClient(token=self._client.token),
            file_upload_client=NotionFileUploadClient(),
        )
