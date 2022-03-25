#!/env/python3

import sys
import os
from typing import Annotated, Iterable

SLURS_FILE = "slurs"

if not os.path.exists(SLURS_FILE):
    with open(SLURS_FILE, "w") as f:
        f.write("### Slurs file\n### One slur per line, # to ignore the line\n### The program will also skip empty lines\n\n")
    raise FileNotFoundError("Slurs file does not exist. Creating it for you. Please add some words to it.")

SLURS = []
with open(SLURS_FILE, "r", encoding = "utf-8") as f: 
    for line in f.readlines():
        if line.strip() and not line.startswith('#'):
            SLURS.append(line.split('#', 1)[0].strip())

class SlurDetector:
    """Opens the file and scans for slurs. Results stored in tally"""

    tally: Annotated[dict[str, int], "A dictionary with strings (slurs) as keys, and their tally as key (int)"]
    slur_lines: Annotated[list[str], "Stores all detected lines, unmodified"]

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
        """Processes one line and detects possible sluts"""
        for slur in SLURS:
            if self.detect_word(slur, text):
                self.slur_lines.append(text.strip())
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
        if none: print("None!")

    def print_results(self):
        """Prints the results to the console"""
        self.print_slur_lines()
        self.print_tally()

    def print_slur_lines(self):
        """Prints all of the lines which have slurs in them"""
        print("Lines with detected slurs:")
        for slur_line in self.slur_lines:
            print(slur_line)

    @staticmethod
    def from_file(target_file: str):
        with open(target_file, "r", encoding = "utf-8") as f:
            return SlurDetector(f.readlines())

def main():
    if len(sys.argv) == 2: 
        file_name = sys.argv[1]
    else: 
        file_name = input("File name: ") 
    slursearch = SlurDetector.from_file(file_name)
    slursearch.print_results()

if __name__ == "__main__":
    main()