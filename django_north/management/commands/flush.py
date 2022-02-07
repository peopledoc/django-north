from __future__ import unicode_literals

import logging
import septentrion

from importlib import import_module

import django
from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.core.management import get_commands
from django.core.management import load_command_class
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.core.management.color import no_style
from django.db import DEFAULT_DB_ALIAS
from django.db import connections
from django.db import transaction

from django_north.management.commands import septentrion_settings
from django_north.management.migrations import get_current_version

logger = logging.getLogger(__name__)


# warning: backport from django 1.8
# this command changed a lot in 1.10


def sql_flush(style, connection, only_django=False, reset_sequences=True,
              allow_cascade=False):
    """
    Returns a list of the SQL statements used to flush the database.

    If only_django is True, then only table names that have associated Django
    models and are in INSTALLED_APPS will be included.
    """
    if only_django:
        tables = connection.introspection.django_table_names(
            only_existing=True, include_views=False)
    else:
        tables = connection.introspection.table_names(include_views=False)
    # custom: do not flush migration tables
    # because if you are running tests with a "reuse db" option,
    # and a transactional test case flushed the test db,
    # migration data must be kept so the next test run do not try
    # to apply migrations again
    protected_tables = getattr(
        settings, 'NORTH_PROTECTED_TABLES',
        ['django_migrations', 'sql_version'])
    for protected in protected_tables:
        if protected in tables:
            tables.remove(protected)

    kwargs = {"allow_cascade": allow_cascade}
    # see commit 75410228dfd16e49eb3c0ea30b59b4c0d2ea6b03
    if django.VERSION[:2] < (3, 1):
        if reset_sequences:
            seqs = connection.introspection.sequence_list()
        else:
            seqs = ()
        kwargs["sequences"] = seqs
    else:
        kwargs["reset_sequences"] = reset_sequences

    statements = connection.ops.sql_flush(style, tables, **kwargs)
    return statements


class Command(BaseCommand):
    help = ('Removes ALL DATA from the database, including data added during '
            'migrations. Unmigrated apps will also have their initial_data '
            'fixture reloaded. Does not achieve a "fresh install" state.')
    stealth_options = ('reset_sequences', 'allow_cascade',
                       'inhibit_post_migrate')

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput', action='store_false', dest='interactive',
            default=True,
            help='Tells Django to NOT prompt the user for input of any kind.')
        parser.add_argument(
            '--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS,
            help='Nominates a database to flush. Defaults to the "default" '
            'database.')
        parser.add_argument(
            '--no-initial-data', action='store_false',
            dest='load_initial_data', default=True,
            help='Tells Django not to load any initial data after database '
            'synchronization.')

    def handle(self, **options):
        if getattr(settings, 'NORTH_MANAGE_DB', False) is not True:
            logger.info('flush command disabled')
            return

        self.flush(**options)

    def flush(self, **options):
        database = options.get('database')
        connection = connections[database]
        verbosity = options.get('verbosity')
        interactive = options.get('interactive')
        # The following are stealth options used by Django's internals.
        reset_sequences = options.get('reset_sequences', True)
        allow_cascade = options.get('allow_cascade', False)
        inhibit_post_migrate = options.get('inhibit_post_migrate', False)

        self.style = no_style()

        # Import the 'management' module within each installed app, to register
        # dispatcher events.
        for app_config in apps.get_app_configs():
            try:
                import_module('.management', app_config.name)
            except ImportError:
                pass

        # custom: only_django False
        # get current version before flush
        current_version = get_current_version(connection)
        sql_list = sql_flush(self.style, connection, only_django=False,
                             reset_sequences=reset_sequences,
                             allow_cascade=allow_cascade)

        if interactive:
            confirm = input(
                """You have requested a flush of the database.
This will IRREVERSIBLY DESTROY all data currently in the %r database,
and return each table to an empty state.
Are you sure you want to do this?

    Type 'yes' to continue, or 'no' to cancel: """
                % connection.settings_dict['NAME'])
        else:
            confirm = 'yes'

        if confirm == 'yes':
            try:
                with transaction.atomic(
                        using=database,
                        savepoint=connection.features.can_rollback_ddl):
                    with connection.cursor() as cursor:
                        for sql in sql_list:
                            cursor.execute(sql)
            except Exception as e:
                new_msg = (
                    "Database %s couldn't be flushed. Possible reasons:\n"
                    "  * The database isn't running or isn't configured "
                    "correctly.\n"
                    "  * At least one of the expected database tables doesn't "
                    "exist.\n"
                    "  * The SQL was invalid.\n"
                    "Hint: Look at the output of 'django-admin sqlflush'. "
                    "That's the SQL this command wasn't able to run.\n"
                    "The full error: %s") % (
                        connection.settings_dict['NAME'], e)
                raise CommandError(new_msg) from e

            if not inhibit_post_migrate:
                self.emit_post_migrate(
                    verbosity, interactive, database, current_version)

            # Reinstall the initial_data fixture.
            if options.get('load_initial_data'):
                # Remove any option that is not handle by loaddata
                # We need to load loaddata command, get its parser to extract
                # valid options
                app_name = get_commands()['loaddata']
                command = load_command_class(app_name, 'loaddata')
                parser = command.create_parser('loaddata', 'initial_data')
                valid_options = [action.dest for action in parser._actions
                                 if action.option_strings]
                app_options = {k: v for k, v in options.items()
                               if k in valid_options}
                # Reinstall the initial_data fixture for apps without
                # migrations.
                from django.db.migrations.executor import MigrationExecutor
                executor = MigrationExecutor(connection)
                for app_label in executor.loader.unmigrated_apps:
                    app_options['app_label'] = app_label
                    try:
                        call_command('loaddata', 'initial_data', **app_options)
                    except CommandError:
                        # fails with django 1.10 if initial_data does not exist
                        pass
        else:
            self.stdout.write("Flush cancelled.\n")

    @staticmethod
    def emit_post_migrate(verbosity, interactive, database, current_version):
        # custom: do what was done on post_migrate
        # clear contenttype cache
        ContentType.objects.clear_cache()

        # reload fixtures
        connection = connections[database]
        septentrion.load_fixtures(
            current_version, **septentrion_settings(connection),
        )
