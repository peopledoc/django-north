# -*- coding: utf-8 -*-
import septentrion

from django.contrib.staticfiles.management.commands.runserver import \
    Command as RunserverCommand

from django.conf import settings
from django.db import connection
from django_north.management import migrations


class Command(RunserverCommand):
    help = ("Starts a lightweight Web server for development and also "
            "serves static files.")

    def check_migrations(self):
        try:
            migration_plan = septentrion.build_migration_plan(**{
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
            })
        except migrations.DBException as e:
            self.stdout.write(self.style.NOTICE("\n{}\n".format(e)))
            return

        if not septentrion.is_schema_initialized():
            self.stdout.write(self.style.NOTICE("\nSchema not inited.\n"))
            return

        has_migrations = migration_plan is not None and any(
            [
                any([not applied
                     for mig, applied, path, is_manual
                     in plan['plan']])
                for plan in migration_plan
            ]
        )
        if has_migrations:
            self.stdout.write(self.style.NOTICE(
                "\nYou have unapplied migrations; your app may not work "
                "properly until they are applied."
            ))
            self.stdout.write(self.style.NOTICE(
                "Run 'python manage.py migrate' to apply them.\n"
            ))
