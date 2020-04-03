from django_north.management import migrations
from django_north.management.commands import runserver


def test_runserver_check_migrations(
        capsys,
        mocker,
):
    mock_plan = mocker.patch(
        'septentrion.core.build_migration_plan')

    # DBException raised
    command = runserver.Command()
    mock_plan.side_effect = migrations.DBException('Something...')
    command.check_migrations()
    captured = capsys.readouterr()
    assert captured.out == '\nSomething...\n'

    # schema not inited
    mocker.patch(
        'septentrion.is_schema_initialized', return_value=False)
    command = runserver.Command()
    mock_plan.side_effect = None
    mock_plan.return_value = None
    command.check_migrations()
    captured = capsys.readouterr()
    assert captured.out == '\nSchema not inited.\n'

    # schema inited, missing migrations
    command = runserver.Command()
    mocker.patch(
        'septentrion.is_schema_initialized', return_value=True)
    mock_plan.return_value = [
        {
            'version': 'v3',
            'plan': [
                ('a-ddl.sql', True, '/somewhere/a-ddl.sql', False),
                ('b-ddl.sql', False, '/somewhere/manual/b-ddl.sql', True),
            ]
        },
        {
            'version': 'v4',
            'plan': [
                ('a-ddl.sql', False, '/somewhere/a-ddl.sql', False),
            ]
        }
    ]
    with capsys.disabled():
        command.check_migrations()
    captured = capsys.readouterr()
    assert captured.out == (
        "\nYou have unapplied migrations; "
        "your app may not work properly until they are applied.\n"
        "Run 'python manage.py migrate' to apply them.\n"
    )

    # schema inited, no missing migrations
    command = runserver.Command()
    mock_plan.return_value = [
        {
            'version': 'v3',
            'plan': [
                ('a-ddl.sql', True, '/somewhere/a-ddl.sql', False),
                ('b-ddl.sql', True, '/somewhere/manual/b-ddl.sql', True),
            ]
        },
        {
            'version': 'v4',
            'plan': [
                ('a-ddl.sql', True, '/somewhere/a-ddl.sql', False),
            ]
        }
    ]
    command.check_migrations()
    captured = capsys.readouterr()
    assert captured.out == ''
