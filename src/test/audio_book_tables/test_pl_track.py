# -*- coding: utf-8 -*-
#
#  test_pl_track.py
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
Test for class audio_book_tables.PlTrack.
This test requires sqlite_tools.DBConnectionManager, because it does matter that the connection is in the exact same
state as what's being used in the program, ie foreign keys.
"""

from test.audio_book_tables import sample_data
import pytest
import audio_book_tables
import sqlite_tools


@pytest.fixture
def in_mem_db_str() -> str:
    """connection string for an in memory database"""
    return ":memory:"


def init_test_data_base(con) -> sample_data.SampleDatabaseCreator:
    """initialize the necessary tables for this test"""
    s_db_c = sample_data.SampleDatabaseCreator()
    s_db_c.populate_track_file(con)
    s_db_c.populate_playlist(con)
    s_db_c.populate_pl_track(con)
    return s_db_c


class TestGetTrackCountByPlaylistId:
    """Unit test for method get_track_count_by_playlist_id()"""

    def test_returns_correct_count_of_rows_with_matching_playlist_ids(self, in_mem_db_str):
        """
        Assert that get_track_count_by_playlist_id() counts the rows that match playlist_id.
        get_track_count_by_playlist_id() should return an int.
        """
        db_con_man = sqlite_tools.DBConnectionManager(in_mem_db_str)
        with db_con_man.query() as con:
            sample_data_ = init_test_data_base(con)

            playlist_id = sample_data_.playlist_list[0]['id']
            track_count = audio_book_tables.PlTrack.get_track_count_by_playlist_id(con, playlist_id)
            assert track_count == 2, 'Failed to count the correct number of pl_tracks.'

            playlist_id = sample_data_.playlist_list[1]['id']
            track_count = audio_book_tables.PlTrack.get_track_count_by_playlist_id(con, playlist_id)
            assert track_count == 1, 'Failed to count the correct number of pl_tracks.'
