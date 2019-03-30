import copy
import os
import os.path as osp
import pprint
pp = pprint.PrettyPrinter(indent=4)

def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def get_param_keys(sql):
    "Return all dict param keys in passed in sql string as a dict"
    keys = {}
    error = True
    while error:
        try:
            str = sql % keys
            error = False
        except KeyError as e:
            key = e.args[0]
            keys[key] = '%%(%s)s' % key
    return keys

def expand_template(sql, template_dict):
    "Returns sql string with all string dict params from template_dict expanded (recursively)"
    params = get_param_keys(sql)
    params.update(template_dict)
    error = True
    while error:
        try:
            sql = sql % params
            error = False
        except KeyError as e:
            params = get_param_keys(sql)
            params.update(template_dict)
    return sql

def expand_params(sql, param_dict):
    "Returns tuple of a sql template string and dict of params updated to refect expanded list params"
    update_params = {}
    for key in param_dict.keys():
        if type(param_dict[key]) == list:
            list_params = {}
            for i, val in enumerate(param_dict[key]):
                list_params['%s_%d' % (key, i)] = param_dict[key][i]
            try:
                sql = sql % {key: ','.join(['%%(%s)s' % k for k in list_params.keys()])}
            except KeyError:
                pass
            update_params.update(list_params)
    param_dict.update(update_params)
    return (sql, param_dict)

def execute_sql(conn, sql, param_dict):
    "Returns results of executing sql as array"
    rows = []
    sql, param_dict = expand_params(sql, param_dict)
    with conn.cursor() as cursor:
        cursor.execute(sql, param_dict)
        rows = dictfetchall(cursor)
    return rows

def execute_sql_template(conn, template, template_dict, param_dict):
    "Returns results of executing sql template as array"
    sql = expand_template(template, template_dict)
    rows = execute_sql(conn, sql, param_dict)
    return rows

def data_to_sql_template(cols, rows):
    "Returns tuple of a sql template string and dict of params defined to map data to inline sql set"
    values = []
    params = {}
    for i, row in enumerate(rows):
        row_values = []
        for col_i, col in enumerate(cols):
            key = '%s_%d' % (col, i)
            params[key] = row[col_i]
            row_values.append('%%(%(key)s)s as %(col)s' % {'key': key, 'col': col})
        values.append('(SELECT %s FROM DUAL)' % ','.join(row_values))
    template = '\nUNION ALL '.join(values)
    return (template, params)

def insert_mock(sql, params, data, replace_target):
        mock_sql, mock_params = data_to_sql_template(data['cols'], data['rows'])
        params.update(mock_params)
        sql = sql.replace(replace_target, mock_sql)
        return (sql, params)


class Statement:
    """
    SQL Statement class to emsulate a sql query context and statement instance tools.
    """
    mock_tables = {}
    mock_templates = {}

    def __init__(self, sql=None, params={}):
        self.sql = sql

    def expand(self, params={}):
        sql = self.sql
        for template in self.mock_templates.keys():
            sql, params = insert_mock(sql, params, self.mock_templates[template], '%%(%s)s'  % template)
        sql = expand_template(sql, SQLRegister().template_dict)
        for table in self.mock_tables.keys():
            sql, params = insert_mock(sql, params, self.mock_tables[table], ' %s ' % table)
        sql, params = expand_params(sql, params)
        return (sql, params)

    def execute(self, conn, params={}):
        sql, params = self.expand(params)
        return execute_sql(conn, sql, params)


class SQLRegister:
    """
    Singleton class to use a repository for sql and sql template strings with some utility wrappers.
    
    Example usage:
    SQLRegister('query_foo', 'select * from foo where id=%(foo_id)')
    SQLRegister('query_nested', 'select * from bar b join (%(query_foo)s) qf ON (qf.id=b.foo_id)')

    from django.db import connection
    result_rows = SQLRegister.execute(connection, 'query_nested', {'foo_id': 12})
    """
    _statements = {}
    __instance = None
    def __new__(cls, name=None, sql=None):
        if SQLRegister.__instance is None:
            SQLRegister.__instance = object.__new__(cls)
        if name is not None and sql is not None:
            SQLRegister.__instance.add(name, sql)
        return SQLRegister.__instance

    def add(self, name, sql):
        self._statements[name] = sql
        pp.pprint(sql)
        try:
            keys = get_param_keys(sql)
            for key in keys:
                pp.pprint(key)
                if key.endswith('.sql'):
                    if osp.exists(self.template_path(key)):
                        self.load_template_file(key)
        except ValueError as e:
            pass

    def get_statement(self, name):
        return Statement(sql=self._statements[name])

    @property
    def template_dict(self):
        return copy.deepcopy(self._statements)

    def template_path(self, path):
        return osp.join(os.getcwd(), path)

    def load_template_file(self, path):
        template_path = self.template_path(path)
        with open(template_path) as f:
            template = f.read()
        self.add(path, template)
        return self.get_statement(path)


if __name__ == '__main__':

    sqlr = SQLRegister()
    sqlr.add('query_foo', 'select * from foo f where id=%(foo_id)')
    sqlr.add('query_nested', 'select * from bar b join (%(query_foo)s) qf ON (qf.id=b.foo_id)')

    sql_statement = sqlr.get_statement('query_nested')
    pp.pprint(sql_statement.expand({'foo_id': 12}))

    sql_statement = sqlr.get_statement('query_nested')
    sql_statement.mock_tables = {
        'foo': {
            'cols': ['id', 'name'],
            'rows': [[1, 'foo_1'],[2, 'foo_2']]
        }
    }
    pp.pprint(sql_statement.expand({'foo_id': 12}))

    sql_statement = sqlr.get_statement('query_nested')
    sql_statement.mock_templates = {
        'query_foo': {
            'cols': ['XXX_1', 'XXX_2'],
            'rows': [['1x1', '1x2']]
        }
    }
    pp.pprint(sql_statement.expand({'foo_id': 12}))

    sql_statement = sqlr.load_template_file(osp.join(os.getcwd(), 'test', 'sql', 'sample1.sql'))
    pp.pprint(sql_statement.sql)
    pp.pprint(sql_statement.expand())


