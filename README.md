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

    sql_statement = sqlr.get_statement('query_nested')
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

setting a mock template

    sql_statement = sqlr.get_statement('query_nested')
    sql_statement.mock_templates = {
        'query_foo': {
            'cols': ['XXX_1', 'XXX_2'],
            'rows': [['1x1', '1x2']]
        }
    }
    pp.pprint(sql_statement.expand({'foo_id': 12}))

output:

    (   'select * from bar b join ((SELECT %(XXX_1_0)s as XXX_1,%(XXX_2_0)s as '
        'XXX_2 FROM DUAL)) qf ON (qf.id=b.foo_id)',
        {'XXX_1_0': '1x1', 'XXX_2_0': '1x2', 'foo_id': 12})

load nested templates from files

    sql_statement = sqlr.load_template_file(osp.join(os.getcwd(), 'test', 'sql', 'sample1.sql'))
    pp.pprint(sql_statement.sql)
    pp.pprint(sql_statement.expand())

output:

    # template sql
    ('SELECT *\n'
    'FROM (%(test/sql/sample2.sql)s) s2\n'
    'JOIN (%(test/sql/sample3.sql)s) s3 ON (s3.sample2_id=s2.id)\n'
    'WHERE s2.id=%(s2_id)s\n')

    # expanded sql
    (   'SELECT *\n'
        'FROM (SELECT id, name\n'
        'FROM foo) s2\n'
        'JOIN (SELECT sample2_id\n'
        'FROM bar) s3 ON (s3.sample2_id=s2.id)\n'
        'WHERE s2.id=%(s2_id)s\n',
        {})
