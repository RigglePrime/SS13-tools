#!/env/python3

from datetime import datetime
import sys
from typing import Optional, Iterable, Union, Generator

from round_data import RoundData

from aiohttp import ClientSession
import asyncio
from dateutil.parser import isoparse
from tqdm.asyncio import tqdm
from colorama import Fore, Style, init as colorama_init

SCRUBBY_API_URL = "https://scrubby.melonmesa.com/ckey/{ckey}/receipts"
SCRUBBY_ROUND_SOURCE_URL = "https://scrubby.melonmesa.com/round/{round_id}/source"
GAME_TXT_URL = "https://tgstation13.org/parsed-logs/{server}/data/logs/{year}/{month}/{day}/round-{round_id}/{file_name}"
GAME_TXT_ADMIN_URL = "https://tgstation13.org/raw-logs/{server}/data/logs/{year}/{month}/{day}/round-{round_id}/{file_name}"
DEFAULT_NUMBER_OF_ROUNDS = 150
DEFAULT_OUTPUT_PATH = "{ckey}.txt"
DEFAULT_ONLY_PLAYED = False

# Maybe add async support in the future some day?
async def get_rounds(ckey: str, number_of_rounds: int, only_played: bool = False) -> list[RoundData]:
    """Calls the scrubby API and retrieves the specified number of rounds  """
    data = {
        "ckey": ckey,
        "startingRound": 999999, # that's how scrubby does it, sue Bobbah, not me
        "limit": number_of_rounds
    }
    # ckey is specified twice, but it seems like the url ckey does not matter at all
    async with ClientSession() as session:
        r = await session.post(SCRUBBY_API_URL.format(ckey=ckey), json=data)
        if not r.ok: raise Exception("Scrubby errored with code " + str(r.status))
        if await r.read() == b"[]": raise Exception("CKEY could not be found")
        if not only_played:
            return await RoundData.from_scrubby_response_async(r)

        played_in = []
        while True:
            rounds = await RoundData.from_scrubby_response_async(r)
            if not rounds: return played_in
            for round in rounds:
                if round.playedInRound: played_in.append(round)
                if len(played_in) == number_of_rounds: return played_in
            data["startingRound"] = rounds[-1].roundID
            r = await session.post(SCRUBBY_API_URL.format(ckey=ckey), json=data)

# Why do it this convoluted way? It's easier to write code around it this way. I think.
# output_bytes is here because removing it is considered a breaking change and I'd have to increment the major version number
async def get_logs_async(rounds: Iterable[RoundData], files: list[str] = ["game.log"], \
        output_bytes: bool = False, tgforums_cookie: str = "", user_agent: str = "Riggle's admin tools") \
            -> Generator[tuple[RoundData, Optional[list[Union[bytes, str]]]], None, None]:
    """This is a generator that yields a tuple of the `RoundData` and list of round logs, for all rounds in `rounds`

    if `output_bytes` is true, the function will instead yield `bytes` instead of `str`

    On 404, the list will be None instead"""
    async with ClientSession(cookies={"tgforums_sid": tgforums_cookie}, headers={"User-Agent": user_agent}) as session:
        tasks = []
        url_to_use = GAME_TXT_URL

        async def fetch(round: RoundData):
            round.timestamp = isoparse(round.timestamp)
            responses = []
            for file in files:
                # Edge case warning: if we go beyond the year 2017 or so, the logs path changes.
                # I don't expect anyone to go that far so I won't be doing anything about it
                async with session.get(url_to_use.format(
                    server = round.server.lower().replace('bagil','basil'),
                    year = str(round.timestamp.year),
                    month = f"{round.timestamp.month:02d}",
                    day = f"{round.timestamp.day:02d}",
                    round_id = round.roundID,
                    file_name = file)) as r:
                    if not r.ok:
                        continue
                    responses.append(await r.read())
                return round, b'\r\n'.join(responses)

        if tgforums_cookie and user_agent:
            url_to_use = GAME_TXT_ADMIN_URL
            round, response = await fetch(rounds[0])
            if not response:
                print(f"{Fore.RED}ERROR: The cookie and user agent were set but invalid, reverting to normal logs.")
                url_to_use = GAME_TXT_URL

        for round in rounds:
            tasks.append(asyncio.ensure_future(fetch(round=round)))

        for task in tasks:
            round, response = await task
            response: bytes
            if not response:
                yield round, None
            else:
                yield round, response.split(b"\r\n")

        await asyncio.gather(*tasks)

async def get_round_range(start_round: int, end_round: int, output_path: str = "rounds.log", files: list[str] = ["game.log"],\
    tgforums_cookie: str = "", user_agent: str = "Riggle's admin tools"):
    """Gets a range of rounds from the servers and writes them to a file"""
    round_ids = range(start_round, end_round + 1)
    
    rounds = []
    async with ClientSession(cookies={"tgforums_sid": tgforums_cookie}, headers={"User-Agent": user_agent}) as session:
        tasks = [asyncio.ensure_future(fetch_one(round_id)) for round_id in round_ids]
        async def fetch_one(round_id):
            async with session.get(SCRUBBY_ROUND_SOURCE_URL.format(round_id=round_id), allow_redirects=False) as r:
                if not r.ok:
                    print(f"Round ID {round_id} returned {r.status}, skipping")
                    return None
                assert r.status == 302
                # At this point I can't be bothered to refactor anything, sorry
                # You will have to bear with me and my bad code
                loc = r.headers['Location']
                # The numbers here are just lengths of the strings. Find returns the start of the argument str
                # and we need to jump to the end of it
                timestamp = datetime.strptime(loc[loc.find("logs/")+5:loc.find("/round")], "%y/%d/%m")
                server_name = loc[loc.find("parsed-logs/")+12:loc.find("/data/logs")]
                return RoundData(round_id, timestamp=timestamp, server=server_name)

        for task in tasks:
            value = await task
            if value:
                rounds.append(value)
        await asyncio.gather(*tasks)

    with open(output_path, 'wb') as f:
        pbar = tqdm(get_logs_async(rounds, files=files, tgforums_cookie=tgforums_cookie, user_agent=user_agent))
        async for round, logs in pbar:
            round: RoundData
            pbar.set_description(f"Getting ID {round.roundID} on {round.server}")
            for line in logs:
                f.write(format_line_bytes(line, round))

