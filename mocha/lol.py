# -*- coding: utf-8 -*-
from tornado.gen import coroutine
from riotwatcher import RiotWatcher
from riotwatcher.riotwatcher import LoLException
from .config import LOL_API_KEY
from datetime import datetime
from tornado.concurrent import Future


w = RiotWatcher(LOL_API_KEY)


def get_summoner_masteries(summoner, region='na'):
    summoner = w.get_summoner(name=summoner)
    masteries = w.get_mastery_pages([summoner['id'], ])[str(summoner['id'])]
    return masteries


def get_first_mastery_name(summoner, region='na'):
    masteries = get_summoner_masteries(summoner, region)
    return masteries['pages'][0]['name']


def get_all_featured_matches():
    """Returns a Future with the featured games.  Should be yielded."""
    fut = Future()
    featured = w.get_featured_games()
    rv = [game for game in featured['gameList']]
    fut.set_result(rv)
    return fut


def get_featured_matches(gameLength):
    """Returns a Future with the featured games of less than or equal
    gameLength.  Should be yielded."""
    fut = Future()
    featured = w.get_featured_games()
    rv = [game for game in featured['gameList'] if int(game['gameLength']) <= int(gameLength)]
    fut.set_result(rv)
    return fut
