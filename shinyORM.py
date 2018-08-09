from flask import g

from config import connect


class Model:
    name = ''

    def __init__(self, **kwargs):
        self.to_destroy, self.cnx = get_connection()
        self.fields = {}
        self.id = kwargs.pop('id', '')

    def save(self):
        cursor = self.cnx.cursor()
        if self.id:
            query = 'UPDATE `{}` set '.format(self.name)
            for name, field in self.fields.items():
                if field['type'] == str:
                    query += '''`{}` = '{}', '''.format(name, field['value'])
                elif field['type'] == int:
                    query += '''`{}` = {}, '''.format(name, field['value'])
            query = query[:-2] + ' '
            query += 'WHERE id={};'.format(self.id)
            print(query)
            cursor.execute(query)
            self.cnx.commit()
        else:
            query = 'INSERT INTO `{}` '.format(self.name)
            query += '(' + ', '.join(['`{}`'.format(name) for name in self.fields]) + ') '
            query += 'VALUES '
            print(self.fields)
            query += '(' + ', '.join(
                ["'{}'".format(field['value']) if field['type'] == str else str(field['value']) for name, field in
                 enumerate(self.fields)]) + '); '
            print(query)
            cursor.execute(query)
            self.cnx.commit()
            self.id = cursor.lastrowid
        cursor.close()
        return self.id

    def delete(self):
        cursor = self.cnx.cursor()
        if self.id:
            query = '''DELETE FROM `{}` WHERE id={}'''
            cursor.execute(query.format(self.name, self.id))
        self.cnx.commit()
        cursor.close()

    def __del__(self):
        self.close()

    def close(self):
        if self.to_destroy:
            self.cnx.close()

    @classmethod
    def get(cls, id):
        to_destroy, cnx = get_connection()
        cursor = cnx.cursor()
        query = '''SELECT * FROM `{}` WHERE id='{}';'''
        cursor.execute(query.format(cls.name, id))
        record = None
        for row in cursor:
            record = cls(**row)
        cursor.close()
        if to_destroy:
            cnx.close()
        return record

    @classmethod
    def get_by(cls, field, value):
        to_destroy, cnx = get_connection()
        cursor = cnx.cursor()
        if type(value) == int:
            query = '''SELECT * FROM `{}` WHERE {}={};'''
        else:
            query = '''SELECT * FROM `{}` WHERE {}='{}';'''
        cursor.execute(query.format(cls.name, field, value))
        record = None
        for row in cursor:
            record = cls(**row)
        cursor.close()
        if to_destroy:
            cnx.close()
        return record

    @classmethod
    def get_all(cls):
        to_destroy, cnx = get_connection()
        cursor = cnx.cursor()
        query = '''SELECT * FROM `{}`;'''
        cursor.execute(query.format(cls.name))
        records = []
        for row in cursor:
            records.append(cls(**row))
        cursor.close()
        if to_destroy:
            cnx.close()
        return records

    @classmethod
    def fetch_single(cls, func):
        def decorated(*args, **kwargs):
            to_destroy, cnx = get_connection()
            cursor = cnx.cursor()
            query = func(*args, **kwargs)
            cursor.execute(query)
            record = None
            for row in cursor:
                record = cls(**row)
            cursor.close()
            if to_destroy:
                cnx.close()
            return record
        return decorated

    @classmethod
    def fetch_multiple(cls, func):
        def decorated(*args, **kwargs):
            to_destroy, cnx = get_connection()
            cursor = cnx.cursor()
            query = func(*args, **kwargs)
            cursor.execute(query)
            records = []
            for row in cursor:
                records.append(cls(**row))
            cursor.close()
            if to_destroy:
                cnx.close()
            return records
        return decorated


def get_connection():
    try:
        cnx = g.pop('cnx', None)
    except RuntimeError:
        return True, connect()
    if cnx:
        return False, cnx
    return True, connect()
