from typing import Annotated

from .abstract import LogDownloader


class RoundLogDownloader(LogDownloader):
    """Downloads a span of rounds"""
    lbound: Annotated[int, "Left boundary"]
    rbound: Annotated[int, "Right boundary"]

    def __init__(self, start_round: int, end_round: int, output_path: str) -> None:
        self.output_path = output_path
        self.lbound = min(start_round, end_round)
        self.rbound = max(start_round, end_round)
