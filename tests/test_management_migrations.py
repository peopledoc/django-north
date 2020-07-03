from django.db import connection

import pytest

from django_north.management import migrations


@pytest.mark.django_db
def test_get_applied_versions(mocker):
    mocker.patch(
        'septentrion.get_known_versions',
        return_value=['1.0', '1.1', '1.2', '1.3', '1.10'])

    recorder = migrations.MigrationRecorder(connection)
    recorder.record_applied('1.10', 'fake-ddl.sql')
    result = migrations.get_applied_versions(connection)
    assert result == ['1.0', '1.1', '1.2', '1.3', '1.10']
