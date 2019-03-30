# sql_utils

A collection of python sql and db utilites.

Example usage:

    from django.db import connection
    import sql_utils
    sqlr =sql_utils.SQLRegister()
    sqlr.add('query_foo', 'select * from foo where id=%(foo_id)')
    sqlr.add('query_nested', 'select * from bar b join (%(query_foo)s) qf ON (qf.id=b.foo_id)')
    sql_statement = sqlr.get_statement('query_nested')
    sql_statement.expand({'foo_id': 12})
    'select * from bar b join (select * from foo where id=%(foo_id)) qf ON (qf.id=b.foo_id)'
    result_rows = sql_statement.execute(connection, {'foo_id': 12})

