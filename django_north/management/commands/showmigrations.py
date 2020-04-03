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
    help = "Shows all available migrations for the current project"

    def add_arguments(self, parser):
        parser.add_argument(
            '--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS,
            help='Nominates a database to synchronize. '
                 'Defaults to the "default" database.',
        )

    def handle(self, *args, **options):
        if getattr(settings, 'NORTH_MANAGE_DB', False) is not True:
            logger.info('showmigrations command disabled')
            return

        connection = connections[options['database']]

        septentrion.show_migrations(
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
            },
        )
