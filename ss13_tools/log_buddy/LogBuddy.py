#!/usr/bin/env python3
import inspect
import os
from typing import Any
from colorama import Fore, init as colorama_init

# Log is unused, but it's here so the user doesn't have to import it manually
from log import Log, LogType  # noqa: F401
from log_parser import LogFile
from version import VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH

# Change the help text, so users can more easily understand what to do
from _sitebuiltins import _Helper
_Helper.__repr__ = lambda self: f"""Welcome to {Fore.CYAN}LogBuddy{Fore.RESET}!
{Fore.YELLOW}Use right click to copy something, CTRL + C will terminate the program.{Fore.RESET}

Please see the latest documentation at {Fore.BLUE}https://github.com/RigglePrime/LogBuddy/blob/master/README.md{Fore.RESET}
To get started, type '{Fore.GREEN}LogFile.from_file("game.txt"){Fore.RESET}' (if there is a file named game.txt in the same directory) or '{Fore.GREEN}LogFile.from_folder("logs"){Fore.RESET}' (if your game.txt, attack.txt... are stored in a folder named logs)

Type '{Fore.GREEN}help(Log){Fore.RESET}' for information about the log, and '{Fore.GREEN}help(LogFile){Fore.RESET}' for information about log files.
Type '{Fore.GREEN}functions(object){Fore.RESET}' for a list of all defined functions and '{Fore.GREEN}variables(object){Fore.RESET}' for a list of all variables. Both are currently quite bad (I will get to it some day I promise).

{Fore.CYAN}LogBuddy{Fore.RESET} performs all operations on an internal work set, so you can chain filters (functions). To reset the work set, call '{Fore.GREEN}reset_work_set(){Fore.RESET}' on your log instance.

If {Fore.YELLOW}-- More --{Fore.RESET} is displayed on the bottom of the screen, press {Fore.YELLOW}return (enter){Fore.RESET} to advance one line, {Fore.YELLOW}space{Fore.RESET} to advance a screen or {Fore.YELLOW}q{Fore.RESET} to quit.
IPython (the thing you type in that displays 'In [2]:') will sometimes suggest commands. The gray part can be inserted by simply pressing {Fore.YELLOW}→{Fore.RESET}. Clear the current line by pressing {Fore.YELLOW}CTRL + C{Fore.RESET}.
You can exit by typing '{Fore.GREEN}exit{Fore.RESET}' or pressing {Fore.YELLOW}CTRL + D{Fore.RESET}.

For Python's interactive help, type '{Fore.GREEN}help(){Fore.RESET}', or '{Fore.GREEN}help(object){Fore.RESET}' for help about object (for example: '{Fore.GREEN}help(LogFile){Fore.RESET}')."""


def functions(cls: object) -> list[tuple[str, Any]]:
    """Returns all methods of an object"""
    return inspect.getmembers(cls, predicate=inspect.ismethod)


def variables(cls: object) -> dict[str, Any]:
    """Returns all variables of an object"""
    return cls.__dict__


if __name__ == "__main__":
    print("LogBuddy starting...")
    import argparse
    parser = argparse.ArgumentParser(description='Parses-the-logs')

    parser.add_argument("-v", "--verbose", action="store_true", help="Toggle verbose mode")
    parser.add_argument("-q", "--quiet", "--silent", action="store_true", help="Toggle silent mode")
    parser.add_argument("--version", action="version", version=f"LogBuddy v{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}")
    parser.add_argument("file", nargs="*", help="One or multiple log files or a single folder containing log files to parse")
    args = parser.parse_args()

    if args.verbose and args.quiet:
        print("Really? You want me to be silent and verbose? Those are mutually exclusive you know")
        exit(1)

    main_file = LogFile()

    if args.file:
        if len(args.file) == 1 and os.path.isdir(args.file[0]):
            main_file = LogFile.from_folder(args.file[0], verbose=args.verbose)
        else:
            for file in args.file:
                if args.verbose: print("Parsing", file)
                main_file.collate(LogFile.from_file(file, verbose=args.verbose, quiet=args.quiet))
    del parser
    del args

    help = _Helper()  # When you bundle everything with pyinstaller, help stops working for some reason
    colorama_init()

    # Hand pick random startup colours
    from random import choice
    colour = choice([Fore.BLUE, Fore.CYAN, Fore.GREEN, Fore.LIGHTBLUE_EX, Fore.LIGHTCYAN_EX,
                    Fore.LIGHTGREEN_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.LIGHTWHITE_EX,
                    Fore.LIGHTYELLOW_EX, Fore.MAGENTA, Fore.RED, Fore.WHITE, Fore.YELLOW])

    from IPython import embed
    embed(header=f"""{colour}
_                ______           _     _       
| |               | ___ \         | |   | |      
| |     ___   __ _| |_/ /_   _  __| | __| |_   _ 
| |    / _ \ / _` | ___ \ | | |/ _` |/ _` | | | |
| |___| (_) | (_| | |_/ / |_| | (_| | (_| | |_| |
\_____/\___/ \__, \____/ \__,_|\__,_|\__,_|\__, |
            __/ |                         __/ |
            |___/                         |___/ 
            {Fore.RESET}
Switching to interactive

Press tab to autocomplete
For {Fore.CYAN}LogBuddy{Fore.RESET} specific help type '{Fore.GREEN}help{Fore.RESET}' or '{Fore.GREEN}?{Fore.RESET}' for IPython's help (without the quotes).
""", colors="Neutral")