def get_lines_with_ckey(ckey: Union[str, bytes], lines: Iterable[Union[str, bytes]]):
    """Filters lines without the specified ckey out. Make sure that `ckey` and members of `lines` are of the same type"""
    for line in lines:
        if ckey.lower() in line.lower(): 
            yield line

def format_line_str(line: str, round: RoundData) -> list[str]:
    """Takes the raw line and formats it to `{server_name} {round_id} | {unmodified line}`"""
    return round.server + " " + str(round.roundID) + " | " + line + "\n"
def format_line_bytes(line: bytes, round: RoundData) -> list[str]:
    """Takes the raw line and formats it to `{server_name} {round_id} | {unmodified line}`"""
    return round.server.encode("utf-8") + b" " + str(round.roundID).encode("utf-8") + b" | " + line + b"\n"

def main():
    if 2 < len(sys.argv) < 6:
        ckey = sys.argv[1]
        number_of_rounds = int(sys.argv[2])
        output_path = DEFAULT_OUTPUT_PATH.format(ckey=ckey)
        if len(sys.argv) > 3:
            output_path = sys.argv[3]
        only_played = DEFAULT_ONLY_PLAYED
        if len(sys.argv) > 4:
            only_played = sys.argv[4]
        default(ckey, number_of_rounds, output_path, only_played)
    elif len(sys.argv) != 1:
        print(f"{Fore.YELLOW}Unknown number of command line arguments{Fore.RESET}")
        print(f"{Fore.GREEN}USAGE{Fore.RESET}: candy-stalker.py <ckey> [number_of_rounds={DEFAULT_NUMBER_OF_ROUNDS}] [output_path={ckey}.txt] [only_played=false]")
        print("<> are required, [] are optional, = means a default value. If you provide an optional, you have to also provide all optionals before it")
        exit(1)
    else:
        interactive()

def interactive() -> tuple[str, int, str, bool]:
    """Run interactive mode. Returns the choices and runs default behaviour
    
    Returns this tuple: `(ckey, number_of_rounds, output_path, only_played)`"""
    ckey = input("CKEY: ").strip()
    while True:
        number_of_rounds = input("How many rounds? [%d] " % DEFAULT_NUMBER_OF_ROUNDS)
        try:
            number_of_rounds = int(number_of_rounds) if number_of_rounds.isdigit() else DEFAULT_NUMBER_OF_ROUNDS
            break
        except ValueError:
            print(f"{Fore.RED}Rounds should be an int{Fore.RESET}")
    print(f"Do you want to get only rounds in which they played? [y/{Style.BRIGHT}N{Style.RESET_ALL}] ", end="")
    only_played = input() # Input and colorama don't mix
    output_path = input(f"Where should I write the file? [{ckey}.txt] ")
    if not only_played:
        only_played = DEFAULT_ONLY_PLAYED
    else:
        only_played = True if only_played.lower() == 'y' or 'yes' or 'true' or '1' else False
    if not output_path: output_path = DEFAULT_OUTPUT_PATH.format(ckey=ckey)
    default(ckey, number_of_rounds, output_path, only_played)
    return ckey, number_of_rounds, output_path, only_played

async def default_async(ckey: str, number_of_rounds: int, output_path: str, only_played: bool):
    """Default behaviour of the application, downloads the file to `output_path`."""
    print(f"Fetching rounds {Style.BRIGHT}{ckey}{Style.RESET_ALL} has participated in. This might take a second, especially if the number of rounds is large")
    rounds = await get_rounds(ckey=ckey, number_of_rounds=number_of_rounds, only_played=only_played)
    print("Got rounds. Parsing...")

    with open(output_path, 'wb') as f:
        ckey = ckey.encode("utf-8")
        pbar = tqdm(get_logs_async(rounds))
        async for round, logs in pbar:
            # Type hints
            round: RoundData
            logs: list[bytes]

            pbar.set_description(f"Getting ID {round.roundID} on {round.server}")
            if not logs: 
                pbar.clear()
                print(f"{Fore.YELLOW}WARNING:{Fore.RESET} Could not find round {round.roundID} on {round.server}")
                pbar.display()
                continue
            if round.roundStartSuicide:
                pbar.clear()
                print(f"{Fore.MAGENTA}WARNING:{Fore.RESET} round start suicide in round {round.roundID} on {round.server}")
                pbar.display()
            for line in get_lines_with_ckey(ckey, logs):
                f.write(format_line_bytes(line, round))

    print("Done! Good luck with getting them candidated!")

def default(ckey: str, number_of_rounds: int, output_path: str, only_played: bool):
    if sys.platform == "win32":
        # This fixes a lot of runtime errors.
        # It's supposed to be fixed but oh well.
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(default_async(ckey=ckey, number_of_rounds=number_of_rounds, output_path=output_path, only_played=only_played))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

if __name__ == "__main__":
    colorama_init()
    main()
