LOC_REGEX = r"\(\d{1,3},\d{1,3},\d{1,2}\)"
ADMIN_OSAY_EXP = r"made the ((?:\w+ ?)+) at ((?:\w+ ?)+) " + LOC_REGEX + r" say \"(.*)\"$"
ADMIN_STAT_CHANGE = r"((re-)|(de))?adminn?ed "
ADMIN_BUILD_MODE = r"has (entered|left) build mode."
