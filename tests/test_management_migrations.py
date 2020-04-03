import os

from django.core.exceptions import ImproperlyConfigured
from django.db import connection

import pytest

from django_north.management import migrations


def test_get_known_versions(settings):
    # wrong path
    message = r"settings\.NORTH_MIGRATIONS_ROOT is improperly configured."

    settings.NORTH_MIGRATIONS_ROOT = '/path/to/nowhere'
    with pytest.raises(ImproperlyConfigured, match=message):
        migrations.get_known_versions()

    root = os.path.dirname(__file__)
    settings.NORTH_MIGRATIONS_ROOT = os.path.join(root, 'foo')
    with pytest.raises(ImproperlyConfigured, match=message):
        migrations.get_known_versions()

    # correct path
    settings.NORTH_MIGRATIONS_ROOT = os.path.join(root, 'test_data/sql')
    result = migrations.get_known_versions()
    assert result == ['16.9', '16.11', '16.12', '17.01', '17.02', '17.3']


@pytest.mark.django_db
def test_get_applied_versions(mocker):
    mocker.patch(
        'django_north.management.migrations.get_known_versions',
        return_value=['1.0', '1.1', '1.2', '1.3', '1.10'])

    recorder = migrations.MigrationRecorder(connection)
    recorder.record_applied('1.10', 'fake-ddl.sql')
    result = migrations.get_applied_versions(connection)
    assert result == ['1.0', '1.1', '1.2', '1.3', '1.10']


def test_get_migrations_to_apply(settings):
    root = os.path.dirname(__file__)
    settings.NORTH_MIGRATIONS_ROOT = os.path.join(root, 'test_data/sql')

    # version folder does not exist
    message = r"No sql folder found for version foo\."
    with pytest.raises(migrations.DBException, match=message):
        migrations.get_migrations_to_apply('foo')

    # no manual folder
    result = migrations.get_migrations_to_apply('17.02')
    migs = ['17.02-0-version-dml.sql',
            '17.02-feature_a-ddl.sql',
            '17.02-feature_b_manual-dml.sql',
            '17.02-feature_c_fakemanual-ddl.sql']
    assert result == {
        mig: os.path.join(
            settings.NORTH_MIGRATIONS_ROOT, '17.02', mig) for mig in migs
    }

    # with manual folder
    result = migrations.get_migrations_to_apply('17.01')
    migs = [
        '17.01-0-version-dml.sql',
        '17.01-feature_a-010-ddl.sql',
        '17.01-feature_a-020-ddl.sql',
        '17.01-feature_a-030-dml.sql',
        '17.01-feature_a-050-ddl.sql',
        '17.01-feature_b-ddl.sql',
    ]
    migration_dict = {
        mig: os.path.join(
            settings.NORTH_MIGRATIONS_ROOT, '17.01', mig) for mig in migs
    }
    migs = ['17.01-feature_a-040-dml.sql']
    migration_dict.update({
        mig: os.path.join(settings.NORTH_MIGRATIONS_ROOT, '17.01/manual', mig)
        for mig in migs
    })
    assert result == migration_dict


def test_get_fixtures_for_init(settings, mocker):
    root = os.path.dirname(__file__)
    settings.NORTH_MIGRATIONS_ROOT = os.path.join(root, 'test_data/sql')
    mock_versions = mocker.patch(
        'django_north.management.migrations.get_known_versions')

    mock_versions.return_value = ['16.11', '16.12', '17.01', '17.02']

    # target version is out of scope
    message = (
        r"settings.NORTH_TARGET_VERSION is improperly configured: "
        r"version foo not found\.")
    settings.NORTH_TARGET_VERSION = 'foo'
    with pytest.raises(ImproperlyConfigured, match=message):
        migrations.get_fixtures_for_init('foo')

    # fixtures for the version exists
    assert migrations.get_fixtures_for_init('16.12') == '16.12'

    # fixtures for the version does not exist, take the first ancestor
    assert migrations.get_fixtures_for_init('17.01') == '16.12'

    # no fixtures for the version, and no ancestors
    message = "Can not find fixtures to init the DB."
    with pytest.raises(migrations.DBException, match=message):
        migrations.get_fixtures_for_init('16.11')

    # no ancestors, but fixtures exists
    mock_versions.return_value = ['16.12', '17.01', '17.02']
    assert migrations.get_fixtures_for_init('17.01') == '16.12'

    # wrong template
    settings.NORTH_FIXTURES_TPL = 'foo.sql'
    with pytest.raises(migrations.DBException, match=message):
        migrations.get_fixtures_for_init('16.12')
    settings.NORTH_FIXTURES_TPL = 'foo{}.sql'
    with pytest.raises(migrations.DBException, match=message):
        migrations.get_fixtures_for_init('16.12')
