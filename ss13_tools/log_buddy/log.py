#!/usr/bin/env python3

from datetime import datetime
from enum import Enum
from typing import Annotated, Tuple, Optional
import re
from html import unescape as html_unescape

from dateutil.parser import isoparse

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

    @staticmethod
    def list():
        """Lists all log types"""
        return [x for x in LogType]

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

class Player:
    """This class holds methods for parsing ckey strings ('ckey/(name)')"""
    ckey: Optional[str]
    mob_name: Optional[str]

    def __init__(self, ckey: str, mob_name: str) -> None:
        self.ckey = None if ckey == "*no key*" else ckey
        self.mob_name = mob_name

    def __str__(self) -> str:
        return f"{self.ckey}/({self.mob_name})"

    def __repr__(self) -> str:
        return f"{self.ckey}/({self.mob_name})"

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
        raise Exception("Not yet implemented")

class UnknownLogException(Exception):
    """Thrown when a log type is not known. (so unexpected!)"""

class Log:
    """Represents one log entry

    Examples:
    log = `Log("log line here")` # NOTE: must be a valid log entry"""
    def __init__(self, line: Optional[str] = None) -> None:
        if not line or line[0] != "[":
            raise UnknownLogException("Does not start with [")

        self.time = None
        self.agent = None
        self.patient = None
        self.location = None
        self.location_name = None
        self.text = None
        self.is_dead = None

        self.raw_line = line
        date_time, other = self.raw_line.split("] ", 1)
        self.time = isoparse(date_time[1:]) # Remove starting [
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
        self.log_type = LogType.parse_log_type(log_type)
        # Python go brrrrrrr
        parsing_function = getattr(self, f"parse_{self.log_type.name.lower()}", None)
        if parsing_function:
            parsing_function(other)

    time: Annotated[datetime, "Time of logging"]
    agent: Annotated[Optional[Player], "Player performing the action"]
    patient: Annotated[Optional[Player], "Player receiving the action"]
    raw_line: Annotated[str, "Raw, unmodified line"]
    log_type: Annotated[LogType, "Type of the log"]
    location: Annotated[Optional[Tuple[int,int,int]], "X, Y, Y where the action was performed"]
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

    #Telecomms specific
    telecomms_network: Annotated[str, "If log type is TCOMMS, the network on which the message was spoken on will be stored here"]

    def parse_game(self, log: str) -> None:
        """Parses a game log entry from `GAME:` onwards (GAME: should not be included)"""
        self.text = log

    def parse_access(self, log: str) -> None:
        """Parses a game log entry from `ACCESS:` onwards (ACCESS: should not be included)"""
        self.text = log

    def parse_admin(self, log: str) -> None:
        """Parses a game log entry from `ADMIN:` onwards (ADMIN: should not be included)"""
        self.text = log

    def parse_adminprivate(self, log: str) -> None:
        """Parses a game log entry from `ADMINPRIVATE:` onwards
        (ADMINPRIVATE: should not be included)"""
        # TODO: add better parsing for tickets
        self.text = log

    def parse_ooc(self, log: str) -> None:
        """Parses a game log entry from `OOC:` onwards (OOC: should not be included)"""
        self.generic_say_parse(log)

    def parse_say(self, log: str) -> None:
        """Parses a game log entry from `SAY:` onwards (SAY: should not be included)"""
        self.generic_say_parse(log)

    def parse_whisper(self, log: str) -> None:
        """Parses a game log entry from `WHISPER:` onwards (WHISPER: should not be included)"""
        self.generic_say_parse(log)

    def parse_emote(self, log: str) -> None:
        """Parses a game log entry from `EMOTE:` onwards (EMOTE: should not be included)"""
        agent, other = log.split(") ", 1) # Ensure that we didn't get a name with spaces
        self.agent = Player.parse_player(agent)
        if " (" not in other:
            self.text = other.strip()
            return
        action, location = other.split(' (', 1)
        self.text = action
        loc_start = self.parse_and_set_location(location)
        self.location_name = location[:loc_start]

    def parse_radioemote(self, log: str) -> None:
        """Parses a game log entry from `RADIOEMOTE:` onwards
        (RADIOEMOTE: should not be included)"""
        self.parse_emote(log)

    def parse_attack(self, log: str) -> None:
        """Parses a game log entry from `ATTACK:` onwards (ATTACK: should not be included)"""
        if ") " in log:
            agent, other = log.split(") ", 1)
            self.agent = Player.parse_player(agent)
        elif "] " in log:
            agent, other = log.split("] ", 1)
            # Remove [, since the name usually looks like "[frag grenade] has ..."
            self.agent = Player(None, agent[1:])
        else:
            # Just in case there's some strange log entry
            return

        loc_start = self.parse_and_set_location(other)
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
        # NOTE: Performance? Not sure if it helps go check yourself, I am too lazy
        elif not other.startswith(("has", "was", "is", "started")): 
            # I love the logs. I love spaghetti.
            if "is being stripped of" in other or \
                    "has been stripped of" in other or \
                    "is being pickpocketed of" in other or \
                    "is having the" in other:
                patient = other.split(") ", 1)[0]
                self.patient = Player.parse_player(patient)
        # A large tuple... there is no better way, I thought for a long time
        # If you think of a better way, please PR it or make an issue report

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
            "has places", # Do NOT fix this typo, I will have to add another damn startswith
            # "has hit", # I don't think this is ever used against players, so I'll leave it out
            # Another typo... feel free to fix for free GBP since we already have "kicked"
            "has kicks"
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
            #"started fireman carrying", # Doesn't have a ckey, just a mob name
            #"was fireman carried by", # Doesn't have a ckey, just a mob name
            "has operated on",
            "has stun attacked",
            # "has pulled from", # Annoying to implement, so I won't
            "has restrained (CQC)",
            "has CQCs (CQC)", # Many typos were discovered today
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
            "has been shot by", # NOTE: shot by can have an empty value. I love SS13 logs
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
        else:
            self.silicon_log_type = SiliconLogType.MISC
        agent, other = log.split(") ", 1)
        self.agent = Player.parse_player(agent)

        if self.silicon_log_type == SiliconLogType.LAW and other.startswith("used "):
            agent = other.split(" on ", 1)[1].split(") ", 1)[0]
            self.agent = Player.parse_player(agent)
        self.text = other
        # NOTE: someone PLEASE fix logging this is getting ridiculous
        # NOTE: there is no reliable way of getting the second key here

    def parse_pda(self, log: str) -> None:
        """Parses a game log entry from `PDA:` onwards (PDA: should not be included)"""
        agent, other = log.split(") ", 1)
        self.agent = Player.parse_player(agent)
        # Sending a message with the message monitor console adds a "sent " FOR NO PARTICULAR REASON
        # It gets better... it also moves " to "...
        if "PDA: message monitor console" in other:
            _pda_type, other = other.split(') sent "')
            text, other = other.split('" to ', 1)
            loc_start = self.parse_and_set_location(other)
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
                loc_start = self.parse_and_set_location(location)
                self.location_name = location[:loc_start].strip()
        self.patient = Player(None, patient)
        self.text = html_unescape(text.strip())

    def parse_mecha(self, log: str) -> None:
        """Parses a game log entry from `MECHA:` onwards (MECHA: should not be included)"""
        self.text = log.strip()
        loc_start = self.parse_and_set_location(log)
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
            virus_name, other = other.split(" sym:")
            self.virus_name = virus_name
            self.text = "infected, sym:" + other.strip()
        # Location is available in both cases
        loc_start = self.parse_and_set_location(log)
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
        loc_start = self.parse_and_set_location(location)
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
        if log.startswith("Shuttle call reason:") or " set a new shuttle, " in log:
            self.text = html_unescape(log.strip())
            return

        agent, other = log.split(") ", 1)
        self.agent = Player.parse_player(agent)
        self.text = html_unescape(other.strip())

    def parse_tgui(self, log: str) -> None:
        """Parses a TGUI log without the date""" # Send help, this is a mess
        other = log

        # Just in case because sometimes we have no ckey.
        # I wonder if the logging code was made only to screw with people like me.
        agent = "*no key*/(None)"

        if " (as " in other:
            key, other = other.split(" (as ", 1)
            mob, other = other.split(" at ", 1)
            location, other = other.split(")", 1)

            #Can't use parse_and_set_location because it's a snowflake log yet again! Fun.
            self.location = tuple(int(x) for x in location.split(","))

            agent = f"{key}/({mob})"

        if " in " in other:
            something, other = other.split(" in ", 1)
            something = something.strip() # Just in case
            if something:
                # If the first branch ran, this should be empty. If it didn't then we have a ckey
                # Logging is a giant mess
                agent = f"{something}/(None)"
        self.agent = Player.parse_player(agent)

        # Set text to 'Empty' if other is empty, since we're expecting
        # extra data (newlines will get appended)
        self.text = other or "Empty"

    def parse_and_set_location(self, log: str) -> int:
        """Finds and parses a location entry. (location name (x, y, z)). Can parse a raw line.

        Returns the position of the location in the string as in integer"""
        # NOTE: this does not set location name, as it is not always present
        # Find all possible location strings
        match = re.findall(r"\(\d{1,3},\d{1,3},\d{1,2}\)", log)
        # Check if there are any results
        if not match:
            return -1
        # Get location of last match
        loc = log.index(match[-1])
        # Take the last result from the regex, remove the first and last character,
        # and turn into a list
        match = match[-1][1:-1].split(",")
        # Turn all elements to ints, convert to tuple
        self.location = tuple(int(x) for x in match) # Bad practice since it's a side effect
        return loc

    def generic_say_parse(self, log: str) -> None:
        """Parses a generic SAY log entry from SAY: onwards (includes SAY, WHISPER, OOC)
        (should only include line from SAY: onwards, without the SAY)"""
        agent, other = log.split(") ", 1) # Ensure that we didn't get a name with spaces
        self.agent = Player.parse_player(agent)
        # Priority announcements, yet another exception
        if other.startswith(("(priority announcement)", "(message to the other server)")) and \
                            '" ' not in other:
            self.text = html_unescape(other.strip())
            return
        text, other = other.split('" ', 1)
        self.text = html_unescape(text.strip('"').replace('"', '| '))
        other, location = other.split('(', 1)
        other = other.strip()
        if other:
            self.text += " | " + other

        self.is_dead = False
        if "(DEAD)" in text:
            text = text.replace("(DEAD) ", "", 1)
            self.is_dead = True
        loc_start = self.parse_and_set_location(location)
        self.location_name = location[:loc_start]

    def __str__(self):
        """String representation"""
        return self.raw_line
    def __repr__(self):
        """Object representation"""
        return self.raw_line

if __name__ == "__main__":
    single_log = Log(input())
    print(single_log)
    print(single_log.__dict__)
