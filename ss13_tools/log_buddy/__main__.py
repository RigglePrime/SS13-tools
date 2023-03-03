#!/usr/bin/env python3
# pylint: disable=import-outside-toplevel,not-callable
import inspect
import os
import sys
from typing import Any
from colorama import Fore, init as colorama_init

from _sitebuiltins import _Helper

# Log is unused, but it's here so the user doesn't have to import it manually
from ss13_tools.log_buddy.log import Log, LogType  # noqa: F401 pylint: disable=unused-import
from ss13_tools.log_buddy.log_parser import LogFile
from ss13_tools.log_buddy.constants import HELP_LINK

# Change the help text, so users can more easily understand what to do
_Helper.__repr__ = lambda self: f"""Welcome to {Fore.CYAN}LogBuddy{Fore.RESET}!
{Fore.YELLOW}Use right click to copy something, CTRL + C will terminate the program.{Fore.RESET}
{Fore.YELLOW}Tab will autocomplete, the up and down arrows will cycle through your previous commands.{Fore.RESET}

Please see the latest documentation at {Fore.BLUE}{HELP_LINK}{Fore.RESET}.
The above link should be more than enough! If you are unsure about a command,
just append or prepend it with '{Fore.GREEN}?{Fore.RESET}'.
For example: '{Fore.GREEN}%download?{Fore.RESET}' or '{Fore.GREEN}?%download{Fore.RESET}'
To get a list of all possible commands (magics), type '{Fore.GREEN}%lsmagic{Fore.RESET}'.

If you're a {Fore.CYAN}nerd{Fore.RESET} and would like to know more, type '{Fore.GREEN}help(MORE){Fore.RESET}'
"""

MORE = type("anon", (), {
    '__str__': lambda self: "What are you doing here... stop snooping around!",
    '__repr__': lambda self: str(self)  # pylint: disable=unnecessary-lambda
})()
MORE.__doc__ = f"""Welcome to help for nerds. This is copy-pasted from the old help text, and goes more in-depth.

Type '{Fore.GREEN}help(Log){Fore.RESET}' for information about the log, and '{Fore.GREEN}help(LogFile){Fore.RESET}' for
information about log files. Type '{Fore.GREEN}functions(object){Fore.RESET}' for a list of all defined functions and
'{Fore.GREEN}variables(object){Fore.RESET}' for a list of all variables. Both are currently quite bad
(I will get to it some day I promise). {Fore.CYAN}LogBuddy{Fore.RESET} performs all operations on an internal work set,
so you can chain filters (functions). To reset the work set, call '{Fore.GREEN}reset_work_set(){Fore.RESET}'
on your log instance.

If {Fore.YELLOW}-- More --{Fore.RESET} is displayed on the bottom of the screen, press {Fore.YELLOW}return (enter){Fore.RESET}
to advance one line, {Fore.YELLOW}space{Fore.RESET} to advance a screen or {Fore.YELLOW}q{Fore.RESET} to quit.
IPython (the thing you type in that displays 'In [2]:') will sometimes suggest commands. The gray part can be inserted
by simply pressing {Fore.YELLOW}→{Fore.RESET}. Clear the current line by pressing {Fore.YELLOW}CTRL + C{Fore.RESET}.
You can exit by typing '{Fore.GREEN}exit{Fore.RESET}' or pressing {Fore.YELLOW}CTRL + D{Fore.RESET}.

For Python's interactive help, type '{Fore.GREEN}help(){Fore.RESET}', or '{Fore.GREEN}help(object){Fore.RESET}' for help
about object (for example: '{Fore.GREEN}help(LogFile){Fore.RESET}').
"""


def functions(cls: object) -> list[tuple[str, Any]]:
    """Returns all methods of an object"""
    return inspect.getmembers(cls, predicate=inspect.ismethod)


def variables(cls: object) -> dict[str, Any]:
    """Returns all variables of an object"""
    return cls.__dict__


def main():
    """Main"""
    print("LogBuddy starting...")

    logs = LogFile()

    if len(sys.argv) > 1:
        if len(sys.argv) == 2 and os.path.isdir(sys.argv[1]):
            logs.collate(LogFile.from_folder(sys.argv[1]))
        else:
            for file in sys.argv[1:]:
                logs.collate(LogFile.from_file(file))

    # When you bundle everything with pyinstaller, help stops working for some reason
    help = _Helper()  # noqa: F841 pylint: disable=unused-variable,redefined-builtin
    colorama_init()

    # Hand pick random startup colours
    from random import choice
    colour = choice([Fore.BLUE, Fore.CYAN, Fore.GREEN, Fore.LIGHTBLUE_EX, Fore.LIGHTCYAN_EX,
                    Fore.LIGHTGREEN_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.LIGHTWHITE_EX,
                    Fore.LIGHTYELLOW_EX, Fore.MAGENTA, Fore.RED, Fore.WHITE, Fore.YELLOW])

    from IPython.terminal.embed import InteractiveShellEmbed
    # from IPython.paths import get_ipython_dir

    # Get instance
    shell = InteractiveShellEmbed.instance()

    # Load default config (some day we will actually load it)
    # profile_dir = os.path.join(get_ipython_dir(), 'profile_default')
    # shell.config_file_paths.append(profile_dir)
    # shell.load_config_file()

    # Gets magics
    from ss13_tools.log_buddy.log_magics import LogMagics, register_aliases
    shell.register_magics(LogMagics)
    register_aliases(shell)

    # Cleanup
    del LogMagics, InteractiveShellEmbed, choice  # , get_ipython_dir

    shell(header=f"""{colour}
 _                 _____           _     _
| |               | ___ \\         | |   | |
| |     ___   __ _| |_/ /_   _  __| | __| |_   _
| |    / _ \\ / _` | ___ \\ | | |/ _` |/ _` | | | |
| |___| (_) | (_| | |_/ / |_| | (_| | (_| | |_| |
\\_____/\\___/ \\__, \\____/ \\__,_|\\__,_|\\__,_|\\__, |
            __/  |                         __/ /
            |___/                         |___/
            {Fore.RESET}
Switching to interactive

Press tab to autocomplete
For {Fore.CYAN}LogBuddy{Fore.RESET} specific help type '{Fore.GREEN}help{Fore.RESET}' or '{Fore.GREEN}?{Fore.RESET}'
for IPython's help (without the quotes).
""", colors="Neutral")


if __name__ == "__main__":
    main()
