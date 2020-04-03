from django.core.management import call_command

import pytest
import septentrion


def test_showmigrations_command_override(mocker):
    mock_django_handle = mocker.patch(
        'django.core.management.commands.showmigrations.Command.handle')
    mock_show_migrations = mocker.patch(
        'septentrion.show_migrations', return_value=b'')

    call_command('showmigrations')

    assert mock_django_handle.called is False
    assert mock_show_migrations.called is True


@pytest.mark.parametrize("manage", [True, False, None])
def test_north_manage_migrations(mocker, settings, manage):
    if manage is not None:
        settings.NORTH_MANAGE_DB = manage
    if manage is None and hasattr(settings, 'NORTH_MANAGE_DB'):
        del settings.NORTH_MANAGE_DB

    mock = mocker.patch('septentrion.show_migrations', return_value=b'')

    call_command('showmigrations')

    assert mock.called == bool(manage)


def test_showmigrations_schema_not_inited(capsys, mocker):

    mock_version = mocker.patch(
        'septentrion.db.get_current_schema_version')

    # schema not inited
    mock_version.return_value = None

    call_command('showmigrations')
    captured = capsys.readouterr()

    assert 'Current version is None' in captured.out


def test_showmigrations_schema(capsys, mocker):
    # schema inited
    mock_version = mocker.patch(
        'septentrion.db.get_current_schema_version')
    mock_version.return_value = septentrion.versions.Version.from_string('1.1')

    mock_plan = mocker.patch(
        'septentrion.core.build_migration_plan')
    mock_plan.return_value = [
        {
            'version': "Version 1.2",
            'plan': [
                ('a-ddl.sql', True, '/somewhere/a-ddl.sql', False),
                ('b-ddl.sql', False, '/somewhere/b-ddl.sql', True),
            ]
        },
        {
            'version': "Version 1.3",
            'plan': [
                ('c-ddl.sql', False, '/somewhere/c-ddl.sql', False),
            ]
        }
    ]
    call_command('showmigrations')
    captured = capsys.readouterr()

    assert "Current version is 1.1" in captured.out
    assert "Target version is 1.3" in captured.out
    assert "Version 1.2" in captured.out
    assert "[X] \x1b[0ma-ddl.sql" in captured.out
    assert "[ ] \x1b[0mb-ddl.sql" in captured.out
    assert "Version 1.3" in captured.out
    assert "[ ] \x1b[0mc-ddl.sql" in captured.out
