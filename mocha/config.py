# -*- coding: utf-8 -*-
import os


conf = dict(
    template_path=os.path.join(os.path.dirname(__file__), "templates"),
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    debug=True,
    cookie_secret='partytimefunfun',
)

# rethinkdb://dokku-rethinkdb-mochadick:28015
RETHINK_HOST = os.environ.get('RETHINKDB_HOST', 'localhost')
RETHINK_PORT = os.environ.get('RETHINKDB_PORT', '28015')
DB_NAME = os.environ.get('RETHINKDB_DB_NAME', 'test')


LOL_API_KEY = os.environ.get('LOL_API_KEY', '')
