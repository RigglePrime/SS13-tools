from .round_data import RoundData
from .constants import PLAYER_ROUNDS_URL
from ..constants import USER_AGENT

from aiohttp import ClientSession


async def get_rounds_for_ckey(ckey: str, number_of_rounds: int, only_played: bool = False) -> list[RoundData]:
    """Calls the scrubby API and retrieves the specified number of rounds  """
    data = {
        "ckey": ckey,
        "startingRound": 999999,  # that's how scrubby does it, sue Bobbah, not me
        "limit": number_of_rounds
    }
    # ckey is specified twice, but it seems like the url ckey does not matter at all
    # https://github.com/bobbahbrown/ScrubbyWebPublic/blob/d71ad368e156f56524bf7ec323685ca29af35baa/Controllers/CKeyController.cs#L78
    async with ClientSession(headers={"User-Agent": USER_AGENT}) as session:
        r = await session.post(PLAYER_ROUNDS_URL.format(ckey=ckey), json=data)
        if not r.ok:
            raise Exception("Scrubby errored with code " + str(r.status))
        if await r.read() == b"[]":
            raise Exception("CKEY could not be found")
        if not only_played:
            return await RoundData.from_scrubby_response_async(r)

        played_in = []
        while True:
            rounds = await RoundData.from_scrubby_response_async(r)
            if not rounds:
                return played_in
            for round in rounds:
                if round.playedInRound:
                    played_in.append(round)
                if len(played_in) == number_of_rounds:
                    return played_in
            data["startingRound"] = rounds[-1].roundID
            r = await session.post(PLAYER_ROUNDS_URL.format(ckey=ckey), json=data)


async def get_round_source_url(id: int):
    pass
