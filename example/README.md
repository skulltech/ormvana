## Tutorial

I'm going to demonstrate the usage of this module using a blog application, containing two tables: users and posts. You 
can find the complete example [here](https://github.com/SkullTech/ormvana/tree/master/example/).

### Defining the models

To get started, all you need to do is —
- Create class(es) describing the `Model` // `Table`(s).
- Provide a function which 
returns a connection to a database. 

For example
```sql
CREATE TABLE IF NOT EXISTS user (
 id INTEGER PRIMARY KEY,
 email TEXT NOT NULL,
 first_name TEXT NOT NULL,
 last_name INTEGER NOT NULL,
 active INTEGER NOT NULL DEFAULT '0'
);
```

For the above database `Table` definition, you should create a `Model` class like the following —

```python
from ormvana import Model

class User(Model):
    name = 'user'
    fields = dict()
    for field in ['email', 'first_name', 'last_name']:
        fields[field] = {'type': str}
    fields['active'] = {
        'type': int,
        'value': 0
    }
```

Notice that all we're really doing is:
- Specifying the name of the `Table` using the `name` class variable.
- Specifying the columns // `Field`s of the database using the `fields` class variable. `fields` is a dict, where the 
keys are the _field names_ and the values are dicts. These dicts necessarily contain a key named `type` which can either take 
`str` or `int` as values, and optionally contain another key named `value`, which can be used to provide a default 
value of the given field.

You also would need to provide a `connection` function to `ormvana`, which would return a connection to the database, 
along with a bool that indicates whether to `close` the connection after every query.

Check the following example:
```python
import sqlite3
import ormvana

def connection():
    conn = sqlite3.connect('blog.db')
    conn.row_factory = sqlite3.Row
    return True, conn

ormvana.connection = connection
```

For retrieving records // objects, _ormvana_ provides you with three built-in class functions — 
1. `get`: For retrieving record by `id`. 
2. `get_by`: For retrieving records(s) having given value for given field.
3. `get_all`: For retrieving all the records of the table.

For everything else, you have to write a method for your class that returns a valid SQL query, and decorate that with 
either the `fetch_single` or `fetch_multiple` decorator accordingly. For example, look at the following:

```sql
DROP TABLE IF EXISTS `post`;
CREATE TABLE IF NOT EXISTS post (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  author INTEGER NOT NULL
);
```

```python
from ormvana import Model

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
```

Now that we have defined our models, let's look at how we could use them in our application.

### Creating records

```pycon
>>> from models import User, Post
>>> john = User(email='john@email.com', first_name='John', last_name='Doe')
>>> john.save()
[*] Query: INSERT INTO `user` (`active`, `email`, `first_name`, `last_name`) VALUES (0, 'john@email.com', 'John', 'Doe');
1
>>> john.email = 'john@email.io'
>>> john.save()
[*] Query: UPDATE `user` set `active` = 0, `email` = 'john@email.io', `first_name` = 'John', `last_name` = 'Doe' WHERE id=1;
1
>>> jane = User(email='jane@email.com', first_name='Jane', last_name='Doe', active=1)
>>> jane.save()
[*] Query: INSERT INTO `user` (`active`, `email`, `first_name`, `last_name`) VALUES (1, 'jane@email.com', 'Jane', 'Doe');
2
>>> post = Post(title='Hello world!', body='This is my first post!', author=1)
>>> post
{'id': '', 'cnx': <sqlite3.Connection object at 0x01055B20>, 'title': 'Hello world!', 'body': 'This is my first post!', 'author': 1}
>>> post.save()
[*] Query: INSERT INTO `post` (`title`, `body`, `author`) VALUES ('Hello world!', 'This is my first post!', 1);
1
```

### Updating records

```pycon
>>> john.email = 'john@email.io'
>>> john.save()
[*] Query: UPDATE `user` set `active` = 0, `email` = 'john@email.io', `first_name` = 'John', `last_name` = 'Doe' WHERE id=1;
1
```

### Retrieving records

```pycon
>>> from models import User, Post
>>> users = User.get_all()
[*] Query: SELECT * FROM `user`;
>>> users
[{'id': 1, 'cnx': <sqlite3.Connection object at 0x01D059A0>, 'email': 'john@email.io', 'first_name': 'John', 'last_name': 'Doe', 'active': 0}, {'id': 2, 'cnx': <sqlite3.Connection object at 0x01D05A20>, 'email': 'jane@email.com', 'first_name': 'Jane', 'last_name': 'Doe', 'active': 1}]
>>> users[0].first_name
'John'
>>> jane = User.get(2)
[*] Query: SELECT * FROM `user` WHERE id='2';
>>> jane
{'id': 2, 'cnx': <sqlite3.Connection object at 0x01D05CA0>, 'email': 'jane@email.com', 'first_name': 'Jane', 'last_name': 'Doe', 'active': 1}
>>> results = User.get_by('first_name', 'John')
[*] Query: SELECT * FROM `user` WHERE first_name='John';
>>> results
[{'id': 1, 'cnx': <sqlite3.Connection object at 0x010559A0>, 'email': 'john@email.io', 'first_name': 'John', 'last_name': 'Doe', 'active': 0}]
>>> Post.users_posts('john@email.io')
[*] Query: SELECT * FROM `post` WHERE `author`=(SELECT id from `user` WHERE email='john@email.io');
[{'id': 1, 'cnx': <sqlite3.Connection object at 0x03885CA0>, 'title': 'Hello world!', 'body': 'This is my first post!', 'author': 1}]
```

## Contribute

All kinds of contribution are welcome.

- Issue Tracker — https://github.com/ormvana/issues
- Source Code — https://github.com/ormvana

## License

This project is licensed under the MIT license.
