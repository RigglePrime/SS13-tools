#!/usr/bin/env python3

from enum import Enum
from typing import Optional
from urllib.parse import quote as url_escape
from dataclasses import dataclass

import requests as req

class RoleplayLevel(Enum):
    Unknown = 0
    Low = 1
    Medium = 2
    High = 3

class BanType(Enum):
    Server = 0
    Job = 1

@dataclass(repr=True, frozen=True)
class BanData:
    id: int = -1
    sourceID: int = -1
    sourceName: Optional[str] = None
    sourceRoleplayLevel: RoleplayLevel = RoleplayLevel.Unknown
    type: BanType = BanType.Server
    cKey: Optional[str] = None
    bannedOn: str = "ERROR"
    bannedBy: Optional[str] = None
    reason: Optional[str] = None
    expires: Optional[str] = None
    unbannedBy: Optional[str] = None
    banID: Optional[str] = None
    jobs: Optional[list[str]] = None
    banAttributes: Optional[list[str]] = None
    active: bool = False

def main():
    try:
        print("Paste ckeys to search for, one per line (press CTRL + C to stop)\n")
        while True:
            ckey = input()
            r = req.get("https://centcom.melonmesa.com/ban/search/" + url_escape(ckey))
            ban_data: list[BanData] = r.json(object_hook = lambda d: BanData(**d))

            print(f"{ckey}:\n")
            if len(ban_data) == 0:
                print("No data")
            for ban in ban_data:
                print(ban.bannedOn)
                print(ban.bannedBy)
                print(ban.reason)
            print("=========================\n")
    except KeyboardInterrupt:
        print("Bye!")

if __name__ == "__main__":
    main()
