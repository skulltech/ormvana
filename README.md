# shinyORM
A minimalist ORM for the power users.

# Usage

To get started, all you need to do is create a class describing the `Model` // `Table`, and provide a function which 
returns a connection to a database. For example:

```sql
CREATE TABLE `user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `email` varchar(191) NOT NULL,
  `password` varchar(255) NOT NULL,
  `first_name` varchar(255) NOT NULL,
  `last_name` varchar(255) NOT NULL,
  `active` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
);
```

For the above database `Table` definition, you should create a `Model` class like the following:

```python
from shinyORM import Model

class User(Model):
    name = 'user'
    fields = {
        'active': {
            'type': int,
            'value': 0
        }
    }
    for field in ['username', 'password', 'email', 'first_name', 'last_name']:
        fields[field] = {'type': str}
```

Notice that all we're really doing is:
- Specifying the name of the `Table` using the `name` class variable.
- Specifying the columns // `Field`s of the database using the `fields` class variable. `fields` is a dict, where the 
keys are the _field names_ and the values are dicts. These dicts necessarily contain a key named `type` which can either take 
`str` or `int` as values, and optionally contain another key named `value`, which can be used to provide a default 
value of the given field.

You also would need to provide a `connection` function to `shinyORM`, which would return a connection to the database. 
Check the following example:

```python
import MySQLdb
import MySQLdb.cursors

import shinyORM


def connect(db=None):
    return MySQLdb.connect(
        user='root',
        passwd='admin@123',
        host='localhost',
        db='blog',
        cursorclass=MySQLdb.cursors.DictCursor,
        use_unicode=True,
        charset='utf8')

shinyORM.connection = connect
```
