from django.conf import settings

from django_north.management import migrations


def septentrion_settings(connection):
    return {
        "migrations_root": settings.NORTH_MIGRATIONS_ROOT,
        "target_version": settings.NORTH_TARGET_VERSION,
        "schema_template": getattr(
            settings, "NORTH_SCHEMA_TPL", migrations.schema_default_tpl
        ),
        "fixtures_template": getattr(
            settings, "NORTH_FIXTURES_TPL", migrations.fixtures_default_tpl
        ),
        "dbname": connection.settings_dict["NAME"],
        "host": connection.settings_dict["HOST"],
        "username": connection.settings_dict["USER"],
        "password": connection.settings_dict["PASSWORD"],
        "table": "django_migrations",
        "version_column": "app",
        "name_column": "name",
        "applied_at_column": "applied",
        "create_table": False,
    }
