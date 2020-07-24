from django.conf import settings


def septentrion_settings(connection):

    settings_dict = {}
    mapping = {
        "migrations_root": "NORTH_MIGRATIONS_ROOT",
        "target_version": "NORTH_TARGET_VERSION",
        "schema_template": "NORTH_SCHEMA_TPL",
        "schema_version": "NORTH_SCHEMA_VERSION",
        "target_version": "NORTH_TARGET_VERSION",
        "fixtures_template": "NORTH_FIXTURES_TPL",
        "before_schema_file": "NORTH_BEFORE_SCHEMA_FILES",
        "after_schema_file": "NORTH_AFTER_SCHEMA_FILES",
        "non_transactional_keyword": "NORTH_NON_TRANSACTIONAL_KEYWORDS",
        "target_version": "NORTH_TARGET_VERSION",
    }

    for septentrion_name, django_name in mapping.items():
        try:
            settings_dict[septentrion_name] = getattr(settings, django_name)
        except AttributeError:
            pass

    settings_dict.update({key: value for key, value in {
        # Settings from Django's DB connection
        "dbname": connection.settings_dict["NAME"],
        "host": connection.settings_dict["HOST"],
        "port": connection.settings_dict["PORT"],
        "username": connection.settings_dict["USER"],
        "password": connection.settings_dict["PASSWORD"],
    }.items() if value})

    settings_dict.update({
        # Static settings
        "table": "django_migrations",
        "version_column": "app",
        "name_column": "name",
        "applied_at_column": "applied",
        "create_table": False,
    })
    return settings_dict
