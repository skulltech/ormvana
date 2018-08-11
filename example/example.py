import MySQLdb
import MySQLdb.cursors
import yaml

import shinyORM
from shinyORM import Model


with open('secrets.yaml') as f:
    secrets = yaml.load(f)


def connect(db=None):
    return MySQLdb.connect(
        user=secrets['DBServer']['Username'],
        passwd=secrets['DBServer']['Password'],
        host=secrets['DBServer']['Hostname'],
        db=db or secrets['DBServer']['DB'],
        cursorclass=MySQLdb.cursors.DictCursor,
        use_unicode=True,
        charset='utf8')


shinyORM.get_connection = connect


class User(Model):
    name = 'user'
    fields = {
        'active': {
            'type': int,
            'value': 0
        }
    }
    for field in ['username', 'email', 'first_name', 'last_name']:
        fields[field] = {'type': str}


class Post(Model):
    name = 'post'
    fields = {
        'author': {'type': int}
    }
    for field in ['title', 'body']:
        fields[field] = {'type': str}

    @classmethod
    @Model.fetch_multiple
    def users_posts(cls, user_id):
        return '''SELECT * FROM `{0}` WHERE `author`={1}'''.format(cls.name, user_id)
