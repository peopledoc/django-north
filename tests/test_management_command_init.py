from django.db import connection

from django_north.management import commands


def test_septentrion_settings(db):
    settings = commands.septentrion_settings(connection)

    minimal_keys = {
        "migrations_root",
        "target_version",
        "table",
        "name_column",
        "version_column",
        "applied_at_column",
        "create_table",
    }
    assert minimal_keys <= set(settings)
    assert settings["migrations_root"].endswith("tests/north_project/sql")
    assert settings["target_version"] == "1.3"
    assert settings["table"] == 'django_migrations'
    assert settings["name_column"] == 'name'
    assert settings["version_column"] == 'app'
    assert settings["applied_at_column"] == 'applied'
    assert settings["create_table"] is False

    # we can't really test the db params because they depend on how
    # the tests are launched.
