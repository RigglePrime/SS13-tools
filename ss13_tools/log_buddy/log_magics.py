"""Defines our special log magics so people can use short commands"""
# pylint: disable=unused-argument
import re
import os
from functools import wraps

from IPython.core.page import page
from IPython.terminal.magics import Magics, magics_class, line_magic
from IPython.core.error import UsageError, StdinNotImplementedError
from pyperclip import copy

from ..byond import canonicalize
from .log_parser import LogFile, SHAMELESS
from .log import LogType


LOGS_VARIABLE_NAME = 'logs'


# For info on pasting see IPython.terminal.magics.TerminalMagics.paste
@magics_class
class LogMagics(Magics):
    """Stores our custom log magics for ease of use"""

    def _undoable(func):  # pylint: disable=no-self-argument
        """Marks a function as being able to be undone. Apply to magics that modify the logs"""
        @wraps(func)
        def decorator_undoable(self, arg):
            """You should not be seeing this"""
            func(self, arg)  # pylint: disable=not-callable
            self.actions.append((func.__name__, arg))  # pylint: disable=no-member
        return decorator_undoable

    @property
    def logs_var(self) -> LogFile:
        """Stores the logs (main LogFile) variable"""
        return self.shell.user_ns[LOGS_VARIABLE_NAME]

    @logs_var.setter
    def logs_var(self, new_value) -> None:
        self.shell.user_ns[LOGS_VARIABLE_NAME] = new_value

    @line_magic
    def download(self, parameter_s=''):
        """Downloads logs from a round ID (or ckey) and stores it in `logs`

        - Options:
            - c: force the program to interpret your input as a ckey
            - p: only get the round the person played in? (applies only for ckeys)
            - r: the amount of rounds to download (applies only for ckeys)
            - f: pre-emptively delete all logs without our target ckey (applies only for ckeys)
        - `%download 198563`: download round 198563
        - `%dl 198563`: same as above
        - `%download 199563-199999`: download rounds 199500 to 199600 (inclusive). Be careful with this,
        as downloading and loading more than 100 rounds may slow down your computer by a lot.
        - `%download 198563 198565 198569 198570`: download rounds 198563, 198565, 198569 and 198570.
        You can run this command with as many rounds as you want.
        - `%download -p coolckey123` downloads 50 (default) rounds that `coolckey123` played in
        - `%download -r10 coolckey123` downloads 10 rounds that `coolckey123` played in
        - `%download -c 123123123` this option is useful, as `dl` would interpret numbers as a round ID.
        `-c` forces it to interpret it as a ckey
        - `%download -c -r=10 123123123` you can have more than one switch! The `=` is optional
        - `%download -cr=10 123123123` you can group options like this! The `=` is optional. Just remember
        to have the number right next to the character (r). Doing `-rc10` would assign 10 to c (error)
        """
        if not parameter_s:
            raise UsageError(f"No arguments! Usage:\n{self.download.__doc__}")
        opts, args = self.parse_options(parameter_s, 'cpr:f')
        if 'c' not in opts and '-' in args:
            args = args.split('-')
            if len(args) != 2:
                raise UsageError("I don't know what to do with this, please try again")
            try:
                first, last = (int(x) for x in args)
            except ValueError as ex:
                raise UsageError("One of these is not a number, try again") from ex
            self.logs_var = LogFile.from_round_range(first, last)
            return
        if 'c' not in opts and ' ' in args or ',' in args:
            # Split with spaces and commas
            args = re.split(r'[, ]', args)
            try:
                # Prase ints and get rid of empty strings
                round_ids = tuple(int(x) for x in args if x)
            except ValueError as ex:
                raise UsageError("One of those is not a number, please try again") from ex
            self.logs_var = LogFile.from_round_collection(*round_ids)
            return
        if 'c' not in opts and args.isnumeric():
            self.logs_var = LogFile.from_round_id(int(args))
        else:
            rounds = int(opts['r'].lstrip('=')) if 'r' in opts else 50
            filter_logs = 'f' in opts
            only_played = 'p' in opts
            args = canonicalize(args)
            self.logs_var = LogFile.from_ckey(args, rounds=rounds, only_played=only_played, filter_logs=filter_logs)

    @line_magic
    def length(self, parameter_s=''):
        """Prints how many logs we have"""
        print("Current number of logs is", len(self.logs_var))

    @line_magic
    def sort(self, parameter_s=''):
        """Sorts our logs"""
        self.logs_var.sort()
        print("Logs sorted!")

    @_undoable
    @line_magic
    def search_ckey(self, parameter_s=''):
        """Excludes logs that do not contain any of the ckeys

        Example:
           - `%ckey WindowSmasher86`
           - `%search_ckey ckey1 ckey2 ...`
        """
        if not parameter_s:
            raise UsageError(f"Add some ckeys! Usage:\n{self.search_ckey.__doc__}")
        parameter_s = tuple(canonicalize(x) for x in re.split(r'[, ]', parameter_s) if x)
        print("Looking for", ', '.join(parameter_s))
        for ckey in parameter_s:
            if ckey not in self.logs_var.who:
                print(f"{ckey} not found! Ignoring!")
        self.logs_var.filter_ckeys(*parameter_s, source_only=False)

    @_undoable
    @line_magic
    def search_string(self, parameter_s=''):
        """Works just like bookmarking in Notepad++, or CTRL+F multiple times. Case insensitive

        Options:
            - a: append mode. Take from the unfiltered logs and append the results to the current work set
            - c: case sensitive mode
            - r: raw mode. Do not parse any strings, ignore quotation marks

        Example:
            - `%string 'help maint'`
            - `%string -r help maint`
            - `%string security`
            - `%string 'thank you very much!'`
            - `%string -a 'string to add'`: instead of filtering the current filtered logs, append the results (union)
                - Running these would produce the same result: `%string string1 string2` or
                `%string string1`, `%string -a string2`
            - `%string -c 'Case Sensitive'`: enable case sensitive mode
            - `%string -ar Case Sensitive`: same as above (you can group options)
        """
        if not parameter_s:
            raise UsageError("No string to search for!")
        opts, args = self.parse_options(parameter_s.replace('\\"', '\\\\"').replace('"', '"""'), 'acr')
        additive = 'a' in opts
        case_s = 'c' in opts
        if 'r' in opts:
            self.logs_var.filter_strings(args, case_sensitive=case_s, additive=additive)
            return
        args = parse_quoted_string(args)
        print("Searching for strings", ', '.join(args))
        print("Append is", "ON," if additive else "OFF,", "case sensitive mode is",
              "ON" if case_s else "OFF,", "and raw mode is", "ON" if additive else "OFF")
        self.logs_var.filter_strings(*args, case_sensitive=case_s, additive=additive)

    @_undoable
    @line_magic
    def heard(self, parameter_s=''):
        """Gets only what the people could have heard (conversation but it's a union)

        Example:
            - `%heard WindowSmasher86`
            - `%heard ckey1, ckey2`
        """
        if not parameter_s:
            raise UsageError(f"Add some ckeys! Usage:\n{self.heard.__doc__}")
        parameter_s = tuple(canonicalize(x) for x in re.split(r'[, ]', parameter_s) if x)
        print("Looking for", ', '.join(parameter_s))
        for ckey in parameter_s:
            if ckey not in self.logs_var.who:
                print(f"{ckey} not found! Ignoring!")
        self.logs_var.filter_heard(*parameter_s)

    @_undoable
    @line_magic
    def conversation(self, parameter_s=''):
        """Tries to reconstruct a conversation between parties (like heard but an intersection instead)

        Example:
            - `%conversation ckey`
            - `%conversation ckey1 ckey2`
        """
        if not parameter_s:
            print(f"Add some ckeys! Usage:\n{self.conversation.__doc__}")
            return
        parameter_s = tuple(canonicalize(x) for x in re.split(r'[, ]', parameter_s) if x)
        print("Filtering conversation on ckeys", ', '.join(parameter_s))
        for ckey in parameter_s:
            if ckey not in self.logs_var.who:
                print(f"{ckey} not found! Ignoring!")
        self.logs_var.filter_conversation(*parameter_s)

    @line_magic
    def who(self, parameter_s=''):
        """List all ckeys present in the round

        Example:
            - `%who`
        """
        print(self.logs_var.who)

    @line_magic
    def list_locations(self, parameter_s=''):
        """Gets all of the different locations in our current working set

        Example:
            - `%list_locations`
        """
        print({x.location_name for x in self.logs_var.logs})

    @line_magic
    def reset(self, parameter_s=''):
        """Resets the work set"""
        self.logs_var.reset_work_set()
        self.actions.clear()
        print("Filters reset!")

    @_undoable
    @line_magic
    def location(self, parameter_s=''):
        """Filters by location name.

        Options:
            - e: filter for exact name

        Example:
            - %location Medbay
            - %location -e Medbay Central
        """
        if not parameter_s:
            raise UsageError(f"Add a location! Usage:\n{self.location.__doc__}")
        opts, args = self.parse_options(parameter_s, 'e')
        print("Filtering for", parameter_s)
        self.logs_var.filter_by_location_name(args, exact='e' in opts)

    @_undoable
    @line_magic
    def radius(self, parameter_s=''):
        """Tries to reconstruct a conversation between parties

        Example:
            - %radius x y z radius
            - %radius 50 62 2 8
        """
        parameter_s = parameter_s.split(' ')
        if len(parameter_s) != 4:
            print(f"Add some arguments! Usage:\n{self.radius.__doc__}")
            return
        try:
            x, y, z, radius = (int(x) for x in parameter_s)  # pylint: disable=invalid-name
        except ValueError as ex:
            raise UsageError("Could not convert to an integer") from ex
        print(f"Filtering by x={x}, y={y}, z={z}, r={radius}")
        self.logs_var.filter_by_radius((x, y, z), radius)

    @_undoable
    @line_magic
    def type(self, parameter_s=''):
        """Filters by log type"""
        if not parameter_s:
            raise UsageError("No log types!")
        exclude = set(LogType.parse_log_type(x[1:].strip()) for x in re.split(r'[, ]', parameter_s) if x and x[0] == '!')
        include = set(LogType.parse_log_type(x.strip()) for x in re.split(r'[, ]', parameter_s) if x and x[0] != '!')
        if LogType.UNKNOWN in include | exclude:
            print("Unrecognised log type. Available types:")
            print(LogType.list())
            print(f"Example include: %{self.type.__name__} GAME ATTACK")
            print(f"Example exclude: %{self.type.__name__} !SILICON")
            return
        print("Filtering by the following rules:")
        print("Including:", ', '.join(str(x) for x in include))
        print("Excluding:", ', '.join(str(x) for x in exclude))
        self.logs_var.filter_by_type(include=include, exclude=exclude)

    @line_magic
    def print_logs(self, parameter_s=''):
        """Prints our filtered logs"""
        if len(self.logs_var.logs) > 200:
            page("Too many logs, opening pager. Press q to quit, enter to advance one line, space to advance a screen\n" +
                 '\n'.join(log.pretty() for log in self.logs_var.logs) + '\n')
        else:
            self.logs_var.print_working()

    @line_magic
    def head(self, parameter_s=''):
        """Prints our filtered logs, but only the head"""
        try:
            self.logs_var.head(int(parameter_s))
        except ValueError:
            self.logs_var.head()

    @line_magic
    def tail(self, parameter_s=''):
        """Prints our filtered logs, but only the tail"""
        try:
            self.logs_var.tail(int(parameter_s))
        except ValueError:
            self.logs_var.tail()

    @line_magic
    def clear(self, parameter_s=''):
        """Clears the logs, freeing memory"""
        try:
            response = self.shell.ask_yes_no("Are you sure you want to remove all logs? [y/N]", default='n')
        except StdinNotImplementedError:
            print("Logs will not be removed.")
            return
        if not response:
            print("Cancelled")
            return
        self.logs_var = LogFile()
        self.actions.clear()
        print("Logs cleared!")

    @line_magic
    def save_logs(self, parameter_s=''):
        """Saves the working set to a file"""
        if not parameter_s:
            parameter_s = "logs.log"
        print(f"Writing to file {parameter_s}")
        self.logs_var.write_working_to_file(parameter_s)

    @line_magic
    def load_logs(self, parameter_s=''):
        """Opens the file and adds all logs to our current collection"""
        if not parameter_s:
            print("Enter a file name!")
        if not os.path.exists(parameter_s):
            raise UsageError("File does not exist")
        print("Loading from", parameter_s)
        self.logs_var.collate(LogFile.from_file(parameter_s))

    actions = []

    @line_magic
    def undo(self, parameter_s=''):
        """Undo an action! Provide a number to undo multiple times"""
        if not self.actions:
            print("Nothing to undo!")
            return
        if parameter_s and not parameter_s.isnumeric():
            raise UsageError("That's not a number! Run it without one, or provide a number please")
        undo_times = int(parameter_s) if parameter_s else 1
        if undo_times < 1:
            raise UsageError("What the hell? I can't undo less than 1 time...")
        if len(self.actions) < undo_times:
            raise UsageError("Cannot undo that many times!")
        actions = self.actions.copy()[:-undo_times]

        print("Rewinding...")
        self.logs_var.reset_work_set()
        for magic, params in actions:
            print(f"Running %{magic} with params: {params}")
            self.shell.run_line_magic(magic, params)
        self.actions.clear()
        self.actions = actions
        print("Restored")

    @line_magic
    def clip(self, parameter_s=''):
        """Copy the current filtered logs to your clipboard"""
        copy('\n'.join(log.raw_line for log in self.logs_var.logs) + '\n\n' + SHAMELESS)
        print("Copied to clipboard!")


