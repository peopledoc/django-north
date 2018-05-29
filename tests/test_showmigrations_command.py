from django.core.management import call_command

import pytest


@pytest.mark.parametrize("manage", [True, False, None])
def test_migrate(mocker, settings, manage):
    if manage is not None:
        settings.NORTH_MANAGE_DB = manage
    if manage is None and hasattr(settings, 'NORTH_MANAGE_DB'):
        del settings.NORTH_MANAGE_DB

    mock_handle = mocker.patch(
        'django.core.management.commands.showmigrations.Command.handle')
    mock_plan = mocker.patch(
        'django_north.management.commands.showmigrations.Command.show_list')

    call_command('showmigrations')

    assert mock_handle.called is False
    assert mock_plan.called == bool(manage)


def test_showmigrations(capsys, mocker):
    mock_plan = mocker.patch(
        'django_north.management.migrations.build_migration_plan')

    # schema not inited
    mock_plan.return_value = None
    call_command('showmigrations')
    captured = capsys.readouterr()
    assert captured.out == 'Schema not inited\n'

    # schema inited
    mock_plan.return_value = {
        'current_version': 'v2',
        'init_version': 'v1',
        'plans': [
            {
                'version': 'v3',
                'plan': [
                    ('a-ddl.sql', True, '/somewhere/a-ddl.sql', False),
                    ('b-ddl.sql', False, '/somewhere/b-ddl.sql', True),
                ]
            },
            {
                'version': 'v4',
                'plan': [
                    ('a-ddl.sql', False, '/somewhere/a-ddl.sql', False),
                ]
            }
        ],
    }
    call_command('showmigrations')
    captured = capsys.readouterr()
    assert captured.out == (
        'Current version of the DB:\n'
        '  v2\n'
        'Schema used to init the DB:\n'
        '  v1\n'
        'Version:\n'
        '  v3\n'
        '  [X] a-ddl.sql\n'
        '  [ ] b-ddl.sql (manual)\n'
        'Version:\n'
        '  v4\n'
        '  [ ] a-ddl.sql\n'
    )
