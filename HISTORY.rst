.. :changelog:

History
-------

0.3.2 (2022-02-07)
++++++++++++++++++

- Add Django 3 compatibility
- Add Github actions
- Fix settings initialization
- Pin pytest_django version to solve a known multidb issue
- Add postgres docker container
- Pin psycopg2 version to fix utc issue due to incompatible types

0.3.1 (2020-07-24)
++++++++++++++++++

- Fix septentrion call in runserver
- Bump to septentrion 0.6.1

0.3.0 (2020-07-24)
++++++++++++++++++

- Remove setting "NORTH_DISCARD_ALL"
- Add function for septentrion settings
- Fix classifiers
- Removed the internal logic for applying migrations, use septentrion instead.


0.2.6 (2019-10-25)
++++++++++++++++++

- Add support for Django 2.2
- `NORTH_AFTER_SCHEMA_FILES` and `NORTH_BEFORE_SCHEMA_FILES` can now accept glob string.


0.2.5 (2019-01-22)
++++++++++++++++++

- Add support for Django 2.1 & Python 3.7
- Add setting `NORTH_AFTER_SCHEMA_FILES` for schema files after the main schema.
- Adding setting `NORTH_BEFORE_SCHEMA_FILES`, to replace `NORTH_ADDITIONAL_SCHEMA_FILES`.
- Deprecate setting `NORTH_ADDITIONAL_SCHEMA_FILES`.

0.2.4 (2018-09-12)
++++++++++++++++++

- Use `--database` option to determine which database to use in migrate command (#35)


0.2.3 (2018-06-15)
++++++++++++++++++

- Add support for Django 2.0 (#31)
- Add a "DISCARD ALL" command run at the end of each script. It adds a new settings variable: ``NORTH_DISCARD_ALL`` (#33)


0.2.2 (2018-02-01)
++++++++++++++++++

- Flush command: do not flush migration tables.


0.2.1 (2018-01-29)
++++++++++++++++++

- Add `VACUUM` to `NORTH_NON_TRANSACTIONAL_KEYWORDS` default settings.
- Add a setting `NORTH_SCHEMA_VERSION` to force the schema to be used to init a DB.


0.2.0 (2017-10-16)
++++++++++++++++++

- Backport the `sqlall` command.
- Sanitize sql statements for SimpleBlock.


0.1.8 (2017-09-20)
++++++++++++++++++

- Detect manual files if not stored in the 'manual' dir.
- Fix unicode error with SimpleBlock


0.1.7 (2017-09-06)
++++++++++++++++++

- Fix `get_applied_versions` result ordering.


0.1.6 (2017-09-05)
++++++++++++++++++

- Add tests for Django 1.11.


0.1.5 (2017-05-24)
++++++++++++++++++

- Fix showfixtures command for Django 1.10.


0.1.4 (2017-05-10)
++++++++++++++++++

- Do not fail if fixtures do not exist.
  Use the closest fixtures for DB init and flush command.
- Add support of python3.


0.1.3 (2017-04-18)
++++++++++++++++++

- Use a Block if the sql file contains a 'ALTER TYPE' instruction
  Add a setting to customize the files to run in a Block.


0.1.2 (2017-04-13)
++++++++++++++++++

- Use a Block if the sql file contains a CONCURRENTLY instruction.


0.1.1 (2017-04-11)
++++++++++++++++++

- Add the possibility to configure the current version detector.


0.1.0 (2017-03-28)
++++++++++++++++++

- First release on PyPI.
