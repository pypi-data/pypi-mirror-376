from __future__ import annotations

from typing import List, Optional

from notionary.user.base_notion_user import BaseNotionUser
from notionary.user.client import NotionUserClient
from notionary.user.models import NotionUserResponse
from notionary.util import factory_only
from notionary.util.fuzzy import find_best_matches


class NotionUser(BaseNotionUser):
    """
    Manager for Notion person users.
    Handles person-specific operations and information.
    """

    NO_USERS_FOUND_MSG = "No users found in workspace"
    NO_PERSON_USERS_FOUND_MSG = "No person users found in workspace"

    @factory_only("from_user_id", "from_user_response", "from_name")
    def __init__(
        self,
        user_id: str,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        email: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """Initialize person user with person-specific properties."""
        super().__init__(user_id, name, avatar_url, token)
        self._email = email

    @classmethod
    async def from_user_id(
        cls, user_id: str, token: Optional[str] = None
    ) -> Optional[NotionUser]:
        """
        Create a NotionUser from a user ID.
        """
        client = NotionUserClient(token=token)
        user_response = await client.get_user(user_id)

        if user_response is None:
            cls.logger.error("Failed to load user data for ID: %s", user_id)
            return None

        # Ensure this is actually a person user
        if user_response.type != "person":
            cls.logger.error(
                "User %s is not a person user (type: %s)", user_id, user_response.type
            )
            return None

        return cls._create_from_response(user_response, token)

    @classmethod
    async def from_name(
        cls, name: str, token: Optional[str] = None, min_similarity: float = 0.6
    ) -> Optional[NotionUser]:
        """
        Create a NotionUser by finding a person user with fuzzy matching on the name.
        """
        from notionary.util import find_best_match

        client = NotionUserClient(token=token)

        try:
            # Get all users from workspace
            all_users_response = await client.get_all_users()

            if not all_users_response:
                cls.logger.warning(cls.NO_USERS_FOUND_MSG)
                raise ValueError(cls.NO_USERS_FOUND_MSG)

            person_users = [
                user
                for user in all_users_response
                if user.type == "person" and user.name
            ]

            if not person_users:
                cls.logger.warning(cls.NO_PERSON_USERS_FOUND_MSG)
                raise ValueError(cls.NO_PERSON_USERS_FOUND_MSG)

            cls.logger.debug(
                "Found %d person users for fuzzy matching: %s",
                len(person_users),
                [user.name for user in person_users[:5]],
            )

            # Use fuzzy matching to find best match
            best_match = find_best_match(
                query=name,
                items=person_users,
                text_extractor=lambda user: user.name or "",
                min_similarity=min_similarity,
            )

            if not best_match:
                available_names = [user.name for user in person_users[:5]]
                cls.logger.warning(
                    "No sufficiently similar person user found for '%s' (min: %.3f). Available: %s",
                    name,
                    min_similarity,
                    available_names,
                )
                raise ValueError(
                    f"No sufficiently similar person user found for '{name}'"
                )

            cls.logger.info(
                "Found best match: '%s' with similarity %.3f for query '%s'",
                best_match.matched_text,
                best_match.similarity,
                name,
            )

            # Create NotionUser from the matched user response
            return cls._create_from_response(best_match.item, token)

        except Exception as e:
            cls.logger.error("Error finding user by name '%s': %s", name, str(e))
            raise

    @classmethod
    def from_user_response(
        cls, user_response: NotionUserResponse, token: Optional[str] = None
    ) -> NotionUser:
        """
        Create a NotionUser from an existing API response.
        """
        if user_response.type != "person":
            raise ValueError(f"Cannot create NotionUser from {user_response.type} user")

        return cls._create_from_response(user_response, token)

    @classmethod
    async def search_users_by_name(
        cls,
        name: str,
        token: Optional[str] = None,
        min_similarity: float = 0.3,
        limit: Optional[int] = 5,
    ) -> List[NotionUser]:
        """
        Search for multiple person users by name using fuzzy matching.

        Args:
            name: The name to search for
            token: Optional Notion API token
            min_similarity: Minimum similarity threshold (0.0 to 1.0), default 0.3
            limit: Maximum number of results to return, default 5

        Returns:
            List[NotionUser]: List of matching users sorted by similarity (best first)
        """
        client = NotionUserClient(token=token)

        try:
            # Get all users from workspace
            all_users_response = await client.get_all_users()

            if not all_users_response:
                cls.logger.warning(cls.NO_USERS_FOUND_MSG)
                return []

            # Filter to only person users (not bots)
            person_users = [
                user
                for user in all_users_response
                if user.type == "person" and user.name
            ]

            if not person_users:
                cls.logger.warning(cls.NO_PERSON_USERS_FOUND_MSG)
                return []

            # Use fuzzy matching to find all matches
            matches = find_best_matches(
                query=name,
                items=person_users,
                text_extractor=lambda user: user.name or "",
                min_similarity=min_similarity,
                limit=limit,
            )

            cls.logger.info(
                "Found %d matching users for query '%s'", len(matches), name
            )

            # Convert to NotionUser instances
            result_users = []
            for match in matches:
                try:
                    user = cls._create_from_response(match.item, token)
                    result_users.append(user)
                except Exception as e:
                    cls.logger.warning(
                        "Failed to create user from match '%s': %s",
                        match.matched_text,
                        str(e),
                    )
                    continue

            return result_users

        except Exception as e:
            cls.logger.error("Error searching users by name '%s': %s", name, str(e))
            return []

    @property
    def email(self) -> Optional[str]:
        """
        Get the user email (requires proper integration capabilities).
        """
        return self._email

    @property
    def user_type(self) -> str:
        """Get the user type."""
        return "person"

    @property
    def is_person(self) -> bool:
        """Check if this is a person user."""
        return True

    @property
    def is_bot(self) -> bool:
        """Check if this is a bot user."""
        return False

    @classmethod
    def _create_from_response(
        cls, user_response: NotionUserResponse, token: Optional[str]
    ) -> NotionUser:
        """Create NotionUser instance from API response."""
        email = user_response.person.email if user_response.person else None

        instance = cls(
            user_id=user_response.id,
            name=user_response.name,
            avatar_url=user_response.avatar_url,
            email=email,
            token=token,
        )

        cls.logger.info(
            "Created person user: '%s' (ID: %s)",
            user_response.name or "Unknown",
            user_response.id,
        )

        return instance