def register_aliases(shell):
    """Adds shorthands for all magics"""
    aliases = [
        ('dl', LogMagics.download.__name__),
        ('l', LogMagics.length.__name__),
        ('ckey', LogMagics.search_ckey.__name__),
        ('string', LogMagics.search_string.__name__),
        ('loc', LogMagics.location.__name__),
        ('s', LogMagics.save_logs.__name__),
        ('p', LogMagics.print_logs.__name__),
    ]
    for alias, magic in aliases:
        shell.magics_manager.register_alias(alias, magic, 'line')


def parse_quoted_string(string: str, sep: str = ' ') -> list[str]:
    """Returns a list of strings, separated by a whitespace"""
    quotes = """"'"""  # Very confusing :)
    sep_len = len(sep)
    cur_quote = None
    cur_marker = 0
    assert sep not in quotes
    length = len(string)
    ret = []
    i = -1  # We need i to start at 0 in the loop
    while (i := i + 1) < length:
        if string[i] == "\\":
            # This next line shortens our string by 1, so no need to increment
            string = string.replace("\\", "", 1)
            length -= 1
            continue
        if not cur_quote and string.startswith(sep, i):
            if cur_marker == i:
                cur_marker = i + 1
                continue
            ret.append(string[cur_marker:i])
            # Set the current marker at the beginning of the next string, and
            # i to the last (since it will get +1'd)
            cur_marker = (i := i + sep_len - 1) + 1  # I LOVE the walrus operator
            continue
        if string[i] not in quotes:
            continue
        if not cur_quote:  # Are we in a quoted string?
            if cur_marker != i:
                ret.append(string[cur_marker:i])
            cur_quote = quotes[quotes.index(string[i])]
            cur_marker = i + 1
            continue
        if cur_quote != string[i]:  # Wrong quote, ignore
            continue
        cur_quote = None
        ret.append(string[cur_marker:i])  # Got one!
        cur_marker = i + 1
    if cur_marker < i:  # Check if there's anything left
        ret.append(string[cur_marker:])
    return ret
