.. :changelog:

History
-------

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
