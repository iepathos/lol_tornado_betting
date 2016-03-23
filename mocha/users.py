# -*- coding: utf-8 -*-
from tornado.gen import coroutine
from .utils import encrypt, verify
from .services import RethinkService, if_async
from datetime import datetime
import rethinkdb as r


class UsersService(RethinkService):
    table = 'users'

    @if_async(coroutine)
    def new(self, id, token, raw_password=None):
        old_user = {
                'token': token,
                'lolverified': False,
                'draft_points': 5000,
            }
        if raw_password is not None:
            old_user.update({'password': encrypt(raw_password)})
        else:
            old_user.update({'password': None})

        new_user = old_user
        new_user['id'] = id
        delta = datetime.now() - datetime(1970, 1, 1)
        new_user['created'] = r.epoch_time(delta.total_seconds())
        if self.async:
            exists = yield self.exists(id)
            if exists:
                rv = yield self.update(id, old_user)
            else:
                rv = yield self.insert(new_user)
        else:
            if self.exists(id):
                rv = self.update(id, old_user)
            else:
                rv = self.insert(new_user)
        return rv

    @if_async(coroutine)
    def set_lolverified(self, id):
        if self.async:
            update = yield self.update(id, {'lolverified': True})
        else:
            update = self.update(id, {'lolverified': True})
        return update

    @if_async(coroutine)
    def is_lolverified(self, id):
        if self.async:
            activated = yield self.isTrue(id, 'lolverified')
        else:
            activated = self.isTrue(id, 'lolverified')
        return activated

    @if_async(coroutine)
    def verify(self, id, password):
        """Verifies that a given password matches the stored hash."""
        if self.async:
            data = yield self.get(id)
        else:
            data = self.get(id)
        if data is not None:
            if data.get('password') is not None:
                return verify(password, data['password'])
        return False

    @if_async(coroutine)
    def set_password(self, id, raw_password):
        """Given a raw password, hashes and sets hash to new password."""
        if self.async:
            update = yield self.update(id, {'password': encrypt(raw_password)})
        else:
            update = self.update(id, {'password': encrypt(raw_password)})
        return update

    @if_async(coroutine)
    def has_password(self, id):
        if self.async:
            data = yield self.get(id)
        else:
            data = self.get(id)
        if data:
            if data.get('password') is not None:
                return True
        return False

    @if_async(coroutine)
    def add_points(self, id, points):
        if self.async:
            user = yield self.get(id)
            update = yield self.update(id, {'draft_points': user['draft_points'] + points})
        else:
            user = self.get(id)
            update = self.update(id, {'draft_points': user['draft_points'] + points})
        return update

    @if_async(coroutine)
    def rm_points(self, id, points):
        if self.async:
            user = yield self.get(id)
            update = yield self.update(id, {'draft_points': user['draft_points'] - points})
        else:
            user = self.get(id)
            update = self.update(id, {'draft_points': user['draft_points'] - points})
        return update
