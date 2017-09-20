from __future__ import unicode_literals

from django.core.management.base import AppCommand
from django.core.management.base import CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from django.db import router
from django.utils.version import get_docs_version


def sql_create_model(editor, model):
    """
    Takes a model and creates a table for it in the database.
    Will also create any accompanying indexes or unique constraints.
    """
    # Create column SQL, add FK deferreds if needed
    column_sqls = []
    params = []
    for field in model._meta.local_fields:
        # SQL
        definition, extra_params = editor.column_sql(model, field)
        if definition is None:
            continue
        # Check constraints can go on the column SQL here
        db_params = field.db_parameters(connection=editor.connection)
        if db_params['check']:
            definition += " CHECK (%s)" % db_params['check']
        # Autoincrement SQL (for backends with inline variant)
        col_type_suffix = field.db_type_suffix(connection=editor.connection)
        if col_type_suffix:
            definition += " %s" % col_type_suffix
        params.extend(extra_params)
        # FK
        if field.rel and field.db_constraint:
            editor.deferred_sql.append(
                editor._create_fk_sql(
                    model, field, "_fk_%(to_table)s_%(to_column)s"))
        # Add the SQL to our big list
        column_sqls.append("%s %s" % (
            editor.quote_name(field.column),
            definition,
        ))
        # Autoincrement SQL (for backends with post table definition variant)
        if field.get_internal_type() == "AutoField":
            autoinc_sql = editor.connection.ops.autoinc_sql(
                model._meta.db_table, field.column)
            if autoinc_sql:
                editor.deferred_sql.extend(autoinc_sql)

    # Add any unique_togethers (always deferred, as some fields might be
    # created afterwards, like geometry fields with some backends)
    for fields in model._meta.unique_together:
        columns = [model._meta.get_field(field).column for field in fields]
        editor.deferred_sql.append(editor._create_unique_sql(model, columns))
    # Make the table
    sql = editor.sql_create_table % {
        "table": editor.quote_name(model._meta.db_table),
        "definition": ", ".join(column_sqls)
    }
    if model._meta.db_tablespace:
        tablespace_sql = editor.connection.ops.tablespace_sql(
            model._meta.db_tablespace)
        if tablespace_sql:
            sql += ' ' + tablespace_sql
    # Prevent using [] as params, in the case a literal '%' is used in the
    # definition
    output = [sql % params]

    # Add any field index and index_together's
    editor.deferred_sql.extend(editor._model_indexes_sql(model))

    return output


def sql_create(app_config, style, connection):
    "Returns a list of the CREATE TABLE SQL statements for the given app."

    if connection.settings_dict['ENGINE'] == 'django.db.backends.dummy':
        # This must be the "dummy" database backend, which means the user
        # hasn't set ENGINE for the database.
        raise CommandError(
            "Django doesn't know which syntax to use for your SQL statements,"
            "\nbecause you haven't properly specified the ENGINE setting for "
            "the database.\n"
            "see: https://docs.djangoproject.com/en/%s/ref/settings/"
            "#databases" % get_docs_version()
        )

    # Get installed models, so we generate REFERENCES right.
    # We trim models from the current app so that the sqlreset command does not
    # generate invalid SQL (leaving models out of known_models is harmless, so
    # we can be conservative).
    final_output = []
    output = []

    for model in router.get_migratable_models(
            app_config, connection.alias, include_auto_created=True):
        with connection.schema_editor() as editor:
            output += sql_create_model(editor, model)
            final_output.extend(editor.deferred_sql)
            editor.deferred_sql = []

    return output + final_output


def sql_all(app_config, style, connection):
    """
    Returns a list of CREATE TABLE SQL, initial-data inserts,
    and CREATE INDEX SQL for the given module.
    """
    return sql_create(app_config, style, connection)


class Command(AppCommand):
    help = ("Prints the CREATE TABLE, custom SQL and CREATE INDEX SQL "
            "statements for the given model module name(s).")

    output_transaction = True

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--database',
            default=DEFAULT_DB_ALIAS,
            help='Nominates a database to print the SQL for. Defaults to the '
                 '"default" database.')

    def handle_app_config(self, app_config, **options):
        if app_config.models_module is None:
            return
        connection = connections[options['database']]
        statements = sql_all(app_config, self.style, connection)
        return '\n'.join(statements)
