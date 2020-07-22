from django.db import connection

from django_north.management import commands


def test_septentrion_settings(db):
    assert commands.septentrion_settings(connection) == {
        'migrations_root': '/home/joachim/src/django-north/tests'
                           '/north_project/sql',
        'target_version': '1.3',

        'dbname': 'test_septentrion',
        'host': '127.0.0.1',
        'username': 'postgres',
        'password': 'password',

        'table': 'django_migrations',
        'name_column': 'name',
        'version_column': 'app',
        'applied_at_column': 'applied',
        'create_table': False,
    }
