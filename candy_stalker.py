#!/env/python3

import sys
from typing import Optional, Iterable, Union, Generator

from round_data import RoundData

import requests as req
from dateutil.parser import isoparse
from tqdm import tqdm

SCRUBBY_API_URL = "https://scrubby.melonmesa.com/ckey/{ckey}/receipts"
GAME_TXT_URL = "https://tgstation13.org/parsed-logs/{server}/data/logs/{year}/{month}/{day}/round-{round_id}/game.txt"

# Maybe add async support in the future some day?
def get_rounds(ckey: str, number_of_rounds: int, only_played: bool = False) -> list[RoundData]:
    """Calls the scrubby API and retrieves the specified number of rounds  """
    data = {
        "ckey": ckey,
        "startingRound": 999999, # that's how scrubby does it, sue Bobbah, not me
        "limit": number_of_rounds
    }
    # ckey is specified twice, but it seems like the url ckey does not matter at all
    r = req.post(SCRUBBY_API_URL.format(ckey=ckey), json=data)

    if not r.ok: raise Exception("Scrubby errored with code " + str(r.status_code))
    if r.content == b"[]": raise Exception("CKEY could not be found")
    if not only_played:
        return RoundData.from_scrubby_response(r)

    played_in = []
    while True:
        rounds = RoundData.from_scrubby_response(r)
        if not rounds: return played_in
        for round in rounds:
            if round.playedInRound: played_in.append(round)
            if len(played_in) == number_of_rounds: return played_in
        data["startingRound"] = rounds[-1].roundID
        r = req.post(SCRUBBY_API_URL.format(ckey=ckey), json=data)

## Why do it this convoluted way? It's easier to write code around it this way. I think.
def get_say_logs(rounds: Iterable[RoundData], output_bytes: bool = False) -> Generator[tuple[RoundData, Optional[list[Union[bytes, str]]]], None, None]:
    """This is a generator that yields a tuple of the `RoundData` and list of round logs, for all rounds in `rounds`
    
    if `output_bytes` is true, the function will instead yield `bytes` instead of `str`
    
    On 404, the list will be None instead"""
    for round in rounds:
        round.timestamp = isoparse(round.timestamp)
        # Edge case warning: if we go beyond the year 2017 or so, the logs path changes. I don't expect anyone to go that far so I won't be doing anything about it
        r = req.get(GAME_TXT_URL.format(
            server = round.server.lower().replace('bagil','basil'),
            year = str(round.timestamp.year),
            month = f"{round.timestamp.month:02d}",
            day = f"{round.timestamp.day:02d}",
            round_id = round.roundID
        ))
        if r.status_code == 404:
            yield round, None
        else:
            if output_bytes:
                yield round, r.content.split(b"\r\n")
            else:
                yield round, r.text.split("\r\n")

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
        if len(sys.argv) > 3:
            output_path = sys.argv[3] 
        if len(sys.argv) > 4:
            only_played = sys.argv[4]
        default(ckey, number_of_rounds, output_path, only_played)
    elif len(sys.argv) != 1:
        print("Unknown number of command line arguments")
        print("USAGE: candy-stalker.py <ckey> [number_of_rounds=30] [output_path={ckey}.txt] [only_played=false]")
        print("<> are required, [] are optional, = means a default value. If you provide an optional, you have to also provide all optionals before it")
        exit(1)
    else:
        interactive()

def interactive() -> tuple[str, int, str, bool]:
    """Run interactive mode. Returns the choices and runs default behaviour
    
    Returns this tuple: `(ckey, number_of_rounds, output_path, only_played)`"""
    if True:
        ckey = input("CKEY: ").strip()
        number_of_rounds = input("How many rounds? [30] ")
        try:
            if not number_of_rounds: number_of_rounds = "30"
            number_of_rounds = int(number_of_rounds)
        except:
            print("Rounds should be an int")
            exit(1)
        only_played = input("Do you want to get only rounds in which they played? [y/N] ")
        output_path = input(f"Where should I write the file? [{ckey}.txt] ")
    only_played = True if only_played.lower() == 'y' or 'yes' or 'true' or '1' else False
    if not output_path: output_path = f"{ckey}.txt"
    default(ckey, number_of_rounds, output_path, only_played)
    return ckey, number_of_rounds, output_path, only_played

def default(ckey: str, number_of_rounds: int, output_path: str, only_played: bool):
    """Default behaviour of the application, downloads the file to `output_path`."""
    print(f"Fetching rounds {ckey} has participated in. This might take a second, especially if the number of rounds is large")
    rounds = get_rounds(ckey=ckey, number_of_rounds=number_of_rounds, only_played=only_played)
    print("Got rounds. Parsing...")

    with open(output_path, 'wb') as f:
        ckey = ckey.encode("utf-8")
        pbar = tqdm(get_say_logs(rounds, output_bytes = True), total = number_of_rounds)
        for round, logs in pbar:
            # Type hints
            round: RoundData
            logs: list[bytes]

            pbar.set_description(f"Getting ID {round.roundID} on {round.server}")
            if not logs: 
                print(f"WARNING: Could not find round {round.roundID} on {round.server}")
                continue
            if round.roundStartSuicide: 
                print(f"WARNING: round start suicide in round {round['roundID']} on {round['server']}")
            for line in get_lines_with_ckey(ckey, logs):
                f.write(format_line_bytes(line, round))
        
    print("Done! Good luck with getting them candidated!")

if __name__ == "__main__":
    main()