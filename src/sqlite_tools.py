# -*- coding: utf-8 -*-
#
#  sqlite_tools.py
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
"""This module contains various helper classes specific to using an sqlite db."""
import sqlite3
from pathlib import Path


class DBConnectionManager:
    """
    Provide database connection management for multi queries.

    database is the path to the database or string representing an in memory database
    connection_kwargs are additional args to be passed to sqlite3.connect() during self.create_connection()
    """

    def __init__(self, database: Path | str, **connection_kwargs):
        self.database = database
        self.con = None
        self.connection_kwargs = connection_kwargs

    def create_connection(self) -> sqlite3.Connection:
        """ create a sqlite3 connection object and return it"""
        con = sqlite3.connect(self.database, isolation_level=None, **self.connection_kwargs)
        con.row_factory = sqlite3.Row
        return con

    def multi_query_begin(self):
        """
        create a semi-persistent connection
        for executing multiple transactions
        """
        if self.con is not None:
            raise RuntimeError('connection already exists')
        self.con = self.create_connection()
        self.con.execute('BEGIN')

    def multi_query_end(self):
        """commit and close connection of a multi_query"""
        if self.con is None:
            raise RuntimeError('connection doesn\'t exist')
        self.con.commit()
        self.con.close()
        self.con = None

    def query_begin(self) -> sqlite3.Connection:
        """
        get an sqlite connection object
        returns self.con if a multi_query is in effect.
        Otherwise, create and return a new connection
        """
        if self.con is None:
            return self.create_connection()
        return self.con

    def query_end(self, con: sqlite3.Connection):
        """
        commit and close connection if a multi_query
        is not in effect.
        """
        if con is not self.con:
            con.commit()
            con.close()
