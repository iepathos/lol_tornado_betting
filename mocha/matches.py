# -*- coding: utf-8 -*-
from tornado.gen import coroutine
from .services import RethinkService, if_async
from datetime import datetime
from rethinkdb import r


class MatchesService(RethinkService):
    table = 'matches'
    # players
    # score
    # time

    @if_async(coroutine)
    def new(self, id, game):
        delta = datetime.now() - datetime(1970, 1, 1)
        match = {
            'id': game['gameId'],
            'created': r.epoch_time(delta.total_seconds()),
            'completed': False,
        }
        match.update(game)
        if self.async:
            exists = yield self.exists(id)
            if exists:
                rv = yield self.update(id, match)
            else:
                rv = yield self.insert(match)
        else:
            if self.exists(id):
                rv = self.update(id, match)
            else:
                rv = self.insert(match)
        return rv


"""
Example Riot API response for featured matches gameList:

{'gameStartTime': 1458330878778, 'observers': {'encryptionKey': 'iqrxN28iApmRNOwyV8583P/bLyeuYz6H'}, 'gameLength': 153, 'gameQueueConfigId': 410,
'gameType': 'MATCHED_GAME', 'bannedChampions': [{'pickTurn': 1, 'championId': 76, 'teamId': 100}, {'pickTurn': 2, 'championId': 80, 'teamId': 200},
{'pickTurn': 3, 'championId': 41, 'teamId': 100}, {'pickTurn': 4, 'championId': 203, 'teamId': 200}, {'pickTurn': 5, 'championId': 78, 'teamId': 100},
{'pickTurn': 6, 'championId': 104, 'teamId': 200}], 'mapId': 11, 'participants': [{'summonerName': 'Minibestia', 'championId': 201, 'bot': False, 'teamId': 100,
'profileIconId': 553, 'spell2Id': 4, 'spell1Id': 14}, {'summonerName': 'Robert Morris', 'championId': 29, 'bot': False, 'teamId': 100, 'profileIconId': 756,
'spell2Id': 7, 'spell1Id': 4}, {'summonerName': 'Pomi', 'championId': 113, 'bot': False, 'teamId': 100, 'profileIconId': 986, 'spell2Id': 4, 'spell1Id': 11},
{'summonerName': 'ettelliG', 'championId': 7, 'bot': False, 'teamId': 100, 'profileIconId': 774, 'spell2Id': 14, 'spell1Id': 4}, {'summonerName': 'West Coast Carry',
'championId': 24, 'bot': False, 'teamId': 100, 'profileIconId': 1016, 'spell2Id': 12, 'spell1Id': 4}, {'summonerName': 'teradcujn', 'championId': 429, 'bot': False,
'teamId': 200, 'profileIconId': 4, 'spell2Id': 4, 'spell1Id': 7}, {'summonerName': 'migukgirl', 'championId': 245, 'bot': False, 'teamId': 200, 'profileIconId': 4,
'spell2Id': 4, 'spell1Id': 11}, {'summonerName': 'HvK Porky', 'championId': 79, 'bot': False, 'teamId': 200, 'profileIconId': 1035, 'spell2Id': 12, 'spell1Id': 4},
{'summonerName': 'King Kenneth', 'championId': 40, 'bot': False, 'teamId': 200, 'profileIconId': 786, 'spell2Id': 3, 'spell1Id': 4}, {'summonerName': 'Wolfelol',
'championId': 101, 'bot': False, 'teamId': 200, 'profileIconId': 6, 'spell2Id': 4, 'spell1Id': 7}], 'gameId': 2128807271, 'gameMode': 'CLASSIC', 'platformId': 'NA1'}
"""

