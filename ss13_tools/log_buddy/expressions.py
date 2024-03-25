import re


LOC_REGEX = re.compile(r"\(\d{1,3},\d{1,3},\d{1,2}\)")
ADMIN_STAT_CHANGE_REGEX = re.compile(r"((re-)|(de))?adminn?ed ")
ADMIN_BUILD_MODE_REGEX = re.compile(r"has (entered|left) build mode.")
HORRIBLE_HREF_REGEX = re.compile(r"<a href='\?priv_msg=\w+'>([\w ]+)<\/a>\/\((.+)\)")
GAME_I_LOVE_BOMBS_REGEX = re.compile(r"The (?:self-destruct device|syndicate bomb) that (.+) had primed detonated!")
ADMINPRIVATE_NOTE_REGEX = re.compile(r"(.+) has (created|deleted) a (note|message|watchlist entry) for (.+): (.*)")
ADMINPRIVATE_BAN_REGEX = re.compile(r"(.+) has ((?:un)?banned) (.+) from (.+)")
VIRUS_CULTURE_PRINT_REGEX = re.compile(r"^A culture (?:bottle|tube) was printed for the virus (.+)")
VIRUS_INFECTED_OR_CURED_REGEX = re.compile(r" was (?:infected by|cured of) virus: ")
COMBAT_MODE_REGEX = re.compile(r"\(COMBAT MODE: (\d)\)")
DAMTYPE_REGEX = re.compile(r"\(DAMTYPE: (\w+)\)")
NEW_HP_REGEX = re.compile(r"\(NEWHP: (-?\d+\.?\d?)\)")

LOG_PRETTY_STR = re.compile(r'"(?:.*)"')
LOG_PRETTY_LOC = LOC_REGEX
LOG_PRETTY_PATH = re.compile(r"(?:\/\w+)+\w+")
