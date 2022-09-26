# -*- coding: utf-8 -*-
#
#  untitled.py
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
#
# pylint: disable=redefined-outer-name
# disable redefined-outer-name because it is required to redefine an outer name to use pytest fixtures.
#
# pylint: disable=broad-except
# disable broad-except because one test requires raising and catching the most general exception possible.
#

"""This module tests class sqlite_tools.DBConnectionManager"""
import contextlib
from pathlib import Path
import sqlite3
import pytest
import sqlite_tools


@pytest.fixture
def test_db_str():
    """Database connection string"""
    return "mytestdatabase.db"


@pytest.fixture
def sql_create_test_table():
    """Sql statement to create a database table or testing"""
    sql = """
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            test_col TEXT UNIQUE NOT NULL
        )
        """
    return sql


@pytest.fixture
@contextlib.contextmanager
def test_db(test_db_str, sql_create_test_table):
    """
    Context in which a test database is created with an empty test table and then destroyed on exiting the context.
    Yields the database connection string.
    """
    Path(test_db_str).unlink(missing_ok=True)
    with sqlite3.connect(test_db_str) as con:
        con.execute(sql_create_test_table)
    try:
        yield test_db_str
    finally:
        Path(test_db_str).unlink(missing_ok=True)


class TestCreateConnection:
    """Test method DBConnectionManager.create_connection"""

    def test_returns_sqlite3_connection(self):
        """Show that create_connection returns a connection of type sqlite3.Connection"""
        db_con_mgr = sqlite_tools.DBConnectionManager(":memory:")
        con = db_con_mgr.create_connection()
        assert isinstance(con, sqlite3.Connection)

    def test_sets_row_factory(self):
        """Assert that the connection's row factory is set to sqlite3.Row"""
        db_con_mgr = sqlite_tools.DBConnectionManager(":memory:")
        con = db_con_mgr.create_connection()
        assert con.row_factory is sqlite3.Row


class TestQuery:
    """Test method DBConnectionManager.query"""

    def test_yields_a_context(self):
        """Assert that DBConnectionManager.query creates a context"""
        db_con_mgr = sqlite_tools.DBConnectionManager(":memory:")
        with db_con_mgr.query():
            assert True

    def test_yields_sqlite3_connection_when_not_nested(self):
        """Assert that an outer context yields an sqlite connection."""
        db_con_mgr = sqlite_tools.DBConnectionManager(":memory:")
        with db_con_mgr.query() as con:
            assert isinstance(con, sqlite3.Connection)

    def test_yields_existing_sqlite3_connection_when_nested(self):
        """Assert that an inner context(nested) yields the same connection that was used by the outer context"""
        db_con_mgr = sqlite_tools.DBConnectionManager(":memory:")
        with db_con_mgr.query() as con1:
            with db_con_mgr.query() as con2:
                assert isinstance(con2, sqlite3.Connection)
                assert con2 is con1

    def test_commits_when_not_nested(self, test_db):
        """Assert that a non-nested context commits its transaction."""
        with test_db as test_db_str:
            db_con_mgr = sqlite_tools.DBConnectionManager(test_db_str)
            with db_con_mgr.query() as con:
                con.execute('INSERT INTO  test_table(test_col) Values (?)', (1,))
            # Check that the sample data was committed.
            conn = sqlite3.Connection(test_db_str)
            cur = conn.execute('SELECT * FROM test_table')
            assert len(cur.fetchall()) == 1


    def test_inner_context_defers_commit_when_nested(self, test_db):
        """Assert that an inner context(nested) defers transaction handling to the outer context."""
        with test_db as test_db_str:
            db_con_mgr = sqlite_tools.DBConnectionManager(test_db_str)
            with db_con_mgr.query():
                with db_con_mgr.query() as con2:
                    con2.execute('INSERT INTO  test_table(test_col) Values (?)', (1,))
                # there should be no data to retrieve
                cur = sqlite3.Connection(test_db_str).execute('SELECT * FROM test_table')
                assert len(cur.fetchall()) == 0

    def test_outer_context_commits_when_nested(self, test_db):
        """
        Assert that an outer context commits its transaction when the queries were made in an inner
        context.
        """
        with test_db as test_db_str:
            db_con_mgr = sqlite_tools.DBConnectionManager(test_db_str)
            with db_con_mgr.query():
                with db_con_mgr.query() as con_inner:
                    con_inner.execute('INSERT INTO  test_table(test_col) Values (?)', (1,))
            cur = sqlite3.Connection(test_db_str).execute('SELECT * FROM test_table')
            assert len(cur.fetchall()) == 1

    def test_rolls_back_on_exception_when_not_nested(self, test_db):
        """Assert that a single non-nested context rolls back a transaction after an error occurs."""
        with test_db as test_db_str:
            db_con_mgr = sqlite_tools.DBConnectionManager(test_db_str)
            try:
                with db_con_mgr.query() as con:
                    sql = """
                        INSERT INTO test_table(test_col)
                        Values (?)
                        """
                    con.execute(sql, ('1',))
                    con.execute(sql, ('1',))
            except sqlite3.IntegrityError:
                pass
            finally:
                con = sqlite3.connect(test_db_str)
                cur = con.execute('SELECT * FROM test_table')
                assert len(cur.fetchall()) == 0

    def test_rolls_back_all_on_inner_exception_when_nested(self, test_db):
        """Assert that an outer context rolls back all statements, including those made from an inner context"""
        with test_db as test_db_str:
            try:
                db_con_mgr = sqlite_tools.DBConnectionManager(test_db_str)
                with db_con_mgr.query() as con_outer:
                    con_outer.execute('INSERT INTO test_table(test_col) VALUES (1)')
                    with db_con_mgr.query() as con_inner:
                        con_inner.execute('INSERT INTO test_table(test_col) VALUES (2)')
                        raise Exception
            except Exception:
                pass
            finally:
                con = sqlite3.connect(test_db_str)
                cur = con.execute('SELECT * FROM test_table')
                assert len(cur.fetchall()) == 0
