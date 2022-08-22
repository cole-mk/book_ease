# -*- coding: utf-8 -*-
#
#  book_ease_tables.py
#
#  This file is part of book_ease.
#
#  Copyright 2021 mark cole <mark@capstonedistribution.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.


"""
This module is responsible for reading and writing to the book_ease.db.
book_ease.db stores all application data that is not directly related to playlists.
"""

# disable=too-many-arguments because this module is mostly sql queries, some of which set entire rows at a time.
# pylint: disable=too-many-arguments


from __future__ import annotations
import abc
from typing import TYPE_CHECKING
from pathlib import Path
import sqlite_tools
from sqlite_tools import DBConnectionManager
if TYPE_CHECKING:
    import sqlite3


# set database file creating config directory
__CONFIG_DIR = Path.home() / '.config' / 'book_ease'
__DATABASE_DIR = __CONFIG_DIR / 'data'
__DATABASE_DIR.mkdir(mode=511, parents=True, exist_ok=True)
__DATABASE_FILE_PATH = __DATABASE_DIR / 'book_ease.db'


class SettingsNumeric:
    """
    sql queries for table settings_numeric
    This table stores key value pairs where value is int and bool data types
    """

    @classmethod
    def init_table(cls, con: sqlite3.Connection):
        """Create table settings_numeric in book_ease.db"""

        sql = """
            CREATE TABLE IF NOT EXISTS settings_numeric (
                id_ INTEGER PRIMARY KEY,
                category  STRING,
                attribute STRING,
                value     INTEGER
            )
            """
        con.execute(sql)

    @classmethod
    def set(cls,
            con: sqlite3.Connection,
            category: str,
            attribute: str,
            value: int) -> int:
        """
        Add entry row to table settings_numeric.
        Returns the id of the newly created row.
        """

        sql = """
            INSERT INTO settings_numeric(category, attribute, value)
            VALUES (?,?,?)
            """
        cur = con.execute(sql, (category, attribute, value))
        return cur.lastrowid

    @classmethod
    def get(cls,
            con: sqlite3.Connection,
            category: str,
            attribute: str) -> list[sqlite3.Row]:
        """get all entries that match the category and attribute columns"""

        sql = """
            SELECT * FROM settings_numeric
            WHERE category = (?)
            AND attribute = (?)
            """
        cur = con.execute(sql, (category, attribute))
        return cur.fetchall()

    @classmethod
    def clear_attribute(cls,
                        con: sqlite3.Connection,
                        category: str,
                        attribute: str):
        """delete all rows that from settings_numeric that contain category and attribute"""

        sql = """
            DELETE FROM settings_numeric
            WHERE category = (?)
            AND attribute = (?)
            """
        con.execute(sql, (category, attribute))

    @classmethod
    def clear_value(cls,
                    con: sqlite3.Connection,
                    category: str,
                    attribute: str,
                    value: int):
        """Delete row in settings_numeric"""

        sql = """
            DELETE FROM settings_numeric
            WHERE category = (?)
            AND attribute = (?)
            And value = (?)
            """
        con.execute(sql, (category, attribute, value))

    @classmethod
    def update_row_by_id(cls,
                         con: sqlite3.Connection,
                         id_: int,
                         category: str,
                         attribute: str,
                         value: int):
        """Find row by searching for id_, and then update the category, attribute, and value columns of that row."""

        sql = """
            Update settings_numeric
            SET category = (?),
                attribute = (?),
                value = (?)
            WHERE
                rowid = (?)
            """
        con.execute(sql, (category, attribute, value, id_))

    def update_value_by_id(self,
                           con: sqlite3.Connection,
                           id_: int,
                           value: int):
        """update the value column of the row that contains id_"""

        sql = """
            UPDATE settings_numeric
            SET value = (?)
            WHERE rowid = (?)
            """
        con.execute(sql, (value, id_))
    @staticmethod
    def update_value(con: sqlite3.Connection,
                     category: str,
                     attribute: str,
                     value: int) -> int | None:
        """
        Update the value column on the first row that matches category and attribute.
        returns rowid if the update was successful or None if no match was found.
        """

        updated_by_id = None
        sql = """
            SELECT * FROM settings_numeric
            WHERE category = (?)
            AND attribute = (?)
            """
        cur = con.execute(sql, (category, attribute))
        if row := cur.fetchone():
            updated_by_id = SettingsNumeric.update_value_by_id(con, row['id_'], value)
        return row['id_'] if updated_by_id else None


