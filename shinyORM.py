get_connection = lambda: (None, None)
debug = False


class Model:
    name = ''
    if not get_connection:
        print('[*] No connection getter available! Check docs for details.')
        raise Exception('No connection getter available')

    def __init__(self, **kwargs):
        self.__dict__['fields'] = self.fields
        for name, field in self.fields.items():
            try:
                field['value'] = kwargs.pop(name, field['value'])
            except KeyError:
                field['value'] = kwargs.pop(name, '')
        self.__destroy, self.cnx = get_connection()
        self.id = kwargs.pop('id', '')

    def __getattr__(self, item):
        if item in self.fields:
            return self.fields[item]['value']
        else:
            message = '{} objects do not have any "{}" attribute!'.format(type(self).__name__, item)
            raise AttributeError(message)

    def __setattr__(self, key, value):
        if key in self.fields:
            self.fields[key]['value'] = value
        else:
            super().__setattr__(key, value)

    def __repr__(self):
        ret = {
            'id': self.id,
            'cnx': self.cnx,
        }
        for key, value in self.fields.items():
            ret[key] = value['value']
        return str(ret)

    def __str__(self):
        return '{} object with ID: {}'.format(type(self).__name__, self.id)

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
        if self.__destroy:
            self.cnx.close()

    @classmethod
    def get(cls, id):
        __destroy, cnx = get_connection()
        cursor = cnx.cursor()
        query = '''SELECT * FROM `{}` WHERE id='{}';'''
        cursor.execute(query.format(cls.name, id))
        record = None
        for row in cursor:
            record = cls(**row)
        cursor.close()
        if __destroy:
            cnx.close()
        return record

    @classmethod
    def get_by(cls, field, value):
        __destroy, cnx = get_connection()
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
        if __destroy:
            cnx.close()
        return record

    @classmethod
    def get_all(cls):
        __destroy, cnx = get_connection()
        cursor = cnx.cursor()
        query = '''SELECT * FROM `{}`;'''
        cursor.execute(query.format(cls.name))
        records = []
        for row in cursor:
            records.append(cls(**row))
        cursor.close()
        if __destroy:
            cnx.close()
        return records

    @classmethod
    def fetch_single(cls, func):
        def decorated(*args, **kwargs):
            __destroy, cnx = get_connection()
            cursor = cnx.cursor()
            query = func(*args, **kwargs)
            cursor.execute(query)
            record = None
            for row in cursor:
                record = cls(**row)
            cursor.close()
            if __destroy:
                cnx.close()
            return record

        return decorated

    @classmethod
    def fetch_multiple(cls, func):
        def decorated(*args, **kwargs):
            __destroy, cnx = get_connection()
            cursor = cnx.cursor()
            query = func(*args, **kwargs)
            cursor.execute(query)
            records = []
            for row in cursor:
                records.append(args[0](**row))
            cursor.close()
            if __destroy:
                cnx.close()
            return records

        return decorated
