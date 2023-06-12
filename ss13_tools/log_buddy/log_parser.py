#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
from enum import Enum
import traceback
from typing import Annotated, Iterable, Union, Literal
from html import unescape as html_unescape
from itertools import repeat, chain

from tqdm import tqdm

from .log import Log, LogType
from .constants import ALL_LOGS_WE_PARSE, ERRORED_FILE, SHAMELESS
from ..__version__ import __version__
from ..log_downloader import RoundLogDownloader, RoundListLogDownloader, CkeyLogDownloader
from ..scrubby import get_round_source_url


HEARING_RANGE = 9


class NotSortableException(Exception):
    """Hey, I can't sort this!"""


class InvalidType(Exception):
    """What kind of type is this..."""


class UnsupportedLogTypeException(Exception):
    """Strange log type you have there"""


class LogParserException(Exception):
    """Strange log type you have there"""


class LogFileType(Enum):
    """Enum of possible log file types"""
    UNKNOWN = 0
    COLLATED = 1
    GAME = 2
    ATTACK = 3
    PDA = 4
    SILICON = 5
    MECHA = 6
    VIRUS = 7
    TELECOMMS = 8
    UPLINK = 9
    SHUTTLE = 10
    TGUI = 11

    @staticmethod
    def parse_log_file_type(string: str):
        """Tries to parse a log type from a string"""
        try:
            return LogFileType[string.upper()]
        except KeyError:
            return LogFileType.UNKNOWN

    @staticmethod
    def list():
        """Returns all possible log file types"""
        return list(LogFileType)


