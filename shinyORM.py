connection = lambda: (None, None)
debug = False


class Model:
    '''
    Base class for making models inherited from it. Provides some basic functions for database object retrieval and
    manipulation. Also provides decorators which can be used for making custom object getters.

    Attributes:
        field:                  All the fields are gettable and settable as attributes.
        cnx:                    The database connection.

    Class methods:
        get(id):                Retrieve the object from the database having the given ID.
        get_by(field, value):   Retrieve an object having the given value for the given field.
        get_all():              Retrieve all the objects of the given model.

    Object methods:
        save():                 Save the object to the database.
        delete():               Delete the object from the database.
        close():                Close connection to the database.

    Decorators:
        fetch_single:           Decorator to be used for making custom functions that retrieve single object.
        fetch_multiple:         Decorator to be used for making custom functions that retrieve multiple objects.

    '''
    name = ''
    if not connection:
        print('[*] No connection getter available! Check docs for details.')
        raise Exception('No connection getter available')

    def __init__(self, **kwargs):
        self.__dict__['fields'] = self.fields
        for name, field in self.fields.items():
            try:
                field['value'] = kwargs.pop(name, field['value'])
            except KeyError:
                field['value'] = kwargs.pop(name, '')
        self.__destroy, self.cnx = connection()
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
        '''
        Save the object to the database. Usually executed after creating a new object or making some changes to an
        existing object.

        :return: The ID of the object. Int.
        '''
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
            if debug:
                print('[*] Query: ' + query)
            cursor.execute(query)
            self.cnx.commit()
        else:
            query = 'INSERT INTO `{}` '.format(self.name)
            query += '(' + ', '.join(['`{}`'.format(name) for name in self.fields]) + ') '
            query += 'VALUES '
            query += '(' + ', '.join(
                ["'{}'".format(field['value']) if field['type'] == str else str(field['value']) for name, field in
                 enumerate(self.fields)]) + '); '
            if debug:
                print('[*] Query: ' + query)
            cursor.execute(query)
            self.cnx.commit()
            self.id = cursor.lastrowid
        cursor.close()
        return self.id

    def delete(self):
        '''
        Delete the object from the database.

        :return: None
        '''
        cursor = self.cnx.cursor()
        if self.id:
            query = '''DELETE FROM `{}` WHERE id={}'''.format(self.name, self.id)
            if debug:
                print('[*] Query: ' + query)
            cursor.execute(query)
        self.cnx.commit()
        cursor.close()

    def __del__(self):
        self.close()

    def close(self):
        '''
        Close connection to the database. Call it only when you're sure you're not going to call save() or delete() on
        this object again.

        :return: None
        '''
        if self.__destroy:
            self.cnx.close()

    @classmethod
    def get(cls, id):
        '''
        Retrieve the object from the database having the given ID.

        :param id: ID of the object to be retrieved. Int.
        :return: The object retrieved having the given ID.
        '''
        __destroy, cnx = connection()
        cursor = cnx.cursor()
        query = '''SELECT * FROM `{}` WHERE id='{}';'''.format(cls.name, id)
        if debug:
            print('[*] Query: ' + query)
        cursor.execute(query)
        record = None
        for row in cursor:
            record = cls(**row)
        cursor.close()
        if __destroy:
            cnx.close()
        return record

    @classmethod
    def get_by(cls, field, value):
        '''
        Retrieve an object having the given value for the given field.

        :param field: The field name. Str.
        :param value: The value of the given field.  Str or Int.
        :return: An object having the given value for the given field.
        '''
        __destroy, cnx = connection()
        cursor = cnx.cursor()
        if type(value) == int:
            query = '''SELECT * FROM `{}` WHERE {}={};'''
        else:
            query = '''SELECT * FROM `{}` WHERE {}='{}';'''
        query = query.format(cls.name, field, value)
        if debug:
            print('[*] Query: ' + query)
        cursor.execute(query)
        record = None
        for row in cursor:
            record = cls(**row)
        cursor.close()
        if __destroy:
            cnx.close()
        return record

    @classmethod
    def get_all(cls):
        '''
        Retrieve all the objects of the given model.

        :return: List of objects of the given model.
        '''
        __destroy, cnx = connection()
        cursor = cnx.cursor()
        query = '''SELECT * FROM `{}`;'''.format(cls.name)
        if debug:
            print('[*] Query: ' + query)
        cursor.execute(query)
        records = []
        for row in cursor:
            records.append(cls(**row))
        cursor.close()
        if __destroy:
            cnx.close()
        return records

    @classmethod
    def fetch_single(cls, func):
        '''
        Decorator to be used for making custom functions that retrieve single object.

        :param func: Function which returns a valid SQL query, for selecting a record of the corresponding model.
        :return: Decorated function which returns a single object according to the query made by the input func.
        '''
        def decorated(*args, **kwargs):
            __destroy, cnx = connection()
            cursor = cnx.cursor()
            query = func(*args, **kwargs)
            if debug:
                print('[*] Query: ' + query)
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
        '''
        Decorator to be used for making custom functions that retrieve multiple objects.

        :param func: Function which returns a valid SQL query, for selecting records of the corresponding model.
        :return: Decorated function which returns a list of objects according to the query made by the input func.
        '''
        def decorated(*args, **kwargs):
            __destroy, cnx = connection()
            cursor = cnx.cursor()
            query = func(*args, **kwargs)
            if debug:
                print('[*] Query: ' + query)
            cursor.execute(query)
            records = []
            for row in cursor:
                records.append(args[0](**row))
            cursor.close()
            if __destroy:
                cnx.close()
            return records

        return decorated
