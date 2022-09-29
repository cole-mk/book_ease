# -*- coding: utf-8 -*-
#
#  test_abt_player_position.py
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
# pylint: disable=too-few-public-methods
#

"""
Test for class audio_book_tables.PlayerPosition.
This test requires sqlite_tools.DBConnectionManager, because it does matter that the connection is in the exact same
state as what's being used in the program, ie foreign keys.
"""

import sqlite3
from test import audio_book_tables_test_data
import pytest
import audio_book_tables
import sqlite_tools


@pytest.fixture
def in_mem_db_str() -> str:
    """connection string for an in memory database"""
    return ":memory:"

def init_test_data_base(con) -> audio_book_tables_test_data.SampleDatabaseCreator:
    """initialize the necessary tables for this test"""
    s_db_c = audio_book_tables_test_data.SampleDatabaseCreator()
    s_db_c.populate_track_file(con)
    s_db_c.populate_playlist(con)
    s_db_c.populate_pl_track(con)
    s_db_c.populate_player_position(con)
    return s_db_c




class TestInitTable:
    """Test for method PlayerPosition.__init__."""

    def test_creates_table_with_correct_columns(self, in_mem_db_str):
        """Show that the table gets created with the correct columns."""
        db_con_man = sqlite_tools.DBConnectionManager(in_mem_db_str)
        with db_con_man.query() as con:
            audio_book_tables.PlayerPosition.init_table(con)
            sql = """
                pragma table_info(player_position)
                """
            cur = con.execute(sql)
            data = [(row['name'], row['type']) for row in cur.fetchall()]
            assert ('pl_track_id', 'INTEGER') in data
            assert ('position', 'INTEGER') in data
            assert ('playlist_id', 'INTEGER') in data


class TestUpsertRow:
    """Test for method PlayerPosition.upsert_row"""

    def test_upsert_row_fails_without_matching_pl_track_foreign_key(self, in_mem_db_str):
        """Show that the method upsert_row fails when the pl_track_id doesn't exist in table pl_track"""
        db_con_man = sqlite_tools.DBConnectionManager(in_mem_db_str)
        with db_con_man.query() as con:
            sample_data = init_test_data_base(con)
            playlist_id = sample_data.playlist_list[1]['id']

            pl_track_id = 1
            # set pl_track_id to a number that is known to not be in the database
            for row in sample_data.pl_track_list:
                if pl_track_id <= row['id']:
                    pl_track_id = row['id'] + 1
            with pytest.raises(sqlite3.IntegrityError):
                audio_book_tables.PlayerPosition.upsert_row(
                    con, pl_track_id=pl_track_id, playlist_id=playlist_id, position=200
                )

    def test_upsert_row_fails_without_matching_playlist_foreign_key(self, in_mem_db_str):
        """Show that the method upsert_row fails when the pl_track_id doesn't exist in table pl_track"""
        db_con_man = sqlite_tools.DBConnectionManager(in_mem_db_str)
        with db_con_man.query() as con:
            sample_data = init_test_data_base(con)
            pl_track_id = sample_data.pl_track_list[0]['id']
            playlist_id = 1
            # set pl_track_id to a number that is known to not be in the database
            for row in sample_data.playlist_list:
                if playlist_id <= row['id']:
                    playlist_id = row['id'] + 1
            with pytest.raises(sqlite3.IntegrityError):
                audio_book_tables.PlayerPosition.upsert_row(
                    con, pl_track_id=pl_track_id, playlist_id=playlist_id, position=200
                )

    def test_upsert_row_updates_row_when_duplicate_playlist_id(self, in_mem_db_str):
        """
        Assert that upsert_row updates the existing row where playlist_id already exists.
        This checks that both position and pl_track_id are changed
        """
        db_con_man = sqlite_tools.DBConnectionManager(in_mem_db_str)
        with db_con_man.query() as con:
            sample_data = init_test_data_base(con)
            # initial conditions
            cur = con.execute('SELECT * FROM player_position')
            rows = cur.fetchall()
            initial_number_of_rows = len(rows)
            initial_pl_track_id = rows[0]['pl_track_id']
            initial_position = sample_data.player_position_list[0]['position']
            # test data
            pl_track_id = sample_data.pl_track_list[1]['id']
            playlist_id = sample_data.playlist_list[0]['id']
            position = initial_position + 200
            # test
            audio_book_tables.PlayerPosition.upsert_row(
                con, pl_track_id=pl_track_id, playlist_id=playlist_id, position=position
            )
            # validate
            cur = con.execute('SELECT * FROM player_position')
            rows = cur.fetchall()

            assert len(rows) == initial_number_of_rows, f'the number of rows increased by: ' \
                                                        f'{len(rows) - initial_number_of_rows}' \
                                                        f'\nwhen it should have stayed the same'

            assert pl_track_id != initial_pl_track_id, 'invalid initial condition for test:' \
                                                       '\ninitial_pl_track_id and pl_track_id match\n'

            assert rows[0]['pl_track_id'] == pl_track_id, 'The pl_track_id did not get updated'

            assert rows[0]['position'] == position, 'The position did not get updated'

    def test_upsert_row_adds_new_row(self, in_mem_db_str):
        """
        Assert that upsert_row adds a new row to the table under ideal initial conditions:
        No rows with matching playlist_id.
        pl_track_id and  playlist_id both exist in their respective tables.
        position is given as int
        """
        db_con_man = sqlite_tools.DBConnectionManager(in_mem_db_str)
        with db_con_man.query() as con:
            # populate data
            sample_data = init_test_data_base(con)
            pl_track_id = sample_data.pl_track_list[2]['id']
            playlist_id = sample_data.playlist_list[1]['id']
            audio_book_tables.PlayerPosition.upsert_row(
                con, pl_track_id=pl_track_id, playlist_id=playlist_id, position=300
            )
            # validate
            sql = """
                SELECT * FROM player_position
                """
            cur = con.execute(sql)
            rows = cur.fetchall()
            assert len(rows) == 2, 'No new rows were added to table player_position'


class TestGetRowByID:
    """Tests for method PlayerPosition.get_row_by_playlist_id"""

    def test_returns_row_when_playlist_id_found(self, in_mem_db_str):
        """
        Show that the method returns an entire row containing playlist_id,
        provided that playlist_id is found in the table.
        """
        db_con_man = sqlite_tools.DBConnectionManager(in_mem_db_str)
        with db_con_man.query() as con:
            sample_data = init_test_data_base(con)
            playlist_id = sample_data.player_position_list[0]['playlist_id']
            test_row = audio_book_tables.PlayerPosition.get_row_by_playlist_id(con, playlist_id)
            # sample_data.player_position_list[0] contains an id column that is implicit in the table
            # and not included in the row result.
            del sample_data.player_position_list[0]['id']
            assert dict(test_row) == sample_data.player_position_list[0]

    def test_returns_none_when_playlist_id_not_found(self, in_mem_db_str):
        """Show that the method returns None, provided that playlist_id is not found in the table."""
        db_con_man = sqlite_tools.DBConnectionManager(in_mem_db_str)
        with db_con_man.query() as con:
            sample_data = init_test_data_base(con)
            # find a playlist_id that is known to not be in the table
            playlist_id = 1
            for row in sample_data.player_position_list:
                if playlist_id <= row['playlist_id']:
                    playlist_id += 1
            test_row = audio_book_tables.PlayerPosition.get_row_by_playlist_id(con, playlist_id)
            assert test_row is None
