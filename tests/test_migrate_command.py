import dj_database_url
import psycopg2

from django.core.management import call_command
from django.db import connections
from django.db import DEFAULT_DB_ALIAS

import pytest
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from django_north.management import migrations

import septentrion


def test_migrate_command_override(mocker):
    mock_django_handle = mocker.patch(
        'django.core.management.commands.migrate.Command.handle')
    mock_sept_migrate = mocker.patch('septentrion.migrate')

    call_command('migrate')

    assert mock_django_handle.called is False
    assert mock_sept_migrate.called is True


@pytest.mark.parametrize("manage", [True, False, None])
def test_migrate_if_needed(mocker, settings, manage):
    if manage is not None:
        settings.NORTH_MANAGE_DB = manage
    if manage is None and hasattr(settings, 'NORTH_MANAGE_DB'):
        del settings.NORTH_MANAGE_DB

    mock_migrate = mocker.patch(
        'septentrion.migrate')

    call_command('migrate')

    assert mock_migrate.called == bool(manage)


def test_migrate_select_database(settings, mocker):
    mock_migrate = mocker.patch('septentrion.migrate')

    call_command('migrate')
    assert mock_migrate.called_once()

    dbname = mock_migrate.call_args[1]['DBNAME']
    assert dbname == settings.DATABASES[DEFAULT_DB_ALIAS]['NAME']

    mock_migrate.reset_mock()

    call_command('migrate', '--database', 'foo')
    assert mock_migrate.called_once()

    dbname = mock_migrate.call_args[1]['DBNAME']
    assert dbname == settings.DATABASES['foo']['NAME']


def run_sql(sql):
    from django.conf import settings
    config = settings.DATABASES['no_init']
    # connect to the database using the default DB name
    # which should have been created by django_db_setup
    # session level fixture
    conn = psycopg2.connect(
        user=config['USER'],
        host=config['HOST'],
        port=config['PORT'],
        password=config['PASSWORD'],
        database=settings.DATABASES['default']['NAME'])
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(sql)
    conn.close()


@pytest.yield_fixture(scope='function')
def django_db_setup_no_init():
    from django.conf import settings

    settings.DATABASES['no_init'] = dj_database_url.config()
    settings.DATABASES['no_init']['NAME'] = 'no_init'

    run_sql('DROP DATABASE IF EXISTS no_init')
    run_sql('CREATE DATABASE no_init')

    yield

    for conn in connections.all():
        conn.close()

    run_sql('DROP DATABASE no_init')


@pytest.mark.django_db
def test_migrate_command_for_real(django_db_setup_no_init, settings):
    # from scratch, septentrion will create a migrations table itself

    # if DB is not initialized, this return None
    assert migrations.get_current_version(connections['no_init']) is None

    call_command('migrate', '--database', 'no_init')

    assert migrations.get_current_version(connections['no_init']) is not None

    # check if max applied version is target version
    assert (migrations.get_applied_versions(connections['no_init'])[-1] ==
            settings.NORTH_TARGET_VERSION)


@pytest.mark.django_db
def test_migrate_command_with_django_table(django_db_setup_no_init, settings):
    """
    This test simulate the case when a project
    was created to be used with django migrations table
    Either because it didn't use septentrion-based django-north,
    or a pre septentrion-base django-north version.
    """
    connection = connections['no_init']

    # We begin with an empty database
    assert migrations.get_current_version(connection) is None

    # We simulate the setup of the database in the past,
    # with a django_migrations table.
    septentrion.migrate(
        **{
            "MIGRATIONS_ROOT": settings.NORTH_MIGRATIONS_ROOT,
            "target_version": "1.0",
            "SCHEMA_TEMPLATE": getattr(
                settings,
                "NORTH_SCHEMA_TPL",
                migrations.schema_default_tpl),
            "DBNAME": connection.settings_dict["NAME"],
            "HOST": connection.settings_dict["HOST"],
            "USERNAME": connection.settings_dict["USER"],
            "PASSWORD": connection.settings_dict["PASSWORD"],
            "TABLE": "django_migrations",
            "VERSION_COLUMN": 'app',
            "NAME_COLUMN": 'name',
            "APPLIED_COLUMN": 'applied',
            "CREATE_TABLE": False,
        },
    )

    # DB is initialized, this doesn't return None
    assert migrations.get_current_version(connections['no_init']) is not None

    # and migrate to newer version
    call_command('migrate', '--database', 'no_init')

    # check if max applied version is target version
    assert settings.NORTH_TARGET_VERSION != "1.0"
    assert (migrations.get_applied_versions(connections['no_init'])[-1] ==
            settings.NORTH_TARGET_VERSION)
