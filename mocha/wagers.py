# -*- coding: utf-8 -*-
from tornado.gen import coroutine
from .services import RethinkService, if_async
from datetime import datetime
import rethinkdb as r


class WagersService(RethinkService):
    table = 'wagers'

    @coroutine
    def new(self, user, match, team, points):
        delta = datetime.now() - datetime(1970, 1, 1)
        wager = {
            'created': r.epoch_time(delta.total_seconds()),
            'user': user,
            'match': match,
            'team': team,
            'points': points,
            'settled': False,
            'payout': 0,
            'match_data': None,
        }
        rv = yield self.insert(wager)
        return rv

    @coroutine
    def settle(self, id):
        update = yield self.update(id, {'settled': True})
        return update
