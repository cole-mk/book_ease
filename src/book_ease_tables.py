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

    @staticmethod
    def init_table(con: sqlite3.Connection):
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

    @staticmethod
    def set(con: sqlite3.Connection,
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

    @staticmethod
    def get(con: sqlite3.Connection,
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

    @staticmethod
    def clear_attribute(con: sqlite3.Connection,
                        category: str,
                        attribute: str):
        """delete all rows that from settings_numeric that contain category and attribute"""

        sql = """
            DELETE FROM settings_numeric
            WHERE category = (?)
            AND attribute = (?)
            """
        con.execute(sql, (category, attribute))

    @staticmethod
    def clear_value(con: sqlite3.Connection,
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

    @staticmethod
    def update_row_by_id(con: sqlite3.Connection,
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

    @staticmethod
    def update_value_by_id(con: sqlite3.Connection,
                           id_: int,
                           value: int) -> bool:
        """update the value column of the row that contains id_"""

        sql = """
            UPDATE settings_numeric
            SET value = (?)
            WHERE rowid = (?)
            """
        cur = con.execute(sql, (value, id_))
        return bool(cur.rowcount)

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

    @staticmethod
    def init_table(con: sqlite3.Connection):
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

    @staticmethod
    def set(con: sqlite3.Connection,
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

    @staticmethod
    def get(con: sqlite3.Connection,
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

    @staticmethod
    def clear_attribute(con: sqlite3.Connection,
                        category: str,
                        attribute: str):
        """delete all rows that from settings_string that contain category and attribute"""

        sql = """
            DELETE FROM settings_string
            WHERE category = (?)
            AND attribute = (?)
            """
        con.execute(sql, (category, attribute))

    @staticmethod
    def delete_row_by_id(con: sqlite3.Connection,
                         id_: int):
        """delete all rows that from settings_string that contain category and attribute"""

        sql = """
            DELETE FROM settings_string
            WHERE id_ = (?)
            """
        con.execute(sql, (id_,))

    @staticmethod
    def clear_value(con: sqlite3.Connection,
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

    @staticmethod
    def clear_category(con: sqlite3.Connection,
                       category: str):
        """delete all rows from settings_string that contain category."""

        sql = """
            DELETE FROM settings_string
            WHERE category = (?)
            """
        con.execute(sql, (category,))

    @staticmethod
    def get_category(con: sqlite3.Connection,
                     category: str) -> list[sqlite3.Row]:
        """get all rows that match category"""

        sql = """
            SELECT * FROM settings_string
            WHERE category = (?)
            """
        cur = con.execute(sql, (category,))
        return cur.fetchall()

    @staticmethod
    def update_row_by_id(con: sqlite3.Connection,
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


class SettingsNumericDBI:
    """
    A simple adapter for the SettingsNumeric table class.
    This should allow other classes to store and retrieve data in a manner similar to using configparser.
    """

    @staticmethod
    def get(category: str, attribute: str) -> int | None:
        """
        Retrieve a single numeric value from SettingsNumeric where row contains category and attribute.

        Returns None if a row matching  category:attribute is not found in table.
        """
        with DB_CONNECTION_MANAGER.query() as con:
            value = SettingsNumeric.get(con, category, attribute)
        return value[0]['value'] if value else None

    @staticmethod
    def set(category: str, attribute: str, value: int) -> int:
        """
        Update the first row that matches category and attribute or insert new row.
        return the id of the modified row.
        """
        with DB_CONNECTION_MANAGER.query() as con:
            if id_ := SettingsNumeric.update_value(con, category, attribute, value) is None:
                id_ = SettingsNumeric.set(con, category, attribute, value)
        return id_

    @staticmethod
    def get_bool(category: str, attribute: str) -> bool | None:
        """
        Retrieve a boolean value from SettingsNumeric
        Returns None if a row matching  category:attribute is not found in table
        """
        val = SettingsNumericDBI.get(category, attribute)
        return bool(val) if val is not None else None

    @staticmethod
    def set_bool(category: str, attribute: str, value: bool) -> int:
        """
        Set a boolean value in table settings_numeric.
        This is just a convenience function added for readability in the caller classes.

        Returns the rowid of the modified row.
        """
        return SettingsNumericDBI.set(category, attribute, int(value))


class BookMarks:
    """
    sql queries for table book_marks
    This table stores the list of bookmarks displayed in the BookMark View.
    """

    @staticmethod
    def init_table(con: sqlite3.Connection):
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

    @staticmethod
    def get_all_rows_sorted_by_index_asc(con: sqlite3.Connection) -> list['sqlite3.Row']:
        """Get all rows in the book_marks table"""

        sql = """
            SELECT * FROM book_marks
            ORDER BY
            index_ ASC
            """
        cur = con.execute(sql)
        return cur.fetchall()

    @staticmethod
    def update_row_by_id(con: sqlite3.Connection,
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

    @staticmethod
    def delete_rows_not_in_ids(con: sqlite3.Connection, ids: tuple):
        """Delete any row whose id_ column is not included in ids."""

        sql = f"""
            DELETE FROM book_marks
            WHERE
            id_ NOT IN ({','.join(['?'] * len(ids))})
            """
        con.execute(sql, ids)

    @staticmethod
    def set(con: sqlite3.Connection,
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


def _init_database(connection_manager: sqlite_tools.DBConnectionManager):
    """Ensure that the correct tables have been created inside the connected database"""
    with connection_manager.create_connection() as conn:
        SettingsNumeric.init_table(conn)
        SettingsString.init_table(conn)
        BookMarks.init_table(conn)


# The connection manager that is accessible from outside the module
DB_CONNECTION_MANAGER: DBConnectionManager = DBConnectionManager(__DATABASE_FILE_PATH)

# create the required tables in memory.
_init_database(DB_CONNECTION_MANAGER)

if __name__ == '__main__':
    import sys
    sys.exit()
