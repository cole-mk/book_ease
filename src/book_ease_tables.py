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
import abc


"""
This module is responsible for reading and writing to the book_ease.db.
book_ease.db stores all application data that is not directly related to playlists.
"""


from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path
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
                value     INT
            )
            """
        con.execute(sql)

    @classmethod
    def set(cls,
            con: sqlite3.Connection,
            category: str,
            attribute: str,
            value: int) -> int:
        """add entry row to table settings_numeric"""

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
            SET category = (?)
                attribute = (?)
                value = (?)
            WHERE
                rowid = (?)
            """
        con.execute(sql, (category, attribute, value, id_))


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
                value     STRING
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


# initialize the db connection and ensure that the database is set up properly
DB_CONNECTION_MANAGER = DBConnectionManager(db)
with DB_CONNECTION_MANAGER.create_connection() as conn:
    SettingsNumeric.init_table(conn)
    SettingsString.init_table(conn)


class _TableLoader(metaclass=abc.ABCMeta):
    """
    This is an interface class that defines the methods required to move table data back and forth between the copies
    of the db on disc and in ram:

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

    @abc.abstractmethod
    def load_to_mem(self):
        raise NotImplementedError

    @abc.abstractmethod
    def save_to_hd(self):
        raise NotImplementedError

    @abc.abstractmethod
    def clear_from_mem(self):
        raise NotImplementedError


if __name__ == '__main__':
    import sys
    sys.exit()
