from __future__ import annotations
from typing import Annotated, Iterable

from colorama import Fore

from .slur_file import SLURS
from .word_detection import detect_word


class SlurDetector:
    """Opens the file and scans for slurs. Results stored in tally"""

    total_lines_scanned: Annotated[int, "Total amount of lines scanned"]
    tally: Annotated[dict[str, int], "A dictionary with strings (slurs) as keys, and their tally as key (int)"]
    slur_lines: Annotated[list[tuple[str, str]], "Stores all unmodified detected lines with the slur's position"]

    def __init__(self, text: Iterable[str]) -> None:
        self.reset_tally()
        self.scan_text(text)

    def reset_tally(self):
        """Resets the tally to 0"""
        self.tally = {}
        for slur in SLURS:
            self.tally[slur] = 0
        self.slur_lines = []
        self.total_lines_scanned = 0

    def scan_text(self, text: Iterable[str]) -> None:
        """Scans the text. Automatically called in __init__"""
        if not SLURS:
            print(f"{Fore.RED}ERROR:{Fore.RESET} No slurs found, aborting. Please open the slurs file in your " +
                  "favourite text editor, and add some slurs to it.")
            return
        for line in text:
            self.process_line(line)

    def process_line(self, text: str) -> None:
        """Processes one line and detects possible slurs"""
        self.total_lines_scanned += 1
        for slur in SLURS:
            if detect_word(slur, text):
                self.slur_lines.append((text.strip(), slur))
                self.tally[slur] += 1

    def print_tally(self):
        """Prints the slurs according to the tally"""
        print("\nSlurs:")
        none = True
        for key, value in self.tally.items():
            if value:
                none = False
                print(f"{key:>12}:    {value} ({value / self.total_lines_scanned * 100:0.03f} per line)")
        if none:
            print(f"{Fore.GREEN}None!{Fore.RESET}")

    def print_results(self):
        """Prints the results to the console"""
        print(f"Scanned {self.total_lines_scanned} lines.")
        self.print_slur_lines()
        self.print_tally()

    def print_slur_lines(self):
        """Prints all of the lines which have slurs in them"""
        print(f"{Fore.YELLOW}Lines with detected slurs:{Fore.RESET}")
        for slur_line, slur in self.slur_lines:
            print(slur_line.replace(slur, f"{Fore.RED}{slur}{Fore.RESET}"))

    @staticmethod
    def from_file(target_file: str) -> SlurDetector:
        """Opens the path and scans the contents with a new SlurDetector"""
        with open(target_file, "r", encoding="utf-8") as file:
            return SlurDetector(file)
