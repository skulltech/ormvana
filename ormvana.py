from copy import deepcopy


def connection():
    """
    Function that provide the SQL connection to be uses by the ORM.

    Returns
    -------
    (bool, SQL connection object)
        The first element of the tuple indicates whether the connection is to be closed after every query. The second
        element should provide an SQL connection object compliant with PEP-249.
    """
    return None, None


#: bool: Setting `debug` to `True` will make `ormvana` print each SQL query it's about to execute.
debug = True


class Model:
    """
    Base class for making models inherited from it.

    Base class for making models inherited from it. Provides some basic functions for database object retrieval and
    manipulation. Also provides decorators which can be used for making custom object getters.

    Attributes
    ----------
    cnx: SQL connection object
        SQL connection object compliant with PEP-249.
    """
    #: str: Name of the database table this `Model` corresponds to.
    name = ''
    if not connection:
        raise Exception('No SQL connection getter available')
    if not callable(connection):
        raise Exception('The provided SQL connection getter is not a callable')

    def __init__(self, **kwargs):
        self.__dict__['record'] = deepcopy(self.fields)  # To avoid RecursionError while setting property "record"
        for name, field in self.fields.items():
            self.record[name]['value'] = kwargs.pop(name, field.pop('value', ''))
        self.__destroy, self.cnx = connection()
        self.id = kwargs.pop('id', '')

    def __getattr__(self, item):
        if item in self.record:
            return self.record[item]['value']
        else:
            message = '{} objects do not have any "{}" attribute!'.format(type(self).__name__, item)
            raise AttributeError(message)

    def __setattr__(self, key, value):
        if key in self.record:
            self.record[key]['value'] = value
        else:
            super().__setattr__(key, value)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __repr__(self):
        ret = {
            'id': self.id,
            'cnx': self.cnx,
        }
        for key, value in self.record.items():
            ret[key] = value['value']
        return str(ret)

    def __str__(self):
        return '{} object with ID: {}'.format(type(self).__name__, self.id)

    def save(self):
        """
        Save the object to the database. Usually executed after creating a new object or making some changes to an
        existing object.

        Returns
        -------
        int
            The ID of the object
        """
        cursor = self.cnx.cursor()
        if self.id:
            query = 'UPDATE `{}` set '.format(self.name)
            for name, field in self.record.items():
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
            query += '(' + ', '.join(['`{}`'.format(name) for name in self.record]) + ') '
            query += 'VALUES '
            query += '(' + ', '.join(
                ["'{}'".format(field['value']) if field['type'] == str else str(field['value']) for name, field in
                 self.record.items()]) + '); '
            if debug:
                print('[*] Query: ' + query)
            cursor.execute(query)
            self.cnx.commit()
            self.id = cursor.lastrowid
        cursor.close()
        return self.id

    def delete(self):
        """
        Delete the object from the database.
        """
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
        """
        Close connection to the database. Call it only when you're sure you're not going to call save() or delete() on
        this object again.
        """
        if self.__destroy:
            self.cnx.close()

    @classmethod
    def get(cls, id):
        """
        Retrieve the object from the database having the given ID.

        Parameters
        ----------
        id : int
            ID of the object to be retrieved.

        Returns
        -------
        `Model` object
            The object retrieved having the given ID.
        """
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
        """
        Retrieve records having the given value for the given field.

        Parameters
        ----------
        field : str
            The field name.
        value: int or str
            The value of the given field.

        Returns
        -------
        `Model` object
            An object having the given value for the given field.
        """
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
        records = []
        for row in cursor:
            records.append(cls(**row))
        cursor.close()
        if __destroy:
            cnx.close()
        return records

    @classmethod
    def get_all(cls):
        """
        Retrieve all the objects of the given model.

        Returns
        -------
        list of `Model` object
            List of objects of the given model.
        """
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
        """
        Decorator to be used for making custom functions that retrieve single object.

        Parameters
        ----------
        func : function
            Function which returns a valid SQL query, for selecting a record of the corresponding model.

        Returns
        -------
        function
            Decorated function which returns a single object according to the query made by the input func.
        """

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
        """
        Decorator to be used for making custom functions that retrieve multiple objects.

        Parameters
        ----------
        func : function
            Function which returns a valid SQL query, for selecting records of the corresponding model.

        Returns
        -------
        function
            Decorated function which returns a list of objects according to the query made by the input func.
        """

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
