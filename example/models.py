import sqlite3

import ormvana
from ormvana import Model


def connection():
    conn = sqlite3.connect('blog.db')
    conn.row_factory = sqlite3.Row
    return True, conn


ormvana.connection = connection


class User(Model):
    name = 'user'
    fields = dict()
    for field in ['email', 'first_name', 'last_name']:
        fields[field] = {'type': str}
    fields['active'] = {
        'type': int,
        'value': 0
    }


class Post(Model):
    name = 'post'
    fields = dict()
    for field in ['title', 'body']:
        fields[field] = {'type': str}
    fields['author'] = {'type': int}

    @classmethod
    @Model.fetch_multiple
    def users_posts(cls, email):
        return '''SELECT * FROM `{0}` WHERE `author`=(SELECT id from `user` WHERE email='{1}');'''.format(cls.name,
                                                                                                          email)
