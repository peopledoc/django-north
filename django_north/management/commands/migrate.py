# -*- coding: utf-8 -*-
import logging

import septentrion

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connections
from django.db import DEFAULT_DB_ALIAS

from django_north.management import migrations

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

        connection = connections[options['database']]

        septentrion.migrate(
            **{
                "MIGRATIONS_ROOT": settings.NORTH_MIGRATIONS_ROOT,
                "target_version": settings.NORTH_TARGET_VERSION,
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
                "APPLIED_AT_COLUMN": 'applied',
                "CREATE_TABLE": False,
            },
        )
