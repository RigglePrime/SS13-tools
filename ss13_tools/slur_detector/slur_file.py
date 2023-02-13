import os

from colorama import Fore

from .constants import SLURS_FILE

if not os.path.exists(SLURS_FILE):
    with open(SLURS_FILE, "w", encoding='utf-8') as file:
        file.write("### Slurs file\n" +
                   "### One slur per line, # to ignore the line\n" +
                   "### The program will also skip empty lines\n\n")
    raise FileNotFoundError("Slurs file does not exist. Creating it for you. Please add some words to it.")

SLURS = []  # Should not be modified after filling up once
with open(SLURS_FILE, "r", encoding="utf-8") as file:
    for line in file.readlines():
        if line.strip() and not line.startswith('#'):
            SLURS.append(line.split('#', 1)[0].strip())

if not SLURS:
    print(f"{Fore.YELLOW}WARNING:{Fore.RESET} No slur entries detected! Please open the slurs file and add some.")

del SLURS_FILE  # Del as you probably don't want this constant anyway
