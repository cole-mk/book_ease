# -*- coding: utf-8 -*-
#
#  test_abt_join_track_file_pl_track_player_position.py
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

from test.audio_book_tables import audio_book_tables_test_data
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


class TestGetPathPositionByPlaylistId:
    """Test method get_path_position_by_playlist_id"""

    def test_returns_row_when_playlist_id_found(self, in_mem_db_str):
        """Show that method returns path and position when playlist_id is found in table player_position."""
        db_con_man = sqlite_tools.DBConnectionManager(in_mem_db_str)
        with db_con_man.query() as con:
            sample_data = init_test_data_base(con)
            playlist_id = sample_data.player_position_list[0]['playlist_id']
            result = audio_book_tables.JoinTrackFilePlTrackPlayerPosition.get_path_position_by_playlist_id(
                con, playlist_id
            )
            assert result['position'] == sample_data.player_position_list[0]['position']
            assert result['path'] == sample_data.track_file_list[0]['path']

    def test_returns_none_when_playlist_id_not_found(self, in_mem_db_str):
        """Show that method returns None when playlist_id is not found in table player_position."""
        db_con_man = sqlite_tools.DBConnectionManager(in_mem_db_str)
        with db_con_man.query() as con:
            sample_data = init_test_data_base(con)
            playlist_id = 1
            for i in sample_data.player_position_list:
                if playlist_id <= i['playlist_id']:
                    playlist_id += 1
            result = audio_book_tables.JoinTrackFilePlTrackPlayerPosition.get_path_position_by_playlist_id(
                con, playlist_id
            )
            assert result is None
