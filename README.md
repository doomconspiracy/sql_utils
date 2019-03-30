# sql_utils

A collection of python sql and db utilites.

## Examples:

    import sql_utils
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    sqlr = sql_utils.SQLRegister()
    sqlr.add('query_foo', 'select * from foo f where id=%(foo_id)')
    sqlr.add('query_nested', 'select * from bar b join (%(query_foo)s) qf ON (qf.id=b.foo_id)')

    sql_statement = sqlr.get_statement('query_nested')

    pp.pprint(sql_statement.expand({'foo_id': 12}))

output:

    (   'select * from bar b join (select * from foo f where id=%(foo_id)) qf ON '
        '(qf.id=b.foo_id)',
        {'foo_id': 12})

setting a mock table:

    sql_statement.mock_tables = {
        'foo': {
            'cols': ['id', 'name'],
            'rows': [[1, 'foo_1'],[2, 'foo_2']]
        }
    }
    pp.pprint(sql_statement.expand({'foo_id': 12}))

output:

    (   'select * from bar b join (select * from(SELECT %(id_0)s as id,%(name_0)s '
        'as name FROM DUAL)\n'
        'UNION ALL (SELECT %(id_1)s as id,%(name_1)s as name FROM DUAL)f where '
        'id=%(foo_id)) qf ON (qf.id=b.foo_id)',
        {'foo_id': 12, 'id_0': 1, 'id_1': 2, 'name_0': 'foo_1', 'name_1': 'foo_2'})