class LogFile:
    """An object representing a log file. Most functions use `self.work_set`, original logs sorted in `self.logs`.

    Parameters:
    `logs` (list[str]): list of log lines
    `type` (LogFileType): type of the log file
    `verbose` (bool): toggles verbose mode
    `quiet` (bool): toggles quiet mode

    Examples:

    `log_file = LogFile()` # Empty log file, useful for combining more later using `collate`,

    `log_file = LogFile(open("game.log"), LogFileType.UNKNOWN)`,

    `log_file = LogFile(["logline 1", "log line 2", "log line 3"])\
    # NOTE: must be a valid log or the parser will raise an exception`
    """
    round_id: Annotated[int, "Stores the round ID. If unknown, it will equal -1"]
    unfiltered_logs: Annotated[list[Log], "Stores a list of all logs"]
    logs: Annotated[list[Log], "Stores a list of filtered logs"]
    who: Annotated[list[str], "Stores a list of all connected ckeys"]
    sortable: bool
    log_source: Annotated[str, "Source of the logs (if available)"]

    def __init__(self, logs: Iterable[str] = None, log_type: LogFileType = LogFileType.UNKNOWN,
                 verbose: bool = False, quiet: bool = False) -> None:
        if verbose and quiet:
            print("Really? You want me to be silent and verbose? Those are mutually exclusive you know")
        self.round_id = -1
        self.unfiltered_logs = []
        self.logs = []
        self.who = []
        self.sortable = True
        self.log_type = log_type
        self.log_source = None

        if not logs:
            return

        self.__parse_logs(logs, verbose=verbose, quiet=quiet)
        self.unfiltered_logs.sort(key=lambda log: log.time)
        self.logs = self.unfiltered_logs

    def __parse_logs(self, logs: Iterable[str], verbose: bool = False, quiet: bool = False):
        errored = []
        pbar = tqdm(logs)
        for line in pbar:
            line = line.strip()
            if not line or line == "- -------------------------" or line == '-' \
                    or "] Starting up round ID " in line or line.startswith("##"):
                continue
            try:
                self.__parse_one_line(line)
            except Exception as exception:  # pylint: disable=broad-exception-caught
                errored.append(line)
                pbar.clear()
                if not quiet:
                    print(f"Could not be parsed: '{line}', with the reason:", exception)
                if verbose:
                    traceback.print_exc()
                pbar.display()
        if errored:
            with open(ERRORED_FILE, 'a+', encoding="utf-8") as file:
                file.write("## If you see this, please share it with Riggle.\n")
                file.write("## ")
                file.write(__version__)
                file.write("\n\n")
                file.writelines(chain.from_iterable(zip(errored, repeat("\n"))))

    def __parse_one_line(self, line: str):
        if line.startswith("-censored"):
            return  # Skip censored lines

        # VOTE is split into multiple lines, so account for that
        if line.startswith("- <b>") and self.unfiltered_logs and self.unfiltered_logs[-1].log_type == LogType.VOTE:
            self.unfiltered_logs[-1].text += ", " + html_unescape(line.replace("- <b>", "").replace("</b>", ""))
            return

        # Priority announcements (and others like it) sometimes do this
        if line.startswith("- ") and self.unfiltered_logs:
            # Don't actually insert a new line
            line = self.unfiltered_logs[-1].raw_line + "\\n" + line.replace("- ", "")
            # Remove the incomplete entry (so we can parse location too!)
            self.unfiltered_logs.pop()
        log = Log(line)
        self.unfiltered_logs.append(log)
        if log.agent and log.agent.ckey and log.agent.ckey not in self.who:
            self.who.append(log.agent.ckey)

    def add_log(self, log: Log, reset_workset: bool = True, sort: bool = True) -> None:
        """Appends a log entry to the end.

        Parameters:
        `log` (Log): the Log object to be added
        `reset_workset` (bool): if we should also reset the working set
        `sort` (bool): if we should also sort the logs afterwards

        NOTE: the log variable MUST be of type Log

        Returns None
        """
        if not isinstance(log, Log):
            raise InvalidType(f"Type Log required but type {str(type(log))} was found")
        self.unfiltered_logs.append(log)
        if reset_workset:
            self.reset_work_set()
        if sort:
            self.sort()

    def add_logs(self, logs: list[Log], reset_workset: bool = True, sort: bool = True) -> None:
        """Appends a list of log entries to the end.

        Parameters:
        logs (list[Log]): the Log objects list to be added
        `reset_workset` (bool): if we should also reset the working set
        `sort` (bool): if we should also sort the logs afterwards

        Returns None
        """
        self.unfiltered_logs.extend(logs)
        if reset_workset:
            self.reset_work_set()
        if sort:
            self.sort()

    def sort(self) -> None:
        """Sorts the current work set, using the time at which the log was added, descending

        Example call: `my_logs.sort()`

        Returns None"""
        if not self.sortable:
            raise NotSortableException("Not enough information to sort the logs")
        self.logs.sort(key=lambda log: log.time)

    def collate(self, logfile: LogFile) -> None:
        """Collates (extends, adds together) two LogFile objects and changes the LogFileType to COLLATED.
        The result is stored in the the object this was called on. A call to this function will reset the
        current work set.

        Parameters:
        `logfile` (LogFile): the LogFile object you want to combine

        Example:
        `my_logs = LogFile()`
        `my_logs.collate(LogFile.from_file("game.txt"))`
        `my_logs.collate(LogFile.from_file("attack.txt"))`

        Returns `None`
        """
        self.add_logs(logfile.unfiltered_logs, sort=True)
        self.log_type = LogFileType.COLLATED
        self.who.extend(logfile.who)
        self.who = list(set(self.who))  # Remove duplicates
        self.who.sort()
        self.logs = self.unfiltered_logs

    def filter_ckeys(self, *ckeys: str, source_only: bool = False) -> None:
        """Removes all logs in which the specified ckeys are not present, saving the result
        in self.work_set. Works much like Notepad++, but only counts the agent (actor, the
        one who performed the action). See `filter_strings` for a function like Notepad++ bookmark

        Parameters:
        `ckeys` (tuple[str, ...]): ckeys to filter

        Example call: `my_logs.filter_ckeys("ckey1", "ckey2")` (as many or little ckeys as you want)

        Returns `None`"""
        filtered = []
        ckeys = [x.casefold() for x in ckeys]
        for log in self.logs:
            if (log.agent and log.agent.ckey and log.agent.ckey.casefold() in ckeys) or \
               (not source_only and log.patient and log.patient.ckey and log.patient.ckey.casefold() in ckeys):
                filtered.append(log)
        if not filtered:
            print("Operation completed with empty set. Aborting.")
            return
        self.logs = filtered

    def filter_strings(self, *strings: str, case_sensitive: bool = False, additive: bool = False) -> None:
        """Removes all logs in which the specified strings are not present, saving them in
        `self.work_set`. Works exactly like Notepad++ bookmark

        Parameters:
        `strings` (tuple[str, ...]): strings to filter
        `case_sensitive` (bool): toggles case sensitivity

        Example calls: `my_logs.filter_strings("Hi!")`
        `my_logs.filter_strings("attacked", "injected", "I hate you")`
        `my_logs.filter_strings("racial slur", case_sensitive=True)` (as many strings as you want)

        Returns `None`"""
        filtered = []
        logs_it = self.unfiltered_logs if additive else self.logs
        for log in logs_it:
            raw_line = log.raw_line
            if not case_sensitive:
                raw_line = raw_line.casefold()
            for string in strings:
                if not case_sensitive:
                    string = string.casefold()
                if string in raw_line:
                    filtered.append(log)
                break
        if not filtered:
            print("Operation completed with empty set. Aborting.")
            return
        if additive:
            self.logs.extend(filtered)
            self.logs = list(set(self.logs))  # Make sure they're unique
            self.sort()
        else:
            self.logs = filtered

    def filter_strings_case_sensitive(self, *strings: str) -> None:
        """Shorter for `filter_strings(*strings, case_sensitive = True)`"""
        self.filter_strings(*strings, case_sensitive=True)

    def filter_heard(self, *ckeys: str, walking_error: int = 4) -> None:
        """Removes all log entries which could not have been heard by the specified ckey(s)
        (very much in alpha) and stores the remaining lines in `self.work_set`

        Parameters:
        `ckeys` (tuple[str, ...]): desired ckey(s)
        `walking_error` (int): added to hearing range to account for the lack of logs

        Example call: `my_logs.filter_heard("ckey")`

        Returns `None`"""
        final = set()
        for ckey in ckeys:
            final.update(self._get_only_heard(ckey, walking_error=walking_error))
        self.logs = list(final)
        self.sort()

    def filter_conversation(self, *ckeys: str, walking_error: int = 4) -> None:
        """Tries to get a conversation between multiple parties, excluding what they would and would not hear as a group.
        Saves the result in `self.work_set`

        Parameters:
        `ckeys` (tuple[str, ...]): ckeys to use for sorting
        `walking_error` (int): added to hearing range to account for the lack of logs

        Example call: `my_logs.filter_conversation("ckey1", "ckey2", "ckey3")` (as many or little ckeys as you want)

        Returns None"""
        self.filter_ckeys(*ckeys, source_only=False)
        final = self._get_only_heard(ckeys[0], walking_error=walking_error)
        for ckey in ckeys[1:]:
            final.intersection_update(self._get_only_heard(ckey, walking_error=walking_error))

        if not final:
            print("Operation completed with empty set. Aborting.")
            return
        self.logs = list(final)
        self.sort()

    def reset_work_set(self):
        """Removes all filters; sets the working set to be equal to all logs

        Example call: my_logs.reset_work_set()"""
        self.logs = self.unfiltered_logs

    def _get_only_heard(self, ckey: str, logs_we_care_about: Union[list[LogType],
                        Literal["ALL"]] = "ALL", walking_error: int = 4) -> set[Log]:
        """Removes all log entries which could not have been heard by the specified ckey (very much in alpha).
        Uses logs from `self.work_set`

        Parameters:
        `ckey` (str): ckeys to use
        `logs_we_care_about` (list[LogType])
        `walking_error` (int): added to hearing range to account for the lack of logs

        Example calls: `my_logs.get_only_heard("ckey")`
        `my_logs.get_only_heard("ckey", "ALL")`
        `my_logs.get_only_heard("ckey", [LogType.SAY, LogType.WHISPER])`

        Returns `set[Log]`"""
        self.sort()
        # Adjust for error created by lack of logs
        hearing_range = HEARING_RANGE + walking_error
        filtered = set()
        cur_loc = (0, 0, 0)
        last_loc = cur_loc
        # Iterate through unfiltered logs to actually get the data we want
        for log in self.unfiltered_logs:
            # Check for ckey. If our target was included in the action we can safely assume they saw it
            if (log.agent and ckey == log.agent.ckey) or\
               (log.patient and ckey == log.patient.ckey) or\
               (log.text and f"{ckey}/(" in log.text):
                # If there's a location attached, update it
                if log.location:
                    last_loc = cur_loc
                    cur_loc = log.location
                filtered.add(log)
                continue
            # If our target didn't participate, we need to check how far away it happened

            # Check z-level, if they differ save location and continue
            if cur_loc[2] != last_loc[2]:
                continue
            # Filter logs that we don't care about but still use their location
            if logs_we_care_about and (logs_we_care_about != "ALL"):
                continue
            if isinstance(logs_we_care_about, list) and log.log_type not in logs_we_care_about:
                continue
            # Skip logs with no location data available
            if not log.location:
                continue
            # Calculate distance
            # if sqrt(pow(cur_loc[0] - log.location[0], 2) + pow(cur_loc[1] - log.location[1], 2)) - hearing_range < 0:
            if abs(cur_loc[0] - log.location[0]) - hearing_range < 0 and abs(cur_loc[1] - log.location[1]) - hearing_range < 0:
                filtered.add(log)
            # You (almost) always hear tcomms
            elif log.log_type == LogType.TCOMMS:
                filtered.add(log)

        # Intersect with currently filtered logs so we don't reset filters
        return filtered & set(self.logs)

    def filter_by_location_name(self, location_name: str, exact: bool = False) -> None:
        """Removes all logs that did not happen in the specified location,
        and stores the result in the work set.

        Parameters:
        `location_name` (str): the name of the location, case insensitive
        `exact` (bool): should the strings exactly match, or just contain?

        Example call: my_logs.filter_by_location_name("Bar")

        Returns `None`"""
        filtered = []
        location_name = location_name.casefold()
        for log in self.logs:
            if not log.location_name:
                continue
            if (not exact and location_name in log.location_name.casefold()) or \
               (location_name == log.location_name.casefold()):
                filtered.append(log)
        if not filtered:
            print("Operation completed with empty set. Aborting.")
            return
        self.logs = filtered

    def filter_by_radius(self, location: tuple[int, int, int], radius: int, exclude_locationless: bool = True) -> None:
        """Removes all logs that did not happen in the specified radius around the location,
        and stores the result in the work set.

        Parameters:
        `location` (tuple[int, int, int]): the location
        `radius` (int): the radius

        Example call: `my_logs.filter_by_radius((32, 41, 2), 5)`

        Returns None"""
        filtered = []
        for log in self.logs:
            if not log.location:
                if not exclude_locationless:
                    filtered.append(log)
                continue
            # Z level must match
            if log.location[2] != location[2]:
                continue
            if abs(location[0] - log.location[0]) - radius < 0 and abs(location[1] - log.location[1]) - radius < 0:
                filtered.append(log)
        if not filtered:
            print("Operation completed with empty set. Aborting.")
            return
        self.logs = filtered

    def filter_by_type(self, include: Iterable[LogType] = None, exclude: Iterable[LogType] = None):
        """Only keeps (or removes) logs lines of the specified type.

        Parameters:
        `include` (tuple[LogType]): log types to include
        `exclude` (tuple[LogType]): log types to exclude

        If the same type is seen in include and exclude, it will be excluded.
        To get a list of all available LogTypes call `LogType.list()`

        Example calls:
        `my_logs.filter_by_type((LogType.OOC,))` (the first argument counts as include)
        `my_logs.filter_by_type(include=(LogType.SAY,))`
        `my_logs.filter_by_type(exclude=(LogType.TCOMMS,))`
        """

        if include:
            filter_for = set(LogType) & set(include)
        else:
            filter_for = set(LogType) - set(exclude)
        if not filter_for:
            print("Nothing to filter for!")
            return
        filtered = []
        for log in self.logs:
            if log.log_type in filter_for:
                filtered.append(log)
        if not filtered:
            print("Operation completed with empty set. Aborting.")
            return
        self.logs = filtered

    def print_working(self) -> None:
        """Prints working set to the console

        Example call: `my_logs.print_working()`

        Returns `None`"""
        if not self.logs:
            print("Working set empty")
            return
        for log in self.logs:
            print(log.pretty())

    def head(self, number: int = 10) -> None:
        """Prints the first few lines of the working set to the console.

        Parameters:
        `n` (int): number to print, defaults to 10

        Example call: `my_logs.head()`

        Returns `None`"""
        if not self.logs:
            print("Working set empty")
            return
        for log in self.logs[:number]:
            print(log.pretty())

    def tail(self, number: int = 10) -> None:
        """Prints the last few lines of the working set to the console.

        Parameters:
        `n` (int): number to print, defaults to 10

        Example call: `my_logs.tail()`

        Returns `None`"""
        if not self.logs:
            print("Working set empty")
            return
        for log in self.logs[-number:]:
            print(log.pretty())

    def write_working_to_file(self, filename: str, force_overwrite: bool = False) -> None:
        """Writes current `self.work_set` to the desired file.

        Parameters:
        `filename` (str): name of the file to write to (overwrites everything)

        Example call: `my_logs.write_working_to_file("logs.txt")`

        Returns None"""
        if not force_overwrite and os.path.exists(filename):
            print("Seems like there's already a file at that location! Overwrite? [y/N] ", end='')
            if input().strip().lower() != 'y':
                print("Nothing was saved.")
                return
            print("Okay then, overwriting")
        with open(filename, "w", encoding="utf-8") as file:
            for log in self.logs:
                file.write(str(log) + "\n")
            file.write(SHAMELESS)
            if self.log_source:
                file.write(f"## Logs acquired from {self.log_source}")

    def __len__(self) -> int:
        """Returns the length of the logs array"""
        return self.logs.__len__()

    def __getitem__(self, key):
        """Access logs like an array, delegates to the underlying logs list"""
        return self.logs.__getitem__(key)

    @staticmethod
    def from_file(filename: str, log_type: LogFileType = None, verbose: bool = False, quiet: bool = False) -> LogFile:
        """Parses the specified log file

        Parameters:
        `filename` (str): name (and location) of the desired file
        `type` (LogFileType): type of the log. Use if you want to override log type detection
        (optional, defaults to LogFileType.UNKNOWN)
        `verbose` (bool): toggle verbose mode (False by default)
        `quiet` (bool): toggle quiet mode (False by default)

        Example call: `my_logs = LogFile.from_file("game.txt")`

        Returns LogFile"""
        if filename.endswith(".html"):
            raise UnsupportedLogTypeException(f"{filename} does not seem to be supported")
        if not log_type and "." in filename:
            log_type = LogFileType.parse_log_file_type(filename.split(".", 1)[0])
        with open(filename, "r", encoding="utf-8") as file:
            return LogFile(file, log_type, verbose, quiet)

    @staticmethod
    def from_folder(folder: str, verbose: bool = False, quiet: bool = False) -> LogFile:
        """Parses all log files in a folder, combining them into a single file

        Parameters:
        `filename` (str): name (and location) of the desired folder
        `verbose` (bool): toggle verbose mode (False by default)
        `quiet` (bool): toggle quiet mode (False by default)

        Example call: `my_logs = LogFile.from_file("game.txt")`

        Returns `LogFile`"""
        if not os.path.isdir(folder):
            raise FileNotFoundError("Is not a folder")
        folder = folder.replace("\\", "/")
        if folder[-1] != "/":
            folder += "/"
        log_collection = LogFile()
        for file in os.listdir(folder):
            if not quiet:
                print("Parsing", file)
            try:
                log_collection.collate(LogFile.from_file(folder + file, verbose=verbose, quiet=quiet))
            except UnsupportedLogTypeException:
                if not quiet:
                    print(f"{file} isn't supported, skipping")
                continue
        return log_collection

    @staticmethod
    def from_round_id(round_id: int, logs_we_care_about: list[str] = None) -> LogFile:
        """Downloads multiple files from a round ID.

        Parameters:
        `round_id` (int): round to download
        `logs_we_care_about` (list[str]): list of strings, containing the file names.
        For example: `["game.txt", "attack.txt"]`. This defaults to all supported files.

        Example call: `my_logs = LogFile.from_round_id(185556)`

        Returns `LogFile`"""
        # Should be all supported log types as a default. Don't forget to update this list! (you will)
        if not logs_we_care_about:
            logs_we_care_about = ALL_LOGS_WE_PARSE.copy()

        downloader = RoundLogDownloader(round_id, round_id, f"{round_id}.log")
        downloader.output_only_log_line = True
        downloader.files = logs_we_care_about
        downloader.try_authenticate_interactive()
        asyncio.run(downloader.process_and_write())
        log_collection = LogFile.from_file(downloader.output_path)
        log_collection.log_type = LogFileType.COLLATED
        # Sort the logs
        log_collection.log_source = get_round_source_url(round_id=round_id)
        log_collection.write_working_to_file(downloader.output_path, force_overwrite=True)
        return log_collection

    @staticmethod
    def from_round_range(start_round_id: int, end_round_id: int, logs_we_care_about: list[str] = None) -> LogFile:
        """Downloads multiple rounds worth of data.

        Parameters:
        `start_round_id` (int): first round to download
        `end_round_id` (int): last round to download (inclusive)
        `logs_we_care_about` (list[str]): list of strings, containing the file names.
        For example: `["game.txt", "attack.txt"]`. This defaults to all supported files.

        Example call: `my_logs = LogFile.from_multiple_rounds(185556, 191100)`

        Returns `LogFile`"""
        # Should be all supported log types as a default. Don't forget to update this list! (you will)
        if not logs_we_care_about:
            logs_we_care_about = ALL_LOGS_WE_PARSE.copy()

        downloader = RoundLogDownloader(start_round_id, end_round_id)
        downloader.output_only_log_line = True
        downloader.files = logs_we_care_about
        downloader.try_authenticate_interactive()
        asyncio.run(downloader.process_and_write())
        log_collection = LogFile.from_file(downloader.output_path)
        log_collection.log_type = LogFileType.COLLATED
        log_collection.log_source = f"{start_round_id}-{end_round_id}"
        log_collection.write_working_to_file(downloader.output_path, force_overwrite=True)
        return log_collection

    @staticmethod
    def from_round_collection(*rounds: int, logs_we_care_about: list[str] = None) -> LogFile:
        """Downloads multiple rounds worth of data.

        Parameters:
        `*rounds` (int): list of rounds to download
        `logs_we_care_about` (list[str]): list of strings, containing the file names.
        For example: `["game.txt", "attack.txt"]`. This defaults to all supported files.

        Example call: `my_logs = LogFile.from_round_collection(185556, 185558, 185560, ...)`

        Returns `LogFile`"""
        # Should be all supported log types as a default. Don't forget to update this list! (you will)
        if not logs_we_care_about:
            logs_we_care_about = ALL_LOGS_WE_PARSE.copy()

        downloader = RoundListLogDownloader(rounds)
        downloader.output_only_log_line = True
        downloader.files = logs_we_care_about
        downloader.try_authenticate_interactive()
        asyncio.run(downloader.process_and_write())
        log_collection = LogFile.from_file(downloader.output_path)
        log_collection.log_type = LogFileType.COLLATED
        log_collection.log_source = "rounds " + ', '.join(str(x) for x in rounds)
        log_collection.write_working_to_file(downloader.output_path, force_overwrite=True)
        return log_collection

    @staticmethod
    def from_ckey(ckey: str, rounds: int = 20, only_played: bool = False, filter_logs: bool = False,
                  logs_we_care_about: list[str] = None) -> LogFile:
        """Downloads multiple rounds worth of data, where the specified ckey was present.

        Parameters:
        `ckey` (str): the ckey
        `rounds` (int): number of rounds
        `filter` (bool): pre-emptively delete all logs not containing their ckey
        `logs_we_care_about` (list[str]): list of strings, containing the file names.
        For example: `["game.txt", "attack.txt"]`. This defaults to all supported files.

        Example call: `my_logs = LogFile.from_ckey("Riggle")`

        Returns `LogFile`"""
        # Should be all supported log types as a default. Don't forget to update this list! (you will)
        if not logs_we_care_about:
            logs_we_care_about = ALL_LOGS_WE_PARSE.copy()

        downloader = CkeyLogDownloader(ckey, only_played, rounds)
        downloader.output_only_log_line = True
        downloader.files = logs_we_care_about
        downloader.filter_logs = filter_logs
        downloader.try_authenticate_interactive()
        asyncio.run(downloader.process_and_write())
        log_collection = LogFile.from_file(downloader.output_path)
        log_collection.log_type = LogFileType.COLLATED
        log_collection.log_source = f"{rounds} latest rounds that {ckey} played in"
        log_collection.write_working_to_file(downloader.output_path, force_overwrite=True)
        return log_collection


if __name__ == "__main__":
    import sys
    LogFile.from_file(sys.argv[1]).print_working()
