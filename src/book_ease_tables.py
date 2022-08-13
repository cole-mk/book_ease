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


from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path
from sqlite_tools import DBConnectionManager
if TYPE_CHECKING:
    import sqlite3


# set database file creating config directory
config_dir = Path.home() / '.config' / 'book_ease'
db_dir = config_dir / 'data'
db_dir.mkdir(mode=511, parents=True, exist_ok=True)
db = db_dir / 'book_ease.db'


DB_CONNECTION_MANAGER = DBConnectionManager(db)


class SettingsNumeric:
    """
    sql queries for table settings_numeric
    This table stores key value pairs where value is int and bool data types
    """

    def __init__(self):
        con = DB_CONNECTION_MANAGER.create_connection()
        with con:
            self.__init_table(con)

    def __init_table(self, con: sqlite3.Connection):
        """Create table settings_numeric in book_ease.db"""
        sql = """
            CREATE TABLE IF NOT EXISTS settings_numeric (
                category  STRING,
                attribute STRING,
                value     INT
            )
            """
        con.execute(sql)

    def set(self,
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

    def get(self,
            con: sqlite3.Connection,
            category: str,
            attribute: str) -> list[sqlite3.Row]:

        """get all entries that match the category and attribute columns"""
        sql = """
            SELECT * FROM settings_numeric
            WHERE category = (?)
            AND attribute = (?)
            """
        cur = con.execute(sql,(category, attribute))
        return cur.fetchall()

    def clear_attribute(self,
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

    def clear_value(self,
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


class SettingsString:
    """
    sql queries for table settings_string
    This table stores key value pairs where value is string data type
    """

    def __init__(self):
        con = DB_CONNECTION_MANAGER.create_connection()
        with con:
            self.__init_table(con)

    def __init_table(self, con: sqlite3.Connection):
        """Create table settings_string in book_ease.db"""
        sql = """
            CREATE TABLE IF NOT EXISTS settings_string (
                category  STRING,
                attribute STRING,
                value     STRING
            )
            """
        con.execute(sql)

    def set(self,
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

    def get(self,
            con: sqlite3.Connection,
            category: str,
            attribute: str) -> list[sqlite3.Row]:

        """get all entries from settings_string that match the category and attribute columns"""
        sql = """
            SELECT * FROM settings_string
            WHERE category = (?)
            AND attribute = (?)
            """
        cur = con.execute(sql,(category, attribute))
        return cur.fetchall()

    def clear_attribute(self,
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

    def clear_value(self,
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


if __name__ == '__main__':
    import sys
    sys.exit()