class SettingsString:
    """
    sql queries for table settings_string
    This table stores key value pairs where value is string data type
    """

    @classmethod
    def init_table(cls, con: sqlite3.Connection):
        """Create table settings_string in book_ease.db"""
        sql = """
            CREATE TABLE IF NOT EXISTS settings_string (
                category  STRING,
                attribute STRING,
                value     STRING,
                id_ INTEGER  PRIMARY KEY
            )
            """
        con.execute(sql)

    @classmethod
    def set(cls,
            con: sqlite3.Connection,
            category: str,
            attribute: str,
            value: str) -> int:
        """add entry row to table settings_string"""

        sql = """
            INSERT INTO settings_string(category, attribute, value)
            VALUES (?,?,?)
            """
        cur = con.execute(sql, (category, attribute, value))
        return cur.lastrowid

    @classmethod
    def get(cls,
            con: sqlite3.Connection,
            category: str,
            attribute: str) -> list[sqlite3.Row]:
        """get all entries from settings_string that match the category and attribute columns"""

        sql = """
            SELECT * FROM settings_string
            WHERE category = (?)
            AND attribute = (?)
            """
        cur = con.execute(sql, (category, attribute))
        return cur.fetchall()

    @classmethod
    def clear_attribute(cls,
                        con: sqlite3.Connection,
                        category: str,
                        attribute: str):
        """delete all rows that from settings_string that contain category and attribute"""

        sql = """
            DELETE FROM settings_string
            WHERE category = (?)
            AND attribute = (?)
            """
        con.execute(sql, (category, attribute))

    @classmethod
    def delete_row_by_id(cls,
                         con: sqlite3.Connection,
                         id_: int):
        """delete all rows that from settings_string that contain category and attribute"""

        sql = """
            DELETE FROM settings_string
            WHERE id_ = (?)
            """
        con.execute(sql, (id_,))

    @classmethod
    def clear_value(cls,
                    con: sqlite3.Connection,
                    category: str,
                    attribute: str,
                    value: str):
        """Delete row in settings_string"""

        sql = """
            DELETE FROM settings_string
            WHERE category = (?)
            AND attribute = (?)
            And value = (?)
            """
        con.execute(sql, (category, attribute, value))

    @classmethod
    def clear_category(cls,
                       con: sqlite3.Connection,
                       category: str):
        """delete all rows from settings_string that contain category."""

        sql = """
            DELETE FROM settings_string
            WHERE category = (?)
            """
        con.execute(sql, (category,))

    @classmethod
    def get_category(cls,
                     con: sqlite3.Connection,
                     category: str) -> list[sqlite3.Row]:
        """get all rows that match category"""

        sql = """
            SELECT * FROM settings_string
            WHERE category = (?)
            """
        cur = con.execute(sql, (category,))
        return cur.fetchall()

    @classmethod
    def update_row_by_id(cls,
                         con: sqlite3.Connection,
                         id_: int,
                         category: str,
                         attribute: str,
                         value: int):
        """Find row by searching for id_, and then update the category, attribute, and value columns of that row."""

        sql = """
            Update settings_string
            SET category = (?),
                attribute = (?),
                value = (?)
            WHERE
                id_ = (?)
            """
        con.execute(sql, (category, attribute, value, id_))


class BookMarks:
    """
    sql queries for table book_marks
    This table stores the list of bookmarks displayed in the BookMark View.
    """

    @classmethod
    def init_table(cls, con: sqlite3.Connection):
        """Create table settings_numeric in book_ease.db"""

        sql = """
            CREATE TABLE IF NOT EXISTS book_marks (
                id_ INTEGER PRIMARY KEY,
                name STRING,
                target STRING,
                index_ INTEGER
            )
            """
        con.execute(sql)

    @classmethod
    def get_all_rows_sorted_by_index_asc(cls, con: sqlite3.Connection) -> list['sqlite3.Row']:
        """Get all rows in the book_marks table"""

        sql = """
            SELECT * FROM book_marks
            ORDER BY
            index_ ASC
            """
        cur = con.execute(sql)
        return cur.fetchall()

    @classmethod
    def update_row_by_id(cls,
                         con: sqlite3.Connection,
                         id_: int,
                         name: str,
                         target: str,
                         index: int):
        """update all rows that match id_"""

        sql = """
            UPDATE book_marks
            SET name = (?),
                target = (?),
                index_ = (?)
            WHERE
                id_ = (?)
            """
        con.execute(sql, (name, target, index, id_))

    @classmethod
    def delete_rows_not_in_ids(cls, con: sqlite3.Connection, ids: tuple):
        """Delete any row whose id_ column is not included in ids."""

        sql = f"""
            DELETE FROM book_marks
            WHERE
            id_ NOT IN ({','.join(['?'] * len(ids))})
            """
        con.execute(sql, ids)

    @classmethod
    def set(cls,
            con: sqlite3.Connection,
            name: str,
            target: str,
            index: int) -> int:
        """Add a new row to table book_marks"""

        sql = """
            INSERT INTO book_marks(name, target, index_)
            VALUES (?, ?, ?)
            """
        cur = con.execute(sql, (name, target, index))
        return cur.lastrowid


