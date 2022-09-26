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

"""This module contains various helper classes specific to using an sqlite database."""

import sqlite3
from pathlib import Path
import contextlib


class DBConnectionManager:
    """
    Provide nested context management of database connections.

    Query context allows a single query to be executed before committing or rolling back a transaction.
    When nested inside another query context, query simply returns the instance connection and defers context
    management entirely to the parent query.

    Nested query context allows multiple queries to be executed before committing or rolling back a transaction.

    database is the path to the database or string representing an in memory database.
    """

    def __init__(self, database: Path | str):
        self.database = database
        self.con = self.create_connection()
        self.query_count = 0

    def create_connection(self) -> sqlite3.Connection:
        """Create an sqlite3 connection object and return it."""
        con = sqlite3.connect(self.database, isolation_level=None)
        con.row_factory = sqlite3.Row
        return con

    @contextlib.contextmanager
    def query(self) -> sqlite3.Connection:
        """
        Query context allows a single query to be executed before committing or rolling back a transaction.
        When nested inside another query context, query simply returns the instance connection and defers context
        management entirely to the parent query.

        Nested query context allows multiple queries to be executed before committing or rolling back a transaction.
        """
        self.query_count += 1
        if self.query_count > 1:
            # Inner instance of nested context
            try:
                yield self.con
            finally:
                self.query_count -= 1
        else:
            # Outer instance of nested context
            self.con.execute('BEGIN')
            try:
                yield self.con
            except Exception:
                self.con.rollback()
                raise
            finally:
                self.con.commit()
                self.query_count -= 1
