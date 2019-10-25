# -*- coding: utf-8 -*-
import glob
import io
import logging
import os.path
import warnings

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connections
from django.db import DEFAULT_DB_ALIAS

from django_north.management import migrations
from django_north.management.runner import Script

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Migrate the DB to the target version."

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput', '--no-input', action='store_false',
            dest='interactive',
            help='Tells Django to NOT prompt the user for input of any kind.',
        )
        parser.add_argument(
            '--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS,
            help='Nominates a database to synchronize. '
                 'Defaults to the "default" database.',
        )
        parser.add_argument(
            '--run-syncdb', action='store_true', dest='run_syncdb',
            help='Creates tables for apps without migrations.',
        )

    def handle(self, *args, **options):
        if getattr(settings, 'NORTH_MANAGE_DB', False) is not True:
            logger.info('migrate command disabled')
            return

        self.verbosity = options.get('verbosity')

        self.connection = connections[options['database']]
        self.migrate()

    def migrate(self):
        # build miration plan
        migration_plan = migrations.build_migration_plan(self.connection)

        if migration_plan is None:
            # schema not inited
            self.init_schema()
            # reload migration_plan
            migration_plan = migrations.build_migration_plan(self.connection)

        # play migrations
        recorder = migrations.MigrationRecorder(self.connection)
        for plan in migration_plan['plans']:
            version = plan['version']
            if self.verbosity >= 1:
                self.stdout.write(self.style.MIGRATE_LABEL(version))
            for mig, applied, path, is_manual in plan['plan']:
                title = mig
                if is_manual:
                    title += ' (manual)'
                if applied:
                    if self.verbosity >= 1:
                        self.stdout.write("  {} already applied".format(title))
                else:
                    if self.verbosity >= 1:
                        self.stdout.write("  Applying {}...".format(title))
                    self.run_script(path)
                    recorder.record_applied(version, mig)

    def _load_schema_file(self, file_name, load_name=None):
        file_path = os.path.join(
            settings.NORTH_MIGRATIONS_ROOT, 'schemas', file_name)
        self._load_schema_path(file_path, load_name or file_name)

    def _load_schema_path(self, file_path, load_name):
        if self.verbosity >= 1:
            self.stdout.write(
                self.style.MIGRATE_LABEL("Load {}".format(load_name)))
        self.run_script(file_path)

    def _load_schema_fullpath_file(self, file_path):
        migration_root = os.path.join(
            settings.NORTH_MIGRATIONS_ROOT, 'schemas')
        load_name = os.path.relpath(file_path, migration_root)
        self._load_schema_file(file_path, load_name)

    def _load_schema_dir(self, dir_path):
        for file_name in sorted(os.listdir(dir_path)):
            file_path = os.path.join(dir_path, file_name)
            if os.path.isfile(file_path) and file_path.endswith('.sql'):
                self._load_schema_fullpath_file(file_path)

    def _load_schema_string(self, input_string):
        path = os.path.join(
            settings.NORTH_MIGRATIONS_ROOT, 'schemas', input_string)

        for file_path in sorted(glob.glob(path)):
            if os.path.isdir(file_path):
                self._load_schema_dir(file_path)
            if os.path.isfile(file_path):
                self._load_schema_fullpath_file(file_path)

    def init_schema(self):
        init_version = migrations.get_version_for_init()

        # load first set of additional files
        before_files = getattr(
            settings, 'NORTH_BEFORE_SCHEMA_FILES', [])
        for file_name in before_files:
            self._load_schema_string(file_name)

        # load additional files (deprecated)
        additional_files = getattr(
            settings, 'NORTH_ADDITIONAL_SCHEMA_FILES', [])
        if additional_files:
            warnings.warn("NORTH_ADDITIONAL_SCHEMA_FILES will be deprecated. "
                          "Use NORTH_BEFORE_SCHEMA_FILES instead.")
        for file_name in additional_files:
            self._load_schema_file(file_name)

        # load schema
        schema_file = getattr(
            settings, 'NORTH_SCHEMA_TPL',
            migrations.schema_default_tpl
        ).format(init_version)
        self._load_schema_file(schema_file, load_name="schema")
        if self.verbosity >= 1:
            self.stdout.write("  Applying {}...".format(init_version))

        # load other set of additional files
        after_files = getattr(
            settings, 'NORTH_AFTER_SCHEMA_FILES', [])
        for file_name in after_files:
            self._load_schema_string(file_name)

        # load fixtures
        try:
            fixtures_version = migrations.get_fixtures_for_init(init_version)
            fixtures_path = os.path.join(
                settings.NORTH_MIGRATIONS_ROOT,
                'fixtures',
                getattr(settings, 'NORTH_FIXTURES_TPL',
                        migrations.fixtures_default_tpl)
                .format(fixtures_version))
            if self.verbosity >= 1:
                self.stdout.write(self.style.MIGRATE_LABEL("Load fixtures"))
                self.stdout.write("  Applying {}...".format(fixtures_version))
            self.run_script(fixtures_path)
        except migrations.DBException:
            pass

    def run_script(self, path):
        with io.open(path, 'r', encoding='utf8') as f:
            script = Script(f)
            script.run(self.connection)
