from django.core.management import call_command
from django.core.management.color import no_style
from django.core.management.sql import sql_flush as dj_sql_flush
from django.db import connection

import pytest

from django_north.management.commands.flush import sql_flush


@pytest.mark.parametrize("manage", [True, False, None])
def test_flush(mocker, settings, manage):
    if manage is not None:
        settings.NORTH_MANAGE_DB = manage
    if manage is None and hasattr(settings, 'NORTH_MANAGE_DB'):
        del settings.NORTH_MANAGE_DB

    mock_handle = mocker.patch(
        'django.core.management.commands.flush.Command.handle')
    mock_flush = mocker.patch(
        'django_north.management.commands.flush.Command.flush')

    call_command('flush')

    assert mock_handle.called is False
    assert mock_flush.called == bool(manage)


def test_sql_flush(db):
    style = no_style()
    dj_sql_list = dj_sql_flush(style, connection, only_django=False)
    north_sql_list = sql_flush(style, connection, only_django=False)

    assert 'django_migrations' in ' '.join(dj_sql_list)
    assert 'sql_version' in ' '.join(dj_sql_list)
    assert 'django_migrations' not in ' '.join(north_sql_list)
    assert 'sql_version' not in ' '.join(north_sql_list)
