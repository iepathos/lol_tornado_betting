# -*- coding: utf-8 -*-
import logging
import threading
import rethinkdb as r
from functools import partial
from tornado.ioloop import IOLoop
from tornado.gen import coroutine
from .config import RETHINK_HOST, RETHINK_PORT, DB_NAME

log = logging.getLogger('mocha.db')

LISTENERS = []


def get_db_conn():
    """Yields a RethinkDB connection"""
    r.set_loop_type("tornado")
    try:
        conn = r.connect(host=RETHINK_HOST,
                           port=RETHINK_PORT,
                           db=DB_NAME)
    except r.RqlRuntimeError:
        conn = r.connect(host=RETHINK_HOST, port=RETHINK_PORT)
    return conn


def get_db_conn_synchronous():
    """Returns a RethinkDB connection, synchronous - mostly for testing
    and management commands."""
    try:
        conn = r.connect(host=RETHINK_HOST,
                         port=RETHINK_PORT,
                         db=DB_NAME)
    except r.RqlRuntimeError:
        conn = r.connect(host=RETHINK_HOST, port=RETHINK_PORT)
    return conn


@coroutine
def make_table(name):
    """Creates a RethinkDB table with the given name."""
    conn = yield get_db_conn()
    try:
        yield r.table_create(name).run(conn)
        log.info("Table %s created successfully." % name)
    except r.RqlRuntimeError:
        log.info("Table %s already exists... skipping." % name)


@coroutine
def setup_tables():
    yield make_table('users')
    yield make_table('matches')
    yield make_table('wagers')


def add_feed(msg, change, addition):
    """Adds an element to a given RethinkDB feed.  Returns the msg and feed."""
    if not change['old_val']:
        msg[addition] = change['new_val'][addition]
    elif change['new_val'][addition] != change['old_val'][addition]:
        msg[addition] = change['new_val'][addition]
    return msg, change


@coroutine
def rethink_listener():
    """RethinkDB listener feeds changes to the websocket listeners."""
    db_conn = yield get_db_conn()
    users = r.table('users')
    io_loop = IOLoop.instance()
    feed = yield users.changes().run(db_conn)
    while (yield feed.fetch_next()):
        change = yield feed.next()
        msg = {}
        user = change['new_val']['id']

        # user table feeds
        add_feed(msg, change, 'draft_points')

        for client in LISTENERS:
            if client.get_current_user() == user:
                io_loop.add_callback(partial(client.on_message, msg))


@coroutine
def build_tables():
    """Builds tables and then stops current IOLoop."""
    yield setup_tables()
    IOLoop.current().stop()


@coroutine
def rethink_setup():
    """Setup necessary RethinkDB tables and thread the change feed listener."""
    yield setup_tables()
    # log.info('Starting RethinkDB listener')
    # threading.Thread(target=rethink_listener).start()
    