"""
API module for ClickUp API resource managers.

This module exports the API resource manager classes that provide a higher-level
interface for interacting with the ClickUp API.
"""

from .space import SpaceAPI
from .team import TeamAPI

__all__ = [
    "SpaceAPI",
    "TeamAPI",
]
