from .abstract_downloader import LogDownloader


class RoundLogDownloader(LogDownloader):
    def __init__(self, start_round: int, end_round: int, output_path: str) -> None:
        self.output_path = output_path
