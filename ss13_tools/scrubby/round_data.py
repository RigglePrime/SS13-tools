# pylint: disable=invalid-name
# Enable type hinting for static methods
from __future__ import annotations
import json
from typing import Optional, Annotated, Any
from dataclasses import dataclass

from aiohttp import ClientResponse


@dataclass
class PlayerRoundData:  # pylint: disable=too-many-instance-attributes
    """Represents round data from Scrubby"""
    roundID: int
    job: Optional[str]
    timestamp: Annotated[str, "ISO 8601, YYYY-MM-DDThh:mm:ss.ffffZ"]
    connectedTime: Annotated[str, "hh:mm:ss.fffffff"]
    roundStartPlayer: bool
    playedInRound: bool
    antagonist: bool
    roundStartSuicide: bool
    isSecurity: bool
    firstSuicide: bool
    firstSuicideEvidence: Optional[Any]
    name: Optional[str]
    server: str

    @staticmethod
    async def from_scrubby_response_async(r: ClientResponse) -> list[PlayerRoundData]:
        """Converts a Scrubby JSON response directly to a Python RoundData object"""
        return json.loads(await r.text(), object_hook=lambda d: PlayerRoundData(**d))


@dataclass
class RoundInfo:
    """Stores basic info about a round"""
    round_id: int
    server: str
    timestamp: Annotated[str, "ISO 8601, YYYY-MM-DDThh:mm:ss.ffffZ"]
