# -8- coding: utf-8 -*-
import os.path
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.escape import json_encode
from tornado.gen import coroutine
import hashlib
from tornado.log import enable_pretty_logging
from .lol import get_first_mastery_name, get_all_featured_matches
from .db import get_db_conn
from .users import UsersService
from .config import conf
from .lol_champions import get_champion_name, get_spell_name
from .matches import MatchesService
from tornado.web import authenticated
from .wagers import WagersService
import rethinkdb as r


class Application(tornado.web.Application):
    def __init__(self, db_conn):
        handlers = [
            (r"/", MainHandler),
            (r"/register", RegisterHandler),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            (r"/get_token", LoLTokenHandler),
            (r"/verify_token", LoLVerifyTokenHandler),
            (r"/set_password", SetPasswordHandler),
            (r"/make_wager", MakeWagerHandler),
            (r"/wagers", WagersHandler),
            (r"/featured", FeaturedMatchesHandler),
            (r"/points", DraftPointsHandler),
        ]
        settings = conf

        self.db = db_conn  # rethinkdb asynchronous connection
        self.users = UsersService(self.db)
        self.matches = MatchesService(self.db)
        self.wagers = WagersService(self.db)
        tornado.web.Application.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class MainHandler(BaseHandler):
    @coroutine
    def get(self):
        if not self.current_user:
            self.redirect("/register")
            return
        name = tornado.escape.xhtml_escape(self.current_user)
        matches = yield get_all_featured_matches()
        # filter by matches user has not made a wager on yet
        # save featured matches to database
        for match in matches:
            curs = yield r.table('wagers').filter({'match': int(match['gameId']), 'user': name}).count().run(self.application.db)
            if curs == 0:
                # reverse order by teamId so teamId 100 (blue) is on bottom
                match['participants'] = sorted(match['participants'], key=lambda k: k['teamId'], reverse=True)
                yield self.application.matches.new(int(match['gameId']), match)
            else:
                matches = [m for m in matches if m != match]
        user = yield self.application.users.get(name)
        self.render('index.html', current_user=name, featured_matches=matches,
                    champions=get_champion_name, spells=get_spell_name,
                    draft_points=user['draft_points'])


class FeaturedMatchesHandler(BaseHandler):
    @authenticated
    @coroutine
    def get(self):
        name = tornado.escape.xhtml_escape(self.current_user)
        matches = yield get_all_featured_matches()
        # filter by matches user has not made a wager on yet
        # save featured matches to database
        for match in matches:
            curs = yield r.table('wagers').filter({'match': int(match['gameId']), 'user': name}).count().run(self.application.db)
            if curs == 0:
                # reverse order by teamId so teamId 100 (blue) is on bottom
                match['participants'] = sorted(match['participants'], key=lambda k: k['teamId'], reverse=True)
                yield self.application.matches.new(int(match['gameId']), match)
            else:
                matches = [m for m in matches if m != match]
        self.render('featured.html', matches=matches, featured_matches=matches,
                    champions=get_champion_name, spells=get_spell_name,)


class RegisterHandler(BaseHandler):
    def get(self):
        self.render('register.html')


class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html')

    @coroutine
    def post(self):
        name = self.get_argument("name")
        password = self.get_argument('password')
        verified = yield self.application.users.verify(name, password)
        if verified:
            self.set_secure_cookie("user", name)
            self.redirect("/")
        else:
            self.write("Bad login")


class LogoutHandler(BaseHandler):
    def get(self):
        self.set_secure_cookie("user", "")
        self.redirect("/login")


class LoLTokenHandler(BaseHandler):
    @coroutine
    def post(self):
        """Called with a username, returns token in JSON dump"""
        name = self.get_argument('name')
        exists = yield self.application.users.exists(name)
        has_password = yield self.application.users.has_password(name)
        if exists and has_password:
            self.write(json_encode({'status': 'League of Legends account verified and password set already!'}))
            return
        else:
            hashtoken = hashlib.sha1(os.urandom(20)).hexdigest()[:25]
            yield self.application.users.new(name, hashtoken)

            rv = {
                'name': name,
                'token': hashtoken,
                'lolverified': False,
                'status': 'success',
            }
            self.write(json_encode(rv))


class LoLVerifyTokenHandler(BaseHandler):
    @coroutine
    def post(self):
        """Accesses the LoL API and verifies that the name of
        the given summoner's page matches the token passed"""
        name = self.get_argument('name')
        user = yield self.application.users.get(name)
        if user:
            mastery_name = get_first_mastery_name(name)
            if user['token'] == mastery_name:
                yield self.application.users.set_lolverified(name)
                self.set_secure_cookie("user", name)
                self.write(json_encode({'status': 'success'}))
                return
        self.write(json_encode({'status': 'failed to verify'}))


class SetPasswordHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect('/register')
            return
        self.render('set_password.html', user=self.current_user)

    @coroutine
    def post(self):
        if not self.current_user:
            self.redirect('/register')
            return
        name = tornado.escape.xhtml_escape(self.current_user)
        password = self.get_argument('password')
        rv = yield self.application.users.get(name)
        if rv:
            verified = rv.get('lolverified')
            if verified:
                self.application.users.set_password(name, password)
                self.redirect('/')
                return
        self.write("Failed to verify")
        return


class MakeWagerHandler(BaseHandler):
    @authenticated
    @coroutine
    def post(self):
        name = tornado.escape.xhtml_escape(self.current_user)
        match = int(self.get_argument('match'))
        team = self.get_argument('team')
        points = int(self.get_argument('points'))
        if match and team and points:
            # make sure user has enough points for wager
            user = yield self.application.users.get(name)
            if user['draft_points'] >= points:
                yield self.application.wagers.new(name, match, team, points)
                yield self.application.users.rm_points(name, points)
                self.write(json_encode({'status': 'success'}))
                return
        self.write(json_encode({'status': 'failed to make wager'}))


class WagersHandler(BaseHandler):
    @authenticated
    @coroutine
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        wagers = []
        curs = yield self.application.wagers.filter({'user': user})
        while (yield curs.fetch_next()):
            item = yield curs.next()
            wagers.append(item)
        self.render('wagers.html', wagers=wagers)


class DraftPointsHandler(BaseHandler):
    @authenticated
    @coroutine
    def get(self):
        name = tornado.escape.xhtml_escape(self.current_user)
        user = yield self.application.users.get(name)
        self.write(json_encode({'draft_points': user['draft_points']}))


@coroutine
def run_server():
    enable_pretty_logging()
    db_conn = yield get_db_conn()
    http_server = tornado.httpserver.HTTPServer(Application(db_conn))
    http_server.listen(5000, address='0.0.0.0')
