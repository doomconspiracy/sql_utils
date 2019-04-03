import unittest
import sql_utils


class GetParamKeysTests(unittest.TestCase):
    def test_matches_all(self):
        self.assertEqual(
            sql_utils.get_param_keys('%(one)s %(two)s %(three)s'),
            {'one': '%(one)s', 'three': '%(three)s', 'two': '%(two)s'}
        )


class ExpandTemplate(unittest.TestCase):
    def test_replaces_template(self):
        self.assertEqual(
            sql_utils.expand_template('%(temp_name)s', {
                'temp_name': 'value'
            }),
            'value'
        )


class ExpandParams(unittest.TestCase):
    def test_expands_scalar(self):
        self.assertEqual(
            sql_utils.expand_params('%(foo_1)s %(foo_2)s %(foo_3)s', {
                'foo_1': 'bar_1',
                'foo_2': 'bar_2',
                'foo_3': 'bar_3',
            }),
           (
               '%(foo_1)s %(foo_2)s %(foo_3)s', {
                    'foo_1': 'bar_1',
                    'foo_2': 'bar_2',
                    'foo_3': 'bar_3',
                }
           )
        )

    def test_expands_list(self):
        self.assertEqual(
            sql_utils.expand_params('%(list_val)s %(scalar)s', {
                'scalar': 'val',
                'list_val': [1,2,3],
            }),
           (
               '(%(list_val_0)s, %(list_val_1)s, %(list_val_2)s) %(scalar)s', {
                    'scalar': 'val',
                    'list_val': [1,2,3],
                    'list_val_0': 1,
                    'list_val_1': 2,
                    'list_val_2': 3,
                }
           )
        )

    def test_missing_scalar_in_template(self):
        self.assertEqual(
            sql_utils.expand_params('%(list_val)s %(scalar)s', {
                'scalar': 'val',
                'list_val': [1,2,3],
                'foo': 'bar',
            }),
           (
               '(%(list_val_0)s, %(list_val_1)s, %(list_val_2)s) %(scalar)s', {
                    'scalar': 'val',
                    'list_val': [1,2,3],
                    'list_val_0': 1,
                    'list_val_1': 2,
                    'list_val_2': 3,
                    'foo': 'bar',
                }
           )
        )

    def test_missing_list_in_template(self):
        self.assertEqual(
            sql_utils.expand_params('%(list_val)s %(scalar)s', {
                'scalar': 'val',
                'list_val': [1,2,3],
                'foo': [1,2,3]
            }),
           (    '(%(list_val_0)s, %(list_val_1)s, %(list_val_2)s) %(scalar)s',
                {
                    'scalar': 'val',
                    'list_val': [1,2,3],
                    'list_val_0': 1,
                    'list_val_1': 2,
                    'list_val_2': 3,
                    'foo': [1,2,3],
                    'foo_0': 1,
                    'foo_1': 2,
                    'foo_2': 3,})
        )


class DataToSQLTemplateTests(unittest.TestCase):
    def test_data_to_sql(self):
        self.assertEqual(sql_utils.data_to_sql_template(
                ['id', 'name'],
                [[1, 'matt',],[2, 'gabe'],[3, 'jen']]
            ), 
            (   '(SELECT %(id_0)s as id,%(name_0)s as name FROM DUAL)\n'
                'UNION ALL (SELECT %(id_1)s as id,%(name_1)s as name FROM DUAL)\n'
                'UNION ALL (SELECT %(id_2)s as id,%(name_2)s as name FROM DUAL)',
                {   'id_0': 1,
                    'id_1': 2,
                    'id_2': 3,
                    'name_0': 'matt',
                    'name_1': 'gabe',
                    'name_2': 'jen'})
        )


class InsertMockTest(unittest.TestCase):
    def test_mock_template(self):
        self.assertEqual(sql_utils.insert_mock(
                'SELECT * FROM (%(view)s)',
                {},
                {   'cols': ['id', 'name'],
                    'rows': [[1, 'matt',],[2, 'gabe'],[3, 'jen']]},
                '%(view)s'
            ),
            (   'SELECT * FROM ((SELECT %(id_0)s as id,%(name_0)s as name FROM DUAL)\n'
                'UNION ALL (SELECT %(id_1)s as id,%(name_1)s as name FROM DUAL)\n'
                'UNION ALL (SELECT %(id_2)s as id,%(name_2)s as name FROM DUAL))',
                {   'id_0': 1,
                    'id_1': 2,
                    'id_2': 3,
                    'name_0': 'matt',
                    'name_1': 'gabe',
                    'name_2': 'jen'})
        )

    def test_mock_table(self):
        self.assertEqual(sql_utils.insert_mock(
                'SELECT * FROM user u',
                {},
                {   'cols': ['id', 'name'],
                    'rows': [[1, 'matt',],[2, 'gabe'],[3, 'jen']]},
                'user'
            ),
            (   'SELECT * FROM (SELECT %(id_0)s as id,%(name_0)s as name FROM DUAL)\n'
                'UNION ALL (SELECT %(id_1)s as id,%(name_1)s as name FROM DUAL)\n'
                'UNION ALL (SELECT %(id_2)s as id,%(name_2)s as name FROM DUAL) u',
                {   'id_0': 1,
                    'id_1': 2,
                    'id_2': 3,
                    'name_0': 'matt',
                    'name_1': 'gabe',
                    'name_2': 'jen'})
        )


class SQLRegisterTests(unittest.TestCase):
    def test_add_sql(self):
        sqlr = sql_utils.SQLRegister()
        sqlr.add('query', 'sql statement string')
        statement = sqlr.get_statement('query')
        self.assertIsInstance(statement, sql_utils.Statement)
        self.assertEqual(statement.expand(), ('sql statement string', {},))

    def test_add_template(self):
        sqlr = sql_utils.SQLRegister()
        sqlr.add('template_1', 'sql %(list)s')
        self.assertEqual(sqlr.get_statement('template_1').expand({'list': ['foo']}),
            ('sql (%(list_0)s)',
            {   'list': ['foo'],
                'list_0': 'foo'
            })
        )

if __name__ == '__main__':
    unittest.main()