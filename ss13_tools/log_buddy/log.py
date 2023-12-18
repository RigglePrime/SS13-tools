#!/usr/bin/env python3

from datetime import datetime
from enum import Enum
from typing import Annotated, Tuple, Optional
import re
from html import unescape as html_unescape
import json

from colorama import init
from dateutil.parser import isoparse

from ss13_tools.byond import canonicalize
from ss13_tools.log_buddy.expressions import LOC_REGEX, ADMIN_BUILD_MODE, ADMIN_STAT_CHANGE, \
    HORRIBLE_HREF, GAME_I_LOVE_BOMBS, ADMINPRIVATE_NOTE, ADMINPRIVATE_BAN, \
    LOG_PRETTY_LOC, LOG_PRETTY_STR, LOG_PRETTY_PATH
from ss13_tools.log_buddy.constants import LOG_COLOUR_SCARLET, LOG_COLOUR_RED, LOG_COLOUR_EMERALD, \
    LOG_COLOUR_PERIWINKLE, LOG_COLOUR_PINK, LOG_COLOUR_GRAY, LOG_COLOUR_PASTEL_CYAN, LOG_COLOUR_SUNSET, \
    LOG_COLOUR_PASTEL_ORANGE, LOG_COLOUR_AMETHYST, LOG_COLOUR_OCEAN, \
    MAX_SUPPORTED_LOG_VERSION


class LogType(Enum):
    """What type of log file is it?"""
    UNKNOWN = 0
    ACCESS = 1
    GAME = 2
    ADMIN = 3
    ADMINPRIVATE = 4
    OOC = 5
    SAY = 6
    WHISPER = 7
    EMOTE = 8
    RADIOEMOTE = 9
    ATTACK = 10
    VOTE = 11
    SILICON = 12
    PDA = 13
    MECHA = 14
    PAPER = 15
    VIRUS = 16
    TCOMMS = 17
    UPLINK = 18
    SHUTTLE = 19
    TOPIC = 20

    @staticmethod
    def list():
        """Lists all log types"""
        return list(LogType)

    @staticmethod
    def parse_log_type(string: str):
        """Gets the log type from a string"""
        try:
            return LogType[string.upper()]
        except KeyError:
            return LogType.UNKNOWN


class DamageType(Enum):
    """What type of damage is it? (enum)"""
    UNKNOWN = 0
    BRUTE = 1
    BURN = 2
    TOXIN = 3
    OXYGEN = 4
    CELLULAR = 5

    @staticmethod
    def parse_damage_type(string: str):
        """Gets the damage type from a string"""
        try:
            return DamageType[string.upper()]
        except KeyError:
            return DamageType.UNKNOWN


class SiliconLogType(Enum):
    """What type of silicon log is it? (enum)"""
    MISC = 0
    CYBORG = 1
    LAW = 2
    EMAG = 3


class AdminLogType(Enum):
    """What type of admin log is it? (enum)"""
    OTHER = "other"
    STATUS_CHANGE = "status_change"
    ANNOUNCE = "announce"
    PLAYER_PANEL = "pp"
    ANTAG_PANEL = "check_antag"
    AGHOST = "aghost"
    SUBTLE_MESSAGE = "sm"
    # OFFER_CONTROL = "offer"
    DIRECT_NARRATE = "dn"
    DAMAGE = "damage"
    DSAY = "dsay"
    SMITE = "smite"
    AHEAL = "aheal"
    COMMAND_REPORT = "command_report"
    BUILD_MODE = "buildmode"
    DELETE = "delete"
    SPAWN = "spawn"
    HEADSET_MESSAGE = "hm"
    # MODIFY = "mod"
    PLAY_SOUND = "sound"
    COMMEND = "commend"
    EQUIPMENT = "equipment"
    OBJECT_SAY = "osay"
    TELEPORT = "teleport"


class AdminprivateLogType(Enum):
    """What type of adminprivate is it? (enum)"""
    OTHER = "other"
    TICKET = "pm"
    ASAY = "asay"
    ERROR = "err"
    FILTER = "filter"
    INTERVIEW = "interview"
    NOTE = "note"
    BAN = "ban"


class Player:
    """This class holds methods for parsing ckey strings ('ckey/(name)')"""
    ckey: Optional[str]
    key: Optional[str]
    mob_name: Optional[str]

    def __init__(self, ckey: str, mob_name: str) -> None:
        self.key = ckey
        self.ckey = None if ckey == "*no key*" else ckey
        if self.ckey:
            if self.ckey.startswith('@'):
                self.ckey = self.ckey[1:]
            if self.ckey.endswith('[DC]'):
                self.ckey = self.ckey[:-4]
            self.ckey = canonicalize(self.ckey)
        self.mob_name = mob_name
        # We usually strip the closing bracket, what's one more string concat?
        if self.mob_name and '(' in self.mob_name:
            self.mob_name += ')'

    def __str__(self) -> str:
        if not self.mob_name:
            return self.key
        return f"{self.key}/({self.mob_name})"

    def __repr__(self) -> str:
        return f"{self.key}/({self.mob_name})"

    @staticmethod
    def parse_player(string: str):
        """Gets player's ckey and name from the following format:
        'ckey/(name)' (parentheses not required)"""
        ckey, name = string.strip().split("/", 1)
        return Player(ckey, name.strip("()"))

    @staticmethod
    def parse_players_from_full_log(string: str):
        """Gets all players from a full log line. Currently not implemented.
        (will be soon hopefully)"""
        # (\w+|\*no key\*)\/\(((?:\w+ ?)+?)\)
        # The above regex is not yet good enough, it catches
        # "MY NAME/(John Smith)" as the ckey "NAME"

        # ((?:\w+ ?)+|\*no key\*)\/\(((?:\w+ ?)+?)\)
        # Above does not work since it catches "has grabbed MY NAME/(John Smith)"
        # as the ckey "has grabbed MY NAME"
        raise NotImplementedError("Not yet implemented")


class UnknownLogException(Exception):
    """Thrown when a log type is not known. (so unexpected!)"""


class UnsupportedSchemaVersionException(Exception):
    """Thrown when a JSON log schema isn't supported. (so unexpected!)"""


