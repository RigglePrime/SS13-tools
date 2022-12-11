from .SlurFile import SLURS

from colorama import Fore
from typing import Annotated, Iterable


class SlurDetector:
    """Opens the file and scans for slurs. Results stored in tally"""

    tally: Annotated[dict[str, int], "A dictionary with strings (slurs) as keys, and their tally as key (int)"]
    slur_lines: Annotated[list[tuple[str, str]], "Stores all unmodified detected lines with the slur's position"]

    def __init__(self, text: Iterable[str]) -> None:
        self.reset_tally()
        self.scan_text(text)

    def reset_tally(self):
        self.tally = {}
        for slur in SLURS:
            self.tally[slur] = 0
        self.slur_lines = []

    def scan_text(self, text: Iterable[str]) -> None:
        """Scans the text. Automatically called in __init__"""
        for line in text:
            self.process_line(line)

    def process_line(self, text: str) -> None:
        """Processes one line and detects possible slurs"""
        for slur in SLURS:
            if self.detect_word(slur, text):
                self.slur_lines.append((text.strip(), slur))
                self.tally[slur] += 1

    @staticmethod
    def detect_word(word: str, text: str) -> bool:
        """Detects if the specified word is in the text"""
        # TODO: improve functionality
        # TODO: add Snowflake stemmer maybe?
        return True if word in text else False

    def print_tally(self):
        """Prints the slurs according to the tally"""
        print("\nSlurs:")
        none = True
        for key, value in self.tally.items():
            if value:
                none = False
                print(f"{key}\t{value}")
        if none:
            print(f"{Fore.GREEN}None!{Fore.RESET}")

    def print_results(self):
        """Prints the results to the console"""
        self.print_slur_lines()
        self.print_tally()

    def print_slur_lines(self):
        """Prints all of the lines which have slurs in them"""
        print(f"{Fore.YELLOW}Lines with detected slurs:{Fore.RESET}")
        for slur_line, slur in self.slur_lines:
            print(slur_line.replace(slur, f"{Fore.RED}{slur}{Fore.RESET}"))

    @staticmethod
    def from_file(target_file: str):
        with open(target_file, "r", encoding="utf-8") as f:
            return SlurDetector(f.readlines())
