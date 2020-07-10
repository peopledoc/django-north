import logging

from django.conf import settings

import six
import sqlparse

from django_north.management.migrations import is_manual_migration

logger = logging.getLogger(__name__)


class SQLRunnerException(Exception):
    pass


def clean_sql_code(code):
    output = ""
    for line in code.split("\n"):
        stripped_line = line.strip()
        if stripped_line == "\\timing":
            continue
        if stripped_line.startswith("--"):
            continue
        if stripped_line == "\\gset":
            continue
        if stripped_line == "\\if":
            continue
        if stripped_line == "\\endif":
            continue
        if stripped_line == "\\gexec":
            continue
        output += stripped_line + "\n"
    return output


class Block(object):
    def __init__(self):
        self.closed = False
        self.content = ""

    def append_line(self, line):
        if self.closed:
            raise SQLRunnerException("Block closed !")
        self.content += line

    def close(self):
        if self.closed:
            raise SQLRunnerException("Block closed !")
        self.closed = True

    def is_closed(self):
        return self.closed

    def run(self, connection):
        statements = sqlparse.parse(self.content)

        content = "".join((six.text_type(stmt) for stmt in statements))
        if content != self.content:
            raise SQLRunnerException("sqlparse failed to properly split input")

        rows = 0
        with connection.cursor() as cursor:
            for statement in statements:
                if clean_sql_code(str(statement)).strip() in ("", ";"):
                    # Sometimes sqlparse keeps the empty lines here,
                    # this could negatively affect libpq
                    continue
                logger.debug("Running one statement... <<%s>>", str(statement))
                cursor.execute(str(statement).replace("\\timing\n", ""))
                logger.debug("Affected %s rows", cursor.rowcount)
                rows += cursor.rowcount
        return rows


class SimpleBlock(Block):
    def run(self, connection):
        with connection.cursor() as cursor:
            statements = clean_sql_code(self.content)
            cursor.execute(statements)


class DiscardBlock(SimpleBlock):
    def __init__(self):
        super(DiscardBlock, self).__init__()
        self.content = "DISCARD ALL;"


class MetaBlock(Block):
    def __init__(self, command):
        super(MetaBlock, self).__init__()
        self.command = command
        if command != "do-until-0":
            raise SQLRunnerException("Unexpected command {}".format(command))

    def run(self, db):
        total_rows = 0
        # Simply call super().run in a loop...
        delta = 0
        batch_delta = -1
        while batch_delta != 0:
            batch_delta = 0
            logger.debug("Running one block in a loop")
            delta = super(MetaBlock, self).run(db)
            if delta > 0:
                total_rows += delta
                batch_delta = delta
            logger.debug("Batch delta done : %s", batch_delta)
        return total_rows


class Script(object):
    def __init__(self, file_handler):
        is_manual = is_manual_migration(file_handler)
        if is_manual:
            self.block_list = [Block()]
        elif self.contains_non_transactional_keyword(file_handler):
            self.block_list = [Block()]
        else:
            self.block_list = [SimpleBlock()]
        for line in file_handler:
            if line.startswith("--meta-psql:") and is_manual:
                self.block_list[-1].close()
                command = line.split(":")[1].strip()
                if command == 'done':
                    # create a new basic block
                    self.block_list.append(Block())
                else:
                    # create a new meta block
                    self.block_list.append(MetaBlock(command))
            else:
                self.block_list[-1].append_line(line)
        self.block_list[-1].close()

    def run(self, db):
        for block in self.block_list:
            block.run(db)

        # RUN a DISCARD ALL command at the end of each script.
        # By default, set to True for security reasons.
        discard_all = getattr(settings, 'NORTH_DISCARD_ALL', True)
        if discard_all:
            DiscardBlock().run(db)

    def contains_non_transactional_keyword(self, file_handler):
        keywords = getattr(
            settings, 'NORTH_NON_TRANSACTIONAL_KEYWORDS',
            ['CONCURRENTLY', 'ALTER TYPE', 'VACUUM'])
        for line in file_handler:
            for kw in keywords:
                if kw.lower() in line.lower():
                    file_handler.seek(0)
                    return True

        file_handler.seek(0)
        return False