def load_data():
    """Copy all data from book_ease.db into the in memory copy of the database"""
    DB_CONNECTION_MANAGER.multi_query_begin()
    _LoaderSettingsNumeric.clear_from_mem()
    _LoaderSettingsString.clear_from_mem()
    _LoaderBookMarks.clear_from_mem()
    _attach_book_ease_db()
    _LoaderSettingsNumeric.load_to_mem()
    _LoaderSettingsString.load_to_mem()
    _LoaderBookMarks.load_to_mem()
    DB_CONNECTION_MANAGER.con.commit()
    _detach_book_ease_db()
    DB_CONNECTION_MANAGER.multi_query_end()


def save_data():
    """Copy all data from the in memory copy of the database into book_ease.db"""
    DB_CONNECTION_MANAGER.multi_query_begin()
    _attach_book_ease_db()
    _LoaderSettingsNumeric.save_to_hd()
    _LoaderSettingsString.save_to_hd()
    _LoaderBookMarks.save_to_hd()
    # id_ values are now corrupted in the in memory database.
    _LoaderSettingsNumeric.clear_from_mem()
    _LoaderSettingsString.clear_from_mem()
    _LoaderBookMarks.clear_from_mem()
    DB_CONNECTION_MANAGER.con.commit()
    _detach_book_ease_db()
    DB_CONNECTION_MANAGER.multi_query_end()


def _attach_book_ease_db():
    """Attach the on disk database to the connection to the in-memory database"""
    con = DB_CONNECTION_MANAGER.query_begin()
    con.execute('ATTACH DATABASE ? AS database_hd', (str(__DATABASE_FILE_PATH),))
    DB_CONNECTION_MANAGER.query_end(con)


def _detach_book_ease_db():
    """Detach the on disk database from the connection to the in-memory database"""
    con = DB_CONNECTION_MANAGER.query_begin()
    con.execute('DETACH DATABASE database_hd')
    DB_CONNECTION_MANAGER.query_end(con)


def _init_database(connection_manager: sqlite_tools.DBConnectionManager):
    """Ensure that the correct tables have been created inside the connected database"""
    with connection_manager.create_connection() as conn:
        SettingsNumeric.init_table(conn)
        SettingsString.init_table(conn)
        BookMarks.init_table(conn)


# Initialize the on disk db connection and ensure that the database is set up properly.
__DB_CONNECTION_MANAGER_HD = DBConnectionManager(__DATABASE_FILE_PATH)
_init_database(__DB_CONNECTION_MANAGER_HD)


# The connection manager that is accessible from outside the module
DB_CONNECTION_MANAGER: DBConnectionManager = DBConnectionManager("file:mem_db?mode=memory&cache=shared", uri=True)


# Create persistent database connection that keeps the in memory database open for the duration of this module's
# existence. This connection must not be closed, because the in memory database will disappear, losing all data.
__PERSISTENT_IN_MEMORY_DATABASE_CONNECTION = DB_CONNECTION_MANAGER.create_connection()


# create the required tables in memory.
_init_database(DB_CONNECTION_MANAGER)


class _LoaderInterface(metaclass=abc.ABCMeta):
    """
    This is an interface class that defines the methods required to move table data back and forth between the copies
    of the db on disc and in ram.

    It is intended that the on disk database will be attached to the in memory database as database_hd elsewhere in the
    module. See _attach_book_ease_db and  _detach_book_ease_db. Then the data can be moved by copying from
    database_hd.table_name to/from table_name.
    ex:
    @classmethod
    def load_to_mem(cls):
        \"""Copy all data from book_ease.db:SettingsNumeric into the in memory copy of the database\"""
        con = DB_CONNECTION_MANAGER.query_begin()
        sql = \"""
            INSERT INTO settings_numeric
            SELECT * FROM database_hd.settings_numeric
            \"""
        con.execute(sql)
        DB_CONNECTION_MANAGER.query_end(con)

    Methods
    load_to_mem()
    save_to_hd()
    clear_from_mem()
    """

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'load_to_mem') and
                callable(subclass.load_to_mem) and
                hasattr(subclass, 'save_to_hd') and
                callable(subclass.save_to_hd) and
                hasattr(subclass, 'clear_from_mem') and
                callable(subclass.clear_from_mem) or
                NotImplemented)

    @classmethod
    @abc.abstractmethod
    def load_to_mem(cls):
        """Load database table data from the database on disc into an identical in memory database."""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def save_to_hd(cls):
        """Load database table data from the database in memory into an identical on disk database."""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def clear_from_mem(cls):
        """clear out all data in the in memory database"""
        raise NotImplementedError


