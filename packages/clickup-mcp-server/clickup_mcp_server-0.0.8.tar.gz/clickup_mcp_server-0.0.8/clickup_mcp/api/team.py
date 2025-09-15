"""
Team API resource manager.

This module provides a resource manager for interacting with ClickUp Teams/Workspaces.
It follows the Resource Manager pattern described in the project documentation.
"""

from typing import TYPE_CHECKING, List

from clickup_mcp.models.domain.team import ClickUpTeam

if TYPE_CHECKING:
    from clickup_mcp.client import ClickUpAPIClient


class TeamAPI:
    """Team API resource manager.

    This class provides methods for interacting with ClickUp Teams/Workspaces through
    the ClickUp API. It follows the Resource Manager pattern, receiving
    a shared HTTP client instance and providing domain-specific methods.
    """

    def __init__(self, client: "ClickUpAPIClient"):
        """Initialize the TeamAPI.

        Args:
            client: The ClickUpAPIClient instance to use for API requests.
        """
        self._client = client

    async def get_authorized_teams(self) -> List[ClickUpTeam]:
        """Get authorized teams/workspaces available to the authenticated user.

        Returns:
            A list of ClickUpTeam instances representing the authorized teams/workspaces.
            Returns an empty list if no teams are found or if an error occurs.
        """
        response = await self._client.get("/team")

        if not response.success or response.status_code != 200:
            return []

        # Ensure response.data is a valid dictionary before processing
        if response.data is None or not isinstance(response.data, dict) or "teams" not in response.data:
            return []

        teams_data = response.data["teams"]
        if not isinstance(teams_data, list):
            return []

        # Create a list of ClickUpTeam instances
        return [ClickUpTeam(**team_data) for team_data in teams_data]