class Log:
    """Represents one log entry

    Examples:
    log = `Log("log line here")` # NOTE: must be a valid log entry"""

    def __init__(self, line: Optional[str] = None) -> None:
        if not line:
            raise UnknownLogException("Log line empty!")

        self.json_schema = None
        self.time = None
        self.agent = None
        self.patient = None
        self.location = None
        self.location_name = None
        self.text = None
        self.is_dead = None
        self.raw_line = line

        if line[0] == "{":
            self.__json_parse()
            return
        if line[0] == "[":
            self.__parse_old_log()
            return
        raise UnknownLogException("Unsupported log")

    def __parse_old_log(self):
        date_time, other = self.raw_line.split("] ", 1)
        self.time = isoparse(date_time[1:])  # Remove starting [
        if other.endswith("VOTE:"):
            other += " "

        # Check for TGUI logs
        if ": " not in other and (" in " in other or " (as " in other):
            # TGUI logs work the following way:
            # If it's a mob, add "[mob.ckey] (as [mob] at [mob.x],[mob.y],[mob.z])"
            # If it's a client, just add "[client.ckey]"
            # Now it checks for context and window. If any of those are true, it
            # appends " in [window]" (or context instead of window).
            # You see, here's the problem. What if we only have a client and no window or context?
            # Is that even possible? I am too lazy to make sure and will assume it's not.
            # If it is, hi! Welcome to hell. Please edit the conditional before to work.
            # Just know that it will catch false positives. What fun world of logging we live in.
            self.parse_tgui(other)
            return
        log_type, other = other.split(": ", 1)
        self.log_type = LogType.parse_log_type(log_type.replace("GAME-", "", 1))
        # Python go brrrrrrr
        parsing_function = getattr(self, f"parse_{self.log_type.name.lower()}", None)
        if parsing_function:
            parsing_function(other)

    def __json_parse(self):
        log = json.loads(self.raw_line)
        if not log['s-ver'].count('.') == 2:
            raise UnknownLogException("Schema version corrupted")
        max_supported = tuple(int(x) for x in MAX_SUPPORTED_LOG_VERSION.split('.'))
        schema_version = tuple(int(x) for x in log['s-ver'].split('.'))
        for i in range(len(max_supported)):  # pylint: disable=consider-using-enumerate
            if max_supported[i] > schema_version[i]:
                break
            if max_supported[i] < schema_version[i]:
                raise UnsupportedSchemaVersionException(f"Unsupported schema: {log['s-ver']}")
        self.json_schema = log['s-ver']
        self.time = isoparse(log['ts'])
        self.log_type = LogType.parse_log_type(log['cat'].replace("game-", "", 1))
        parsing_function = getattr(self, f"parse_{self.log_type.name.lower()}", None)
        if parsing_function:
            parsing_function(log['msg'])

    json_schema = Annotated[str, "JSON schema version. None if not a JSON log"]
    time: Annotated[datetime, "Time of logging"]
    agent: Annotated[Optional[Player], "Player performing the action"]
    patient: Annotated[Optional[Player], "Player receiving the action"]
    raw_line: Annotated[str, "Raw, unmodified line"]
    log_type: Annotated[LogType, "Type of the log"]
    location: Annotated[Optional[Tuple[int, int, int]], "X, Y, Y where the action was performed"]
    location_name: Annotated[Optional[str], "Name of the location where the action was performed"]
    text: Annotated[Optional[str], "Any remaining unparsed text"]
    is_dead: Annotated[Optional[bool], "Is the agent dead?"]

    # Attack specific
    combat_mode: Annotated[bool, "This variable will store if the combat mode was on or off (only applies to attack logs)"]
    damage_type: Annotated[DamageType, "If the log type is attack, the damage type will be stored here"]
    new_hp: Annotated[float, "If the log type is attack, the new hp info will be stored here"]

    # Silicon specific
    silicon_log_type: Annotated[SiliconLogType, "If log type is silicon, it will represent the subtype, otherwise None"]

    # Virus specific
    virus_name: Annotated[SiliconLogType, "If log type is virus, it will store the virus name"]

    # Telecomms specific
    telecomms_network: Annotated[str, "If log type is TCOMMS, the network on which the message was spoken \
                                      on will be stored here"]

    # Admin specific
    admin_log_type: Annotated[AdminLogType, "Sores what kind of admin log it is (None if not an admin log)"]

    # Adminprivate specific
    adminprivate_log_type: Annotated[AdminprivateLogType, "Sores what kind of admin log it is (None if not an admin log)"]
    ticket_number: Annotated[int, "Stores the ticket number, if this log is a ticket"]

    def parse_game(self, log: str) -> None:  # noqa: C901
        """Parses a game log entry from `GAME:` onwards (GAME: should not be included)"""
        other = log
        if other.startswith("Gold Slime chemical mob spawn reaction occuring at"):
            agent = other.split("with last fingerprint ", 1)[-1]
            self.agent = Player(agent.strip(), None)
            loc_start = self.__parse_and_set_location(other)
            other, location_name = other[:loc_start].split("occuring at ", 1)
            self.location_name = location_name.strip()
            self.text = other.strip()
            return
        if " relic used by " in other:
            self.admin_log_type = AdminLogType.OTHER
            agent, other = other.split(" relic used by ", 1)[-1].rsplit(" in ", 1)
            self.agent = Player.parse_player(agent)
            self.text = other.strip()
            loc_start = self.__parse_and_set_location(other)
            if loc_start > 0:
                self.location_name = other[:loc_start].strip()
            self.text = log[:20].strip()
            return
        if match := re.match(GAME_I_LOVE_BOMBS, other):
            self.agent = Player.parse_player(match[1])
            self.text = other.strip()
            return
        if other.startswith("Blast wave primed by "):
            agent, location = other[21:].split(" fired from ", 1)
            location = location.split(" roughly towards ", 1)[0].strip()
            self.agent = Player.parse_player(agent.strip())
            loc_start = self.__parse_and_set_location(location)
            self.location_name = location[:loc_start].strip()
            self.text = other.strip()
            return
        if "rune activated by " in other:
            agent, location = other.split("rune activated by ", 1)[-1].split(" at ", 1)
            self.agent = Player(None, agent.strip())
            loc_start = self.__parse_and_set_location(location)
            self.location_name = location[:loc_start].strip()
            self.text = other.strip()
            return
        if other.startswith("The station self-destruct terminal was armed"):
            other, location = other.split(" at (", 1)
            location, agent = location.split(") by ")
            self.agent = Player.parse_player(agent.strip(". "))
            loc_start = self.__parse_and_set_location(location)
            self.location_name = location[:loc_start]
            return
        loc_start = self.__parse_and_set_location(other)
        if loc_start > 0:
            if "emitter turned " in other:
                other, player_and_loc = other.split(" by ", 1)
                player_and_loc = player_and_loc.split(" in ", 1)
                self.agent = Player.parse_player(player_and_loc[0])
                self.location_name = player_and_loc[1].split(" (")[0].strip()
            elif "emitter lost power" in other:
                self.location_name = other[:loc_start].split(" in ", 1)[-1].strip()
            elif other.startswith("A grenade detonated") or \
                    other.startswith("An explosion has triggered a gibtonite deposit") or \
                    other.startswith("Reagent explosion reaction occurred") or \
                    other.startswith("Life (") or \
                    (" at " in other and " (" not in other[:loc_start]):
                self.location_name = other[:loc_start].split(" at ")[-1].strip()
            elif " in " in other and " (" not in other[:loc_start]:
                self.location_name = other[:loc_start].split(" in ")[-1].strip()
            elif " on fire with " in other:
                agent, patient = other.split(") set ", 1)
                self.agent = Player.parse_player(agent.strip())
                self.patient = Player.parse_player(patient.split(" on fire with ", 1)[0])
                self.location_name = other[:loc_start].split(" at ", 1)[-1].strip()
                self.text = other.strip()
                return
            elif log.startswith("A projectile "):
                other, agent = log.split(" held by ")
                self.agent = Player.parse_player(agent.split(" at ")[0])
                self.text = other.strip()
                return
            elif " fired a cannon in " in other:
                self.location_name = other[:loc_start].split(" fired a cannon in ", 1)[-1]
            else:
                self.location_name = other[:loc_start].rsplit(" (", 1)[-1].strip()
        if "Last fingerprints: " in other:
            other, fingerprints = other.strip(". ").split("Last fingerprints: ")
            if fingerprints.startswith("[Projectile firer: "):
                # Remove the start, and the closing bracket
                fingerprints = fingerprints[19:-1]
            fingerprints = fingerprints.lstrip()
            if "/(" in fingerprints:
                self.agent = Player.parse_player(fingerprints)
            elif fingerprints != "*null*":
                self.agent = Player(fingerprints, None)
        if log.startswith("Bomb valve opened"):
            agent = log.split("- Last touched by: ")[1]
            match = re.match(HORRIBLE_HREF, agent)
            self.agent = Player(match[1], match[2])
        elif log.startswith("Lesser Gold Slime chemical mob spawn") or \
                log.startswith("Friendly Gold Slime chemical mob spawn") or \
                log.startswith("Life (hostile) chemical mob spawn reaction") or \
                log.startswith("Life (friendly) chemical mob spawn reaction"):
            agent, fingerprints = log.split(" carried by ", 1)[1].split(" with last fingerprint ")
            if agent.startswith("*null*"):
                self.agent = Player(fingerprints, None)
            else:
                self.agent = Player.parse_player(agent)
        elif "ignited in" in other and " by " in other:
            self.agent = Player.parse_player(other.split(" by ")[1].strip())
        elif "/(" in other and ") " in other:
            self.agent = Player.parse_player(other.split(") ", 1)[0])
        self.text = other.strip()

    def parse_topic(self, log: str) -> None:
        """Parses a game log entry from `TOPIC:` onwards (TOPIC: should not be included)"""
        self.text = log.strip()

    def parse_access(self, log: str) -> None:
        """Parses a game log entry from `ACCESS:` onwards (ACCESS: should not be included)"""
        if log.startswith("Login: "):
            if "/(" in log:
                self.agent = Player.parse_player(log[7:].split(" from ")[0])
            else:
                self.agent = Player(log[7:].split(" from ")[0], None)
        elif log.startswith("Mob Login: "):
            agent = log[11:].split(" was assigned to")[0]
            if "/(" in log:
                self.agent = Player.parse_player(agent)
            else:
                self.agent = Player(agent, None)
        elif log.startswith("Logout: "):
            if "/(" in log:
                self.agent = Player.parse_player(log[8:])
            else:
                self.agent = Player(log[8:], None)
        self.text = log.strip()

    # Another one of those overly-complex functions, but what can you do...
    def parse_admin(self, log: str) -> None:  # noqa: C901
        """Parses a game log entry from `ADMIN:` onwards (ADMIN: should not be included)"""
        # A yandere dev looking function. I'd do a regex but this runs faster
        # I'm calling this current implementation good enough. It's not the best, but it will do
        # TODO: improve. Consider finite state machines
        self.admin_log_type = AdminLogType.OTHER
        other = log
        if other.startswith("Announce: "):
            self.admin_log_type = AdminLogType.ANNOUNCE
            _, other = other.split(": ", 1)
            agent, other = other.split(") ", 1)
            self.agent = Player.parse_player(agent)
            self.text = other[1:].strip()  # Remove ':'
            return
        if other.startswith("SubtlePM: "):
            self.admin_log_type = AdminLogType.SUBTLE_MESSAGE
            _, other = other.split(": ", 1)
            agent, other = other.split(" -> ", 1)
            self.agent = Player.parse_player(agent)
            patient, other = other.split(") : ", 1)
            self.patient = Player.parse_player(patient)
            self.text = other.strip()
            return
        if other.startswith("Chat Name Check: ") or other.startswith("<span class='boldnotice'>Roundstart logout report"):
            self.text = other.strip()
            return
        if other.startswith("Build Mode: "):
            self.admin_log_type = AdminLogType.BUILD_MODE
            _, other = other.split(": ", 1)
            agent, other = other.split(") ", 1)
            self.agent = Player.parse_player(agent)
            loc_start = self.__parse_and_set_location(other)
            if loc_start > 0:
                if "modified the " in other:
                    self.text = other.strip()
                    return
                if " at " in other and not other.startswith("threw the"):
                    other, location_name = other[:loc_start].split(" at ", 1)
                    self.location_name = location_name.strip()
                elif "filled the region from" in other:
                    self.location_name = other[:loc_start].rsplit(" through ", 1)[-1].strip()
                else:
                    self.location_name = other[:loc_start].rsplit("(", 1)[-1].strip()
                    other = other[:loc_start].replace(self.location_name, "").strip(" (")
            self.text = other.strip()
            return
        if other.startswith("Starting query #"):
            self.text = other.strip()
            return
        if other.startswith("CIRCUIT: "):
            self.text = other.strip()
            return
        if other.startswith("DirectNarrate: "):
            self.admin_log_type = AdminLogType.DIRECT_NARRATE
            agent, other = other[15:].split(" to ", 1)
            self.agent = Player.parse_player(agent)
            patient, other = other.split("): ", 1)
            self.patient = Player.parse_player(patient)
            self.text = other.strip()
            return
        match = re.search(ADMIN_STAT_CHANGE, other)
        if match:
            self.admin_log_type = AdminLogType.STATUS_CHANGE
            agent, other = other.split(match[0])
            self.agent = Player(agent.strip(), None)
            other = match[0] + other.rstrip('.')
            self.text = other.strip()
            return
        if other.startswith("DSAY: "):
            self.__generic_say_parse(log[6:])
            return
        # If we're here, the line probably starts with our agent
        # Except when it doesn't
        if " exploit " in other and "attempted" in other:
            self.text = other.strip()
            return
        if other.endswith(" is trying to join, but needs to verify their ckey."):
            if "/(" in other:
                self.agent = Player.parse_player(other.split(") ", 1)[0].strip())
            else:
                self.agent = Player(other.split(" ", 1)[0].strip(), None)
            self.text = other.strip()
            return
        if " custom away mission" in other:
            other = other.replace("Admin ", "", 1)  # Because WHY WOULD IT BE UNIFORM
            agent, other = other.split(") ", 1)
            self.agent = Player.parse_player(agent)
            return
        if other.startswith("*null*"):
            self.text = other.strip()
            return
        if " has no jobs enabled, " in other:
            self.agent = Player(other.split(" has no jobs enabled, ")[0], None)
            self.text = other.strip()
            return
        if ") " in other:
            agent, other = other.split(") ", 1)
            self.agent = Player.parse_player(agent)
        if re.search(ADMIN_BUILD_MODE, other):
            self.admin_log_type = AdminLogType.BUILD_MODE
        elif other.startswith("made the ") and ' say "' in other:
            self.admin_log_type = AdminLogType.OBJECT_SAY
            patient, other = other[9:].split(' at ', 1)
            self.patient = Player(None, patient)
            location_name, other = other.split(' say "')
            loc_start = self.__parse_and_set_location(location_name)
            if loc_start > 0:
                location_name = location_name[:loc_start]
            self.location_name = location_name.strip()
            self.text = other.rstrip('"')
            return
        elif other.startswith("has created a command report: "):
            self.admin_log_type = AdminLogType.COMMAND_REPORT
            # I can't be bothered anymore
        elif other.startswith("(reply to "):
            self.admin_log_type = AdminLogType.HEADSET_MESSAGE
            # len("(reply to ") == 10
            other = other[10:]
            patient, other = other.split(") ", 1)
            self.patient = Player.parse_player(patient)
            loc_start = self.__parse_and_set_location(other)
            if loc_start > 0:
                self.location_name = other[:loc_start].split("(")[-1].strip()
                other = other[:loc_start].replace(self.location_name, "").strip(" (")
            self.text = other.strip(' "')
            return
        elif other.startswith("created ") or other.startswith("spawned ") or other.startswith("pod-spawned "):
            self.admin_log_type = AdminLogType.SPAWN
        elif other.startswith("changed the equipment of "):
            self.admin_log_type = AdminLogType.EQUIPMENT
            self.patient = Player.parse_player(other[25:])
        elif other.startswith("dealt ") and " to " in other:
            self.admin_log_type = AdminLogType.DAMAGE
            self.patient = Player.parse_player(other.split(" to ", 1)[1].strip())
        elif other.startswith("commended "):
            self.admin_log_type = AdminLogType.COMMEND
            self.patient = Player.parse_player(other[10:])
        elif other.startswith("has offered control of "):
            # len("has offered control of (" == 24
            self.patient = Player.parse_player(other[24:].rsplit(")", 1)[0])
        elif other.startswith("added a new objective for "):
            self.patient = Player(other[26:].split(":", 1)[0], None)
        elif other.startswith("played web sound"):
            self.admin_log_type = AdminLogType.PLAY_SOUND
        elif other.startswith("jumped to "):
            self.admin_log_type = AdminLogType.TELEPORT
            loc_start = self.__parse_and_set_location(other)
            if loc_start > 0:
                # len("jumped to ") == 10
                self.location_name = other[10:loc_start].strip()
        elif other.startswith("teleported "):
            self.admin_log_type = AdminLogType.TELEPORT
            # len("teleported ") == 11
            if " to " not in other:
                self.patient = Player.parse_player(other[11:])
                self.text = log.strip()
                return
            patient, location = other[11:].split(" to ", 1)
            self.patient = Player.parse_player(patient)
            loc_start = self.__parse_and_set_location(location)
            if loc_start > 0:
                self.location_name = location[:loc_start].strip()
        elif other.startswith("has removed ") and "antagonist status" in other:
            self.admin_log_type = AdminLogType.ANTAG_PANEL
            self.patient = Player.parse_player(other[other.index("antagonist status from ") + 23:])
        elif other.startswith("punished "):
            self.admin_log_type = AdminLogType.SMITE
            # Same as before
            self.patient = Player.parse_player(other[9:])
        elif other.startswith("healed / Revived "):
            self.admin_log_type = AdminLogType.AHEAL
            self.patient = Player.parse_player(other[17:])
        elif other.startswith("possessed a golem shell enslaved to"):
            # Same as before, 36 is the len
            self.patient = Player.parse_player(other[36:])
        elif " player panel" in other:
            self.admin_log_type = AdminLogType.PLAYER_PANEL
            if "individual" in other and "*null*" not in other:
                # Same again
                patient = Player.parse_player(other[17:-1])
            return
        elif "checked antagonists" in other:
            self.admin_log_type = AdminLogType.ANTAG_PANEL
        elif "admin ghosted" in other:
            self.admin_log_type = AdminLogType.AGHOST
        # For debugging. No, I won't remove it.
        # if not self.agent:
        #     print("\u001b[31m[!]\u001b[0m", log)
        # if self.admin_log_type == AdminLogType.OTHER and not self.patient:
        #     print("\u001b[33m[*]\u001b[0m", log)
        self.text = other.strip()

    def parse_adminprivate(self, log: str) -> None:  # noqa: C901
        """Parses a game log entry from `ADMINPRIVATE:` onwards
        (ADMINPRIVATE: should not be included)"""
        other = log
        self.adminprivate_log_type = AdminprivateLogType.OTHER
        if other.startswith("ASAY: "):
            self.adminprivate_log_type = AdminprivateLogType.ASAY
            agent, other = other[6:].split(' "', 1)
            self.agent = Player.parse_player(agent.strip())
            other, location = other.split('" (', 1)
            loc_start = self.__parse_and_set_location(location)
            self.location_name = location[:loc_start].strip()
            self.text = html_unescape(other.strip())
            return
        if other.startswith("Ticket #"):
            self.adminprivate_log_type = AdminprivateLogType.TICKET
            ticketno, agent, other = other[8:].split(": ", 2)
            self.ticket_number = int(ticketno)
            self.agent = Player.parse_player(agent)
            self.text = other.strip()
            return
        if other.startswith("PM: "):
            if other.startswith("Ticket #"):
                # len("PM: Ticket #") == 12
                ticketno, other = other[12:].split(": ", 1)
                self.ticket_number = int(ticketno)
            agent, other = other.split(")->", 1)
            self.agent = Player.parse_player(agent)
            patient, other = other.split("): ", 1)
            self.patient = Player.parse_player(patient)
            self.text = other.strip()
            return
        if other.startswith("Ticket <A HREF"):
            end_of_ticket_id = other.index("</A> ")
            self.ticket_number = int(other[other.index("'>#")+3:end_of_ticket_id])
            start_of_agent = other.index(" by <")
            match = re.match(HORRIBLE_HREF, other[start_of_agent+4:])
            self.agent = Player(match[1], match[2])
            self.text = other[end_of_ticket_id + 5:start_of_agent]
            return
        if other.startswith("New interview created for "):
            self.adminprivate_log_type = AdminprivateLogType.INTERVIEW
            # Strip the startswith content and last dot
            self.agent = Player.parse_player(other[26:-1])
        if "has passed the" in other and "filter" in other:
            self.adminprivate_log_type = AdminprivateLogType.FILTER
            self.agent = Player.parse_player(other[:other.index(" has passed")])
        elif match := re.match(ADMINPRIVATE_NOTE, other):
            self.adminprivate_log_type = AdminprivateLogType.NOTE
            self.agent = Player.parse_player(match[1].strip())
            self.patient = Player(match[4], None)
            self.text = f"{match[2]} a {match[3]}: {match[5]}"
            return
        elif match := re.match(ADMINPRIVATE_BAN, other):
            self.adminprivate_log_type = AdminprivateLogType.BAN
            self.agent = Player.parse_player(match[1].strip())
            self.patient = Player(match[3], None)
            self.text = match[2].strip() + " from " + match[4]
            return
        elif other.startswith("Notice: Connecting player "):
            self.agent = Player(other[26:].split(" has the same", 1)[0], None)
        elif other.startswith("ERROR: "):
            self.adminprivate_log_type = AdminprivateLogType.ERROR
        self.text = log.strip()

    def parse_ooc(self, log: str) -> None:
        """Parses a game log entry from `OOC:` onwards (OOC: should not be included)"""
        self.__generic_say_parse(log)

    def parse_say(self, log: str) -> None:
        """Parses a game log entry from `SAY:` onwards (SAY: should not be included)"""
        self.__generic_say_parse(log)

    def parse_whisper(self, log: str) -> None:
        """Parses a game log entry from `WHISPER:` onwards (WHISPER: should not be included)"""
        self.__generic_say_parse(log)

    def parse_emote(self, log: str) -> None:
        """Parses a game log entry from `EMOTE:` onwards (EMOTE: should not be included)"""
        agent, other = log.split(") ", 1)  # Ensure that we didn't get a name with spaces
        self.agent = Player.parse_player(agent)
        if " (" not in other:
            self.text = other.strip()
            return
        action, location, coords = other.rsplit(' (', 2)
        self.text = action
        self.__parse_and_set_location('(' + coords)
        self.location_name = location.strip()

    def parse_radioemote(self, log: str) -> None:
        """Parses a game log entry from `RADIOEMOTE:` onwards
        (RADIOEMOTE: should not be included)"""
        self.parse_emote(log)

    # I have decided that we will all just have to bear with it.
    def parse_attack(self, log: str) -> None:  # noqa: C901
        """Parses a game log entry from `ATTACK:` onwards (ATTACK: should not be included)"""
        player_agent = ") " in log
        object_agent = "] " in log
        if player_agent and object_agent:
            # Why must the logs do this to us
            if log.index("] ") < log.index(") "):
                player_agent = False
        if player_agent:
            agent, other = log.split(") ", 1)
            self.agent = Player.parse_player(agent)
        elif object_agent:
            agent, other = log.split("] ", 1)
            # Remove [, since the name usually looks like "[frag grenade] has ..."
            self.agent = Player(None, agent[1:])
        else:
            # Just in case there's some strange log entry
            return

        loc_start = self.__parse_and_set_location(other)
        if loc_start > 0:
            self.location_name = other[:loc_start].split("(")[-1].strip()
            other = other[:loc_start].replace(self.location_name, "").strip(" (")
        # Combat mode regex
        match = re.search(r"\(COMBAT MODE: (\d)\)", other)
        if match:
            self.combat_mode = bool(int(match.group(1)))
            other = other.replace(match.group(0), "")
        # Damage type regex
        match = re.search(r"\(DAMTYPE: (\w+)\)", other)
        if match:
            self.damage_type = DamageType.parse_damage_type(match.group(1))
            other = other.replace(match.group(0), "")
        # New HP regex
        match = re.search(r"\(NEWHP: (-?\d+\.?\d?)\)", other)
        if match:
            self.new_hp = float(match.group(1))
            other = other.replace(match.group(0), "")

        # NOTE: There is no better way of doing this. Why? Because the ckey isn't a ckey,
        # it's a key WHICH COULD CONTAIN SPACES AND IT'S IMPOSSIBLE TO TELL WHAT IS PART
        # OF THE KEY AND WHAT ISN'T. I love SS13 logs.
        parse_key = False
        other_temp = None
        # One word
        if other.startswith("injected"):
            other_temp = other.split(" ", 1)[1]
            parse_key = True
        elif other.startswith(("attacked ", "shot ", "electrocuted ", "crushed ",
                               "shoved ", "grabbed ", "shaken ", "thrown ", "kicks ",
                               "kicked")) and other[9] != "[":
            other_temp = other.split(" ", 1)[1]
            parse_key = True
        # NOTE: Performance? Not sure if it helps go check yourself, I am too lazy
        elif not other.startswith(("has", "was", "is", "started", "fired at", "stun attacked")):
            # I love the logs. I love spaghetti.
            if "is being stripped of" in other or \
                    "has been stripped of" in other or \
                    "is being pickpocketed of" in other or \
                    "is having the" in other:
                patient = other.split(") ", 1)[0]
                self.patient = Player.parse_player(patient)
            elif other.startswith("surgically removed") and "from" in other:
                patient = other.split(" from ", 1)[1].split(") ", 1)[0]
                self.patient = Player.parse_player(patient)
        # A large tuple... there is no better way, I thought for a long time
        # If you think of a better way, please PR it or make an issue report

        # Special case, has no patient or other text
        elif other.startswith("was flashed(AOE)"):
            pass
        # Two words
        elif other.startswith((
            "has shot", "has sprayed", "has attacked", "has grabbed",
            "has shaken", "has bolted", "has unbolted", "has fed",
            "has kicked", "has flashed", "was flashed", "has tabled",
            "has shoved", "has pushed", "has healed", "has injected",
            "has punched", "has revived", "has applied", "has CPRed",
            "has handcuffed", "has crushed", "has tackled", "has electrocuted",
            "has attached", "has strangled", "has cremated", "has zapped",
            "has implanted", "has stung", "has augmented", "has bopped", "has stuffed",
            "has places",  # Do NOT fix this typo, I will have to add another damn startswith
            # "has hit", # I don't think this is ever used against players, so I'll leave it out
            # Another typo... feel free to fix for free GBP since we already have "kicked"
            "has kicks", "fired at", "has stripped", "has thrown", "stun attacked",
            "is stripping"
        )):
            other_temp = other.split(" ", 2)[2].replace("(CQC) ", "")
            parse_key = True
        # Splashed has a special case :)))
        elif other.startswith("has splashed"):
            other_temp = other.replace("(thrown) ", "")
            other_temp = other_temp.split(" ", 2)[2]
            parse_key = True
        # Three words
        elif other.startswith((
            "has fired at",
            # "started fireman carrying", # Doesn't have a ckey, just a mob name
            # "was fireman carried by", # Doesn't have a ckey, just a mob name
            "has operated on",
            "has stun attacked",
            # "has pulled from", # Annoying to implement, so I won't
            "has restrained (CQC)",
            "has CQCs (CQC)",  # Many typos were discovered today
            "has disarmed (CQC)",
            "has resisted grab",
            "has broke grab",
            "has head slammed"
        )):
            other_temp = other.split(" ", 3)[3]
            parse_key = True
        # Four words
        elif other.startswith("has") and other.startswith((
            "has attempted to inject",
            "has attempted to punch",
            "has attempted to strangle",
            "has been shot by",  # NOTE: shot by can have an empty value. I love SS13 logs
            "has threw and hit",
            "has attempted to handcuff",
            "has attempted to apply",
            "has failed to handcuff"
        )):
            other_temp = other.split(" ", 4)[4]
            parse_key = True
        # Five words
        elif other.startswith(("has tended to the wounds", "has attempted to neck grab",
                               "has overloaded the heart of")):
            other_temp = other.split(" ", 5)[5]
            parse_key = True

        if parse_key and other_temp[0] != "[":
            patient = other_temp.split(") ", 1)[0]
            if "/(" in patient:
                self.patient = Player.parse_player(patient)
            del other_temp
        # NOTE: surgery related logs were not added, as they are quite rare and I don't
        # think they'd contribute much. Feel free to add them yourself.
        # Example: "has surgically removed"
        # On another note, `attached a the saline-glucose solution bottle to the`
        self.text = other.strip()

    def parse_vote(self, log: str) -> None:
        """Parses a game log entry from `VOTE:` onwards (VOTE: should not be included)"""
        self.text = log.replace("<b>", "").replace("</b>", "").strip()

    def parse_silicon(self, log: str) -> None:
        """Parses a game log entry from `SILICON:` onwards (SILICON: should not be included)"""
        if log.startswith("CYBORG: "):
            self.silicon_log_type = SiliconLogType.CYBORG
            log = log[8:]
        elif log.startswith("LAW: "):
            self.silicon_log_type = SiliconLogType.LAW
            log = log[5:]
        elif "upload console was created at" in log:
            self.text = log.strip()
            loc_start = self.__parse_and_set_location(log)
            if loc_start > 0:
                self.location_name = log[:loc_start].rsplit('(', 1)[1].strip()
            return
        else:
            self.silicon_log_type = SiliconLogType.MISC
        agent, other = log.split(") ", 1)
        self.agent = Player.parse_player(agent)

        if self.silicon_log_type == SiliconLogType.LAW and other.startswith("used "):
            patient = other.split(" on ", 1)[1].split(") ", 1)[0]
            if not patient.startswith("*null*"):
                self.patient = Player.parse_player(patient)
        self.text = other.strip()
        # NOTE: someone PLEASE fix logging this is getting ridiculous
        # NOTE: there is no reliable way of getting the second key here

    def parse_pda(self, log: str) -> None:
        """Parses a game log entry from `PDA:` onwards (PDA: should not be included)"""
        agent, other = log.split(") ", 1)
        self.agent = Player.parse_player(agent)
        # Sending a message with the message monitor console adds a "sent " FOR NO PARTICULAR REASON
        # It gets better... it also moves " to "...
        if "PDA: message monitor console" in other or "Tablet: message monitor console" in other or\
                "PDA: Citation Server" in other:
            _pda_type, other = other.split(') sent "')
            if '" to ' not in other:
                self.text = html_unescape(other.strip())
                return
            text, other = other.split('" to ', 1)
            loc_start = self.__parse_and_set_location(other)
            self.location_name = other[:loc_start].split("(")[-1].strip()
            # -1 for a space that we stripped, and an extra 1 for the bracket
            patient = other[:loc_start - len(self.location_name) - 2].strip()
        else:
            _pda_type, other = other.strip(" (").split(" to ", 1)
            patient, other = other.split(') "', 1)
            # If this happens, it's probably a multiline PDA message...
            # And if not? Another exception to add to the list...
            if '"' not in other:
                text = other
            else:
                text, location = other.split('" (', 1)
                loc_start = self.__parse_and_set_location(location)
                self.location_name = location[:loc_start].strip()
        self.patient = Player(None, patient)
        self.text = html_unescape(text.strip())

    def parse_mecha(self, log: str) -> None:
        """Parses a game log entry from `MECHA:` onwards (MECHA: should not be included)"""
        self.text = log.strip()
        loc_start = self.__parse_and_set_location(log)
        self.location_name = log[:loc_start].split("(")[-1].strip()

    def parse_paper(self, log: str) -> None:
        """Parses a game log entry from `PAPER:` onwards (PAPER: should not be included)"""
        agent, other = log.split(") ", 1)
        self.agent = Player.parse_player(agent)
        self.text = other.strip()

    def parse_virus(self, log: str) -> None:
        """Parses a game log entry from `VIRUS:` onwards (VIRUS: should not be included)"""
        if log.startswith("A culture bottle was printed for the virus"):
            agent = log.split(") by ", 1)[1]
            self.agent = Player.parse_player(agent)
            self.virus_name, other = log.split("A culture bottle was printed for the virus ")[1]\
                                        .split(" sym:", 1)
            self.text = "printed, sym:" + other.strip()
        else:
            agent, other = log.split(" was infected by virus: ")
            self.agent = Player.parse_player(agent)
            if " sym:" not in other:
                # Heart attacks my beloved...
                self.text = other.strip()
                return
            virus_name, other = other.split(" sym:")
            self.virus_name = virus_name
            self.text = "infected, sym:" + other.strip()
        # Location is available in both cases
        loc_start = self.__parse_and_set_location(log)
        self.location_name = log[:loc_start].split("(")[-1].strip()

    def parse_tcomms(self, log: str) -> None:
        """Parses a game log entry from `TCOMMS:` onwards (TCOMMS: should not be included)"""
        if " (spans: " not in log:
            # We only care about what people said on telecomms, not what device connected where
            return

        self.is_dead = False
        agent, other = log.split(" [", 1)
        if "/(" in agent:
            self.agent = Player.parse_player(agent)
        else:
            self.agent = Player(None, agent)
        channel, other = other.split("] (", 1)
        self.telecomms_network = channel
        _spans, other = other.split(') "', 1)
        text, other = other.split('" (', 1)
        self.text = html_unescape(text.strip())
        _language, location = other.split(") (", 1)
        loc_start = self.__parse_and_set_location(location)
        self.location_name = location[:loc_start].strip()

    def parse_uplink(self, log: str) -> None:
        """Parses a game log entry from `UPLINK:` onwards (UPLINK: should not be included)"""
        agent, other = log.split(") ", 1)
        self.agent = Player.parse_player(agent)
        self.text = html_unescape(other.strip())
        self.is_dead = False
        # Maybe in the future I could add a telecrystals variable, but I don't see a need

    def parse_shuttle(self, log: str) -> None:
        """Parses a game log entry from `SHUTTLE:` onwards (SHUTTLE: should not be included)"""
        if log.startswith(("Shuttle call reason:", "There is no means of calling the emergency shuttle anymore."))\
           or " set a new shuttle, " in log:
            self.text = html_unescape(log.strip())
            return

        agent, other = log.split(") ", 1)
        self.agent = Player.parse_player(agent)
        self.text = html_unescape(other.strip())

    def parse_tgui(self, log: str) -> None:
        """Parses a TGUI log without the date"""  # Send help, this is a mess
        other = log

        # Just in case because sometimes we have no ckey.
        # I wonder if the logging code was made only to screw with people like me.
        agent = "*no key*/(None)"

        if " (as " in other:
            key, other = other.split(" (as ", 1)
            mob, other = other.split(" at ", 1)
            location, other = other.split(")", 1)

            # Can't use parse_and_set_location because it's a snowflake log yet again! Fun.
            self.location = tuple(int(x) for x in location.split(","))

            agent = f"{key}/({mob})"

        if " in " in other:
            something, other = other.split(" in ", 1)
            something = something.strip()  # Just in case
            if something:
                # If the first branch ran, this should be empty. If it didn't then we have a ckey
                # Logging is a giant mess
                agent = f"{something}/(None)"
        self.agent = Player.parse_player(agent)

        # Set text to 'Empty' if other is empty, since we're expecting
        # extra data (newlines will get appended)
        self.text = other.strip() or "Empty"

    def __parse_and_set_location(self, log: str) -> int:
        """Finds and parses a location entry. (location name (x, y, z)). Can parse a raw line.

        Returns the position of the location in the string as in integer"""
        # NOTE: this does not set location name, as it is not always present
        # Find all possible location strings
        match = re.findall(LOC_REGEX, log)
        # Check if there are any results
        if not match:
            return -1
        # Get location of last match
        loc = log.rindex(match[-1])
        # Take the last result from the regex, remove the first and last character,
        # and turn into a list
        match = match[-1][1:-1].split(",")
        # Turn all elements to ints, convert to tuple
        self.location = tuple(int(x) for x in match)  # Bad practice since it's a side effect
        return loc

    def __generic_say_parse(self, log: str) -> None:
        """Parses a generic SAY log entry from SAY: onwards (includes SAY, WHISPER, OOC)
        (should only include line from SAY: onwards, without the SAY)"""
        agent, other = log.split(") ", 1)  # Ensure that we didn't get a name with spaces
        self.agent = Player.parse_player(agent)
        # Priority announcements, yet another exception
        if other.startswith(("(priority announcement)", "(message to the other server)",
                             "(message to CentCom)", "has requested the nuclear codes"))\
                and '" ' not in other:  # This indentation is a bit confusing IMO but flake8 insists...
            self.text = html_unescape(other.strip())
            return
        if other.startswith("(Personality Commune"):
            patient = other[24:-1]
            if not patient != "*null*":
                self.patient = Player(patient, None)
            other += ' '
        text, other = other.split('" ', 1)  # Do not change this
        self.text = html_unescape(text.strip('"').replace('"', '| '))
        if other.startswith("FORCED by AI Controller") or not other:
            return
        other, location, coords = other.rsplit('(', 2)
        other = other.strip()
        if other:
            self.text += " | " + other

        self.is_dead = False
        if "(DEAD)" in text:
            text = text.replace("(DEAD) ", "", 1)
            self.is_dead = True
        self.__parse_and_set_location('(' + coords)
        self.location_name = location.strip()

    def __re_pretty_htmlescaped(self, colour):
        return lambda match: f"\033[38;5;{colour}m{html_unescape(match.group(0))}\033[0m"

    def __re_pretty(self, colour):
        return lambda match: f"\033[38;5;{colour}m{match.group(0)}\033[0m"

    def pretty(self):
        """Return, but with ANSI colour!"""
        if self.raw_line[0] == "{":
            return self.__pretty_json()
        to_be_printed = self.raw_line
        to_be_printed = re.sub(LOG_PRETTY_LOC, self.__re_pretty(LOG_COLOUR_PASTEL_CYAN), to_be_printed)
        to_be_printed = re.sub(LOG_PRETTY_PATH, self.__re_pretty(LOG_COLOUR_PASTEL_ORANGE), to_be_printed)
        to_be_printed = re.sub(LOG_PRETTY_STR, self.__re_pretty_htmlescaped(LOG_COLOUR_SUNSET), to_be_printed, 1)
        return to_be_printed.replace("[", "\033[38;5;240m[", 1).replace("]", "]\033[0m", 1)\
                            .replace("ACCESS:", f"\033[38;5;{LOG_COLOUR_GRAY}mACCESS:\033[0m", 1)\
                            .replace("ASSET:", f"\033[38;5;{LOG_COLOUR_GRAY}mASSET:\033[0m", 1)\
                            .replace("TOPIC:", f"\033[38;5;{LOG_COLOUR_GRAY}mTOPIC:\033[0m", 1)\
                            \
                            .replace("ADMIN:", f"\033[38;5;{LOG_COLOUR_PINK}mADMIN:\033[0m", 1)\
                            .replace("ADMINPRIVATE:", f"\033[38;5;{LOG_COLOUR_PINK}mADMINPRIVATE:\033[0m", 1)\
                            \
                            .replace("ATTACK:", f"\033[38;5;{LOG_COLOUR_RED}mATTACK:\033[0m", 1)\
                            \
                            .replace("GAME:", f"\033[38;5;{LOG_COLOUR_EMERALD}mGAME:\033[0m", 1)\
                            \
                            .replace("TRAITOR:", f"\033[38;5;{LOG_COLOUR_SCARLET}mTRAITOR:\033[0m", 1)\
                            .replace("UPLINK:", f"\033[38;5;{LOG_COLOUR_SCARLET}mUPLINK:\033[0m", 1)\
                            .replace("MALF UPGRADE:", f"\033[38;5;{LOG_COLOUR_SCARLET}mMALF UPGRADE:\033[0m", 1)\
                            .replace("CHANGELING:", f"\033[38;5;{LOG_COLOUR_SCARLET}mCHANGELING:\033[0m", 1)\
                            .replace("HERETIC RESEARCH:", f"\033[38;5;{LOG_COLOUR_SCARLET}mHERETIC RESEARCH:\033[0m", 1)\
                            .replace("SPELLBOOK:", f"\033[38;5;{LOG_COLOUR_SCARLET}mSPELLBOOK:\033[0m", 1)\
                            \
                            .replace("SAY:", f"\033[38;5;{LOG_COLOUR_PERIWINKLE}mSAY:\033[0m", 1)\
                            .replace("EMOTE:", f"\033[38;5;{LOG_COLOUR_PERIWINKLE}mEMOTE:\033[0m", 1)\
                            .replace("WHISPER:", f"\033[38;5;{LOG_COLOUR_PERIWINKLE}mWHISPER:\033[0m", 1)\
                            .replace("OOC:", f"\033[38;5;{LOG_COLOUR_PERIWINKLE}mOOC:\033[0m", 1)\
                            .replace("PDA:", f"\033[38;5;{LOG_COLOUR_PERIWINKLE}mPDA:\033[0m", 1)\
                            \
                            .replace("SILICON:", f"\033[38;5;{LOG_COLOUR_OCEAN}mSILICON:\033[0m", 1)\
                            \
                            .replace(str(self.agent), f"\033[38;5;{LOG_COLOUR_AMETHYST}m{str(self.agent)}\033[0m")\
                            .replace(str(self.patient), f"\033[38;5;{LOG_COLOUR_AMETHYST}m{str(self.patient)}\033[0m")\
                            .replace(str(self.location_name),
                                     f"\033[38;5;{LOG_COLOUR_PASTEL_CYAN}m{str(self.location_name)}\033[0m")

    def __pretty_json(self):
        return self.raw_line

    def __str__(self):
        """String representation"""
        return self.raw_line

    def __repr__(self):
        """Object representation"""
        return self.raw_line


if __name__ == "__main__":
    single_log = Log(input())
    init()
    print(single_log.pretty())
    print(single_log.__dict__)
