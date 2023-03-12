LOC_REGEX = r"\(\d{1,3},\d{1,3},\d{1,2}\)"
ADMIN_STAT_CHANGE = r"((re-)|(de))?adminn?ed "
ADMIN_BUILD_MODE = r"has (entered|left) build mode."
HORRIBLE_HREF = r"<a href='\?priv_msg=\w+'>([\w ]+)<\/a>\/\((.+)\)"
GAME_I_LOVE_BOMBS = r"The (?:self-destruct device|syndicate bomb) that (.+) had primed detonated!"
ADMINPRIVATE_NOTE = r"(.+) has (created|deleted) a (note|message|watchlist entry) for (.+): (.*)"
ADMINPRIVATE_BAN = r"(.+) has ((?:un)?banned) (.+) from (.+)"

LOG_PRETTY_STR = r'"(?:.*)"'
LOG_PRETTY_LOC = LOC_REGEX
LOG_PRETTY_PATH = r"(?:\/\w+)+\w+"
