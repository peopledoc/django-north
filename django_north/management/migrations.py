import os
from distutils.version import StrictVersion
from importlib import import_module

from django.conf import settings
from django.db.migrations.recorder import MigrationRecorder
from django.db.utils import ProgrammingError

import septentrion
from django_north.management.commands import septentrion_settings


fixtures_default_tpl = 'fixtures_{}.sql'
schema_default_tpl = 'schema_{}.sql'


class DBException(Exception):
    pass


def is_version(vstring):
    try:
        StrictVersion(vstring)
    except ValueError:
        return False
    return True


def list_dirs(root):
    return [d for d in os.listdir(root)
            if os.path.isdir(os.path.join(root, d))]


def list_files(root):
    return [d for d in os.listdir(root)
            if os.path.isfile(os.path.join(root, d))]


def get_applied_versions(connection):
    """
    Return the list of applied versions.
    Reuse django migration table.
    """
    recorder = MigrationRecorder(connection)

    applied_versions = list(recorder.migration_qs.filter(
        app__in=septentrion.get_known_versions(
            MIGRATIONS_ROOT=settings.NORTH_MIGRATIONS_ROOT,
            **septentrion_settings(connection)
        )
    ).values_list(
        'app', flat=True).order_by('app').distinct())

    # sort versions
    applied_versions.sort(key=StrictVersion)
    return applied_versions


def get_current_version(connection):
    """
    Return the current version of the database.
    Return None if the schema is not inited.
    """
    try:
        import_string = settings.NORTH_CURRENT_VERSION_DETECTOR
    except AttributeError:
        import_string = (
            'django_north.management.migrations'
            '.get_current_version_from_table')

    module_path, factory_name = import_string.rsplit('.', 1)
    module = import_module(module_path)
    factory = getattr(module, factory_name)

    return factory(connection)


def get_current_version_from_table(connection):
    """
    Return the current version of the database, from sql_version table.
    Return None if the table does not exist (schema not inited).
    """
    with connection.cursor() as cursor:
        try:
            cursor.execute("SELECT version_num FROM sql_version;")
        except ProgrammingError:
            # table does not exist ?
            return None

        rows = cursor.fetchall()

    versions = [row[0] for row in rows if is_version(row[0])]
    if not versions:
        return None

    # sort versions
    versions.sort(key=StrictVersion)

    # return the last one
    return versions[-1]


def get_current_version_from_comment(connection):
    """
    Return the current version of the database, from django_site comment.
    Return None if the table django_site does not exist (schema not inited).
    """
    with connection.cursor() as cursor:
        try:
            cursor.execute(
                "SELECT obj_description('django_site'::regclass, 'pg_class');")
        except ProgrammingError:
            # table does not exist ?
            return None

        row = cursor.fetchone()
        comment = row[0]

    # no comment
    if comment is None:
        raise DBException('No comment found on django_site.')

    # parse comment
    if 'version ' not in comment:
        raise DBException("No version found in django_site's comment.")
    return comment.replace('version ', '').strip()


def get_applied_migrations(version, connection):
    """
    Return the list of applied migrations for the given version.
    Reuse django migration table.
    """
    recorder = MigrationRecorder(connection)
    return list(recorder.migration_qs.filter(app=version).values_list(
        'name', flat=True))
