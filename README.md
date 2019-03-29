# sql_utils

A collection of python sql and db utilites.

Example usage:
    from django.db import connection
    import sql_utils

    sql_utils.SQLRegister('query_foo', 'select * from foo where id=%(foo_id)')
    sql_utils.SQLRegister('query_nested',
        'select * from bar b join (%(query_foo)s) qf ON (qf.id=b.foo_id)')
    result_rows = sql_utils.SQLRegister.execute(connection, 'query_nested', {'foo_id': 12})

    sql_utils.SQLRegister().get_sql('query_nested')
    'select * from bar b join (select * from foo where id=%(foo_id)) qf ON (qf.id=b.foo_id)'

    sql_utils.expand_params('%(my_list)s', {'my_list':[1,2,3]})
    ('%(my_list_0)s,%(my_list_1)s,%(my_list_2)s', {'my_list': [1, 2, 3], 'my_list_0': 1, 'my_list_1': 2, 'my_list_2': 3})