#!/usr/bin/env python
# -*- coding: utf-8 -*-
import code
import logging
import argparse
from tornado.ioloop import IOLoop
from mocha.server import run_server
from mocha.db import build_tables, rethink_setup, \
                        get_db_conn_synchronous
# from seahorse.auth.management import add_user, delete_user, activate_user
from mocha.users import UsersService
import rethinkdb as r
from mocha.matches import MatchesService
from mocha.match_sync import match_update
from mocha.bookkeeper import bookkeeper


__author__ = 'Glen Baker <iepathos@gmail.com>'
__version__ = '0.6-dev'


log = logging.getLogger('seahorse')


class AppContext(object):

    def __init__(self):
        self.r = r
        self.db_conn = get_db_conn_synchronous()
        self.users = UsersService(self.db_conn, async=False)
        self.matches = MatchesService(self.db_conn, async=False)


def open_shell():
    """Opens an interactive shell with application context.
    Available Context Variables:
    db_conn - an open synchronous RethinkDB connection
    users - synchronous RethinkDB UsersService
    matches - synchronous RethinkDB MatchesService
    """
    app_ctx = AppContext()
    shell_ctx = globals()
    shell_ctx.update(vars(app_ctx))
    code.interact(local=shell_ctx)
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            description='Mocha Dick is an Asynchronous Whale'
        )
    parser.add_argument('-r', '--run', dest='run', action='store_true',
                        help='Runs the server.')
    parser.add_argument('--build_tables', dest='build_tables',
                        action='store_true', help='Build RethinkDB tables.')

    parser.add_argument('-s', '--shell', dest='shell',
                        action='store_true', help='Open an application shell.')

    parser.add_argument('-b', '--book', dest='book',
                        action='store_true', help='Run Bookkeeper to track and settle wagers')

    args = parser.parse_args()
    if args.run:
        rethink_setup()
        IOLoop.current().run_sync(run_server)
        IOLoop.current().start()
    elif args.build_tables:
        IOLoop.current().run_sync(build_tables)
    elif args.book:
        bookkeeper()
    elif args.shell:
        open_shell()
    else:
        parser.print_help()
