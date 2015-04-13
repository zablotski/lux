from . import sqlite
__test__ = False


class TestRethinkDB(sqlite.TestSql):
    config_params = {'DATASTORE': 'rethinkdb://127.0.0.1:28015/luxtests',
                     'GREEN_POOL': 50}

