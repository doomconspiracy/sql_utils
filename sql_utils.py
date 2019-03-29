
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

def execute_sql(conn, sql, param_dict):
    "Returns results of executing sql as array"
    rows = []
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

class SQLRegister:
    """
    Singleton class to use a repository for sql and sql template strings with some utility wrappers.
    
    Example usage:
    SQLRegister('query_foo', 'select * from foo where id=%(foo_id)')
    SQLRegister('query_nested', 'select * from bar b join (%(query_foo)s) qf ON (qf.id=b.foo_id)')

    from django.db import connection
    result_rows = SQLRegister.execute(connection, 'query_nested', {'foo_id': 12})
    """
    queries = {}
    __instance = None
    def __new__(cls, name=None, sql=None):
        if SQLRegister.__instance is None:
            SQLRegister.__instance = object.__new__(cls)
        if name is not None and sql is not None:
            SQLRegister.__instance.add(name, sql)
        return SQLRegister.__instance

    def add(self, name, sql):
        self.queries[name] = sql

    def execute(self, conn, name, params):
        return execute_sql_template(conn, self.queries[name], self.queries, params)

    def get_sql(self, name):
        return expand_template(self.queries[name], self.queries)