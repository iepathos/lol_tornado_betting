# -*- coding: utf-8 -*-
"""
Bookkeeper is responsible for monitoring the change
feed in matches as they complete and updating draft points
on user accounts according to any wagers made on those matches.
"""
from .matches import MatchesService
from .wagers import WagersService
from .users import UsersService
from .db import get_db_conn, get_db_conn_synchronous
from tornado.gen import coroutine
import time
from .lol import w
import logging
import rethinkdb as r
from riotwatcher.riotwatcher import LoLException


log = logging.getLogger('mocha.bookkeeper')


def update_wagers_synchronously():
    conn = get_db_conn_synchronous()
    unsettled_wagers = r.table('wagers').filter({'settled': False}).run(conn)
    for wager in unsettled_wagers:
        print('Checking wager %s on match %s' % (wager['id'], wager['match']))
        match = r.table('matches').get(int(wager['match'])).run(conn)
        if match:
            if 'completed' not in match:
                match['completed'] = False

            user = r.table('users').get(wager['user']).run(conn)
            if not match['completed']:
                try:
                    m = w.get_match(int(wager['match']))
                    # check which team won
                    winning_team = ''
                    for team in m['teams']:
                        if team['winner']:
                            winning_team = team['teamId']
                    if winning_team != '':
                        m['completed'] = True
                    r.table('matches').get(int(match['id'])).update(m).run(conn)

                    if winning_team == '100':
                        winning_team = 'Bottom'
                    else:
                        winning_team = 'Top'
                    payout = 0
                    if wager['team'] == winning_team:
                        print('Winning wager found for team %s.  Awarding draft points for wager to %s' % (wager['team'], wager['user']))
                        # award draft points
                        if match['gameMode'] == 'ARAM':
                            # award ARAM draft points .5
                            payout = int(wager['points']) + .5*int(wager['points'])
                            r.table('users').get(wager['user']).update({'draft_points': user['draft_points'] + payout}).run(conn)
                        elif match['gameMode'] == 'CLASSIC':
                            # award classic draft points 1
                            payout = 2*int(wager['points'])
                            r.table('users').get(wager['user']).update({'draft_points': user['draft_points'] + payout}).run(conn)
                    # mark wager settled
                    print("Marking wager settled")
                    r.table('wagers').get(wager['id']).update({'settled': True, 'payout': payout}).run(conn)
                except LoLException:
                    # not found
                    print("Match not found in Riot API")
            else:
                print("Match already completed, settling the wager.")
                winning_team = ''
                for team in match['teams']:
                    if team['winner']:
                        winning_team = team['teamId']

                if winning_team == '100':
                    winning_team = 'Bottom'
                else:
                    winning_team = 'Top'
                payout = 0
                if wager['team'] == winning_team:
                    print('Winning team found %s.  Awarding draft points for wager on game type %s' % (wager['team'], match['gameMode']))
                    # award draft points
                    if match['gameMode'] == 'ARAM':
                        # award ARAM draft points .5
                        payout = int(wager['points']) + .5*int(wager['points'])
                        r.table('users').get(wager['user']).update({'draft_points': user['draft_points'] + payout}).run(conn)
                    elif match['gameMode'] == 'CLASSIC':
                        # award classic draft points 1
                        payout = 2*int(wager['points'])
                        r.table('users').get(wager['user']).update({'draft_points': user['draft_points'] + payout}).run(conn)
                # mark wager settled
                print("Marking wager settled")
                r.table('wagers').get(wager['id']).update({'settled': True, 'payout': payout}).run(conn)
        else:
            print('Match not found on RethinkDB')


def bookkeeper():
    print('Checking matches of unsettled wagers and updating')
    update_wagers_synchronously()
