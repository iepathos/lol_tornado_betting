# -*- coding: utf-8 -*-
import re
import string
import random
from passlib.hash import pbkdf2_sha256
from itsdangerous import TimestampSigner
from .config import conf


# AUTH
def gen_random_string(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def gen_signature(data):
    """Generates a TimestampSignature using config SECRET_KEY."""
    s = TimestampSigner(conf.get('cookie_secret'))
    return s.sign(str(data))


def check_signature(signature, age):
    """Checks whether a timestamp signature is valid and under a given age."""
    s = TimestampSigner(conf.get('cookie_secret'))
    return s.unsign(signature, max_age=age)


def is_valid_email(address):
    """Returns True if given string matches valid email format."""
    if re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", address):
        return True
    return False


def encrypt(password):
    """SHA256 Encryption shortcut function."""
    hash = pbkdf2_sha256.encrypt(password, rounds=200000, salt_size=16)
    return hash


def verify(password, hash):
    """SHA256 verfication shortcut function."""
    return pbkdf2_sha256.verify(password, hash)
