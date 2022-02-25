# Enable type hinting for static methods
from __future__ import annotations
from typing import Optional, Annotated, Any
from dataclasses import dataclass

from requests import Response

@dataclass
class RoundData:
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
    def from_scrubby_response(r: Response) -> list[RoundData]:
        return r.json(object_hook = lambda d: RoundData(**d))