class _LoaderSettingsString(_LoaderInterface):
    """Move SettingsNumeric data back and forth between the copies of the db on disc and in ram."""

    @classmethod
    def load_to_mem(cls):
        """Copy all data from book_ease.db:SettingsString into the in memory copy of the database"""
        con = DB_CONNECTION_MANAGER.query_begin()
        sql = """
            INSERT INTO settings_string
            SELECT * FROM database_hd.settings_string
            """
        con.execute(sql)
        DB_CONNECTION_MANAGER.query_end(con)

    @classmethod
    def save_to_hd(cls):
        """Copy all data from the in memory copy of SettingsString into book_ease.db:SettingsString"""
        con = DB_CONNECTION_MANAGER.query_begin()
        # first delete rows in the disk database who's id_col is not in the in memory database.
        sql = """
            DELETE FROM database_hd.settings_string
            WHERE
                id_ NOT IN(
                    SELECT id_
                    FROM settings_string
                )
            """
        con.execute(sql)
        # Replace any rows that have changed, or insert if id_ is not in database_hd.settings_numeric
        sql = """
            INSERT OR REPLACE INTO database_hd.settings_string
            SELECT * FROM settings_string
            EXCEPT
            SELECT * FROM database_hd.settings_string
            """
        con.execute(sql)
        DB_CONNECTION_MANAGER.query_end(con)

    @classmethod
    def clear_from_mem(cls):
        """clear all data from the in memory database"""
        con = DB_CONNECTION_MANAGER.query_begin()
        con.execute('DELETE FROM settings_string')
        DB_CONNECTION_MANAGER.query_end(con)


class _LoaderSettingsNumeric(_LoaderInterface):
    """Move SettingsNumeric data back and forth between the copies of the db on disc and in ram."""

    @classmethod
    def load_to_mem(cls):
        """Copy all data from book_ease.db:SettingsNumeric into the in memory copy of the database"""
        con = DB_CONNECTION_MANAGER.query_begin()
        sql = """
            INSERT INTO settings_numeric
            SELECT * FROM database_hd.settings_numeric
            """
        con.execute(sql)
        DB_CONNECTION_MANAGER.query_end(con)

    @classmethod
    def save_to_hd(cls):
        """Move all data from the in memory copy of SettingsNumeric into book_ease.db:SettingsNumeric"""
        con = DB_CONNECTION_MANAGER.query_begin()
        # first delete rows in the disk database who's id_col is not in the in memory database.
        sql = """
            DELETE FROM database_hd.settings_numeric
            WHERE
                id_ NOT IN(
                    SELECT id_
                    FROM settings_numeric
                )
            """
        con.execute(sql)
        # Replace any rows that have changed, or insert if id_ is not in database_hd.settings_numeric
        sql = """
            INSERT OR REPLACE INTO database_hd.settings_numeric
            SELECT * FROM settings_numeric
            EXCEPT
            SELECT * FROM database_hd.settings_numeric
            """
        con.execute(sql)
        DB_CONNECTION_MANAGER.query_end(con)

    @classmethod
    def clear_from_mem(cls):
        """clear all data from the in memory database"""
        con = DB_CONNECTION_MANAGER.query_begin()
        con.execute('DELETE FROM settings_numeric')
        DB_CONNECTION_MANAGER.query_end(con)


class _LoaderBookMarks(_LoaderInterface):
    """Move SettingsNumeric data back and forth between the copies of the db on disc and in ram."""

    @classmethod
    def load_to_mem(cls):
        """Copy all data from book_ease.db:book_marks into the in memory copy of the database"""
        con = DB_CONNECTION_MANAGER.query_begin()
        sql = """
            INSERT INTO book_marks
            SELECT * FROM database_hd.book_marks
            """
        con.execute(sql)
        DB_CONNECTION_MANAGER.query_end(con)

    @classmethod
    def save_to_hd(cls):
        """Move all data from the in memory copy of book_marks into book_ease.db:book_marks"""
        con = DB_CONNECTION_MANAGER.query_begin()
        # first delete rows in the disk database who's id_col is not in the in memory database.
        sql = """
            DELETE FROM database_hd.book_marks
            WHERE
                id_ NOT IN(
                    SELECT id_
                    FROM book_marks
                )
            """
        con.execute(sql)
        # Replace any rows that have changed, or insert if id_ is not in database_hd.book_marks
        sql = """
            INSERT OR REPLACE INTO database_hd.book_marks
            SELECT * FROM book_marks
            EXCEPT
            SELECT * FROM database_hd.book_marks
            """
        con.execute(sql)
        DB_CONNECTION_MANAGER.query_end(con)

    @classmethod
    def clear_from_mem(cls):
        """clear all data from the in memory database"""
        con = DB_CONNECTION_MANAGER.query_begin()
        con.execute('DELETE FROM book_marks')
        DB_CONNECTION_MANAGER.query_end(con)


if __name__ == '__main__':
    import sys
    sys.exit()
