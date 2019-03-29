# sql_utils

A collection of python sql and db utilites.

Example usage:

    from sql_utils import SQLRegister
    SQLRegister('query_foo', 'select * from foo where id=%(foo_id)')
    SQLRegister('query_nested', 'select * from bar b join (%(query_foo)s) qf ON (qf.id=b.foo_id)')

    from django.db import connection
    result_rows = SQLRegister.execute(connection, 'query_nested', {'foo_id': 12})

    >>> SQLRegister().get_sql('query_nested')
    'select * from bar b join (select * from foo where id=%(foo_id)) qf ON (qf.id=b.foo_id)'

