# -*- coding: utf-8 -*-
#
#  test_player_player_dbi.py
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
# pylint: disable=too-few-public-methods
# Disabled because some of the tested methods only require one test

"""
Unit test for class player.PlayerDBI
"""
from unittest import mock
import sqlite3
import audio_book_tables
import player
import sqlite_tools


class TestGetSavedPosition:
    """Unit test for player.PlayerDBI.get_saved_position(playlist_id: int)"""

    @mock.patch.object(audio_book_tables, 'DB_CONNECTION', sqlite_tools.DBConnectionManager(":memory:"))
    @mock.patch.object(audio_book_tables.JoinTrackFilePlTrackPlayerPosition, 'get_path_position_by_playlist_id')
    def test_calls_get_path_position_by_playlist_id_with_correct_args(self, magic_mock):
        """
        show that audio_book_tables.JoinTrackFilePlTrackPlayerPosition.get_path_position_by_playlist_id is passed an
        sqlite3 Connection object and the playlist_id.
        """
        player_dbi = player.PlayerDBI()
        player_dbi.get_saved_position(1)
        assert isinstance(magic_mock.call_args.kwargs['con'], sqlite3.Connection)
        assert magic_mock.call_args.kwargs['playlist_id'] == 1

    @mock.patch.object(audio_book_tables, 'DB_CONNECTION', sqlite_tools.DBConnectionManager(":memory:"))
    @mock.patch.object(audio_book_tables.JoinTrackFilePlTrackPlayerPosition, 'get_path_position_by_playlist_id')
    def test_returns_position_data_object_when_get_path_position_by_playlist_id_returns_sqlite3_row(self, magic_mock):
        """
        Show that get_saved_position returns a PositionData object when
        audio_book_tables.JoinTrackFilePlTrackPlayerPosition.get_path_position_by_playlist_id
        returns an sqlite3.row object.
        """
        # sqlite3.row objects are accessed in the same way as dicts, which is sufficient similarity for this test.
        magic_mock.return_value = {'path': 'some/path', 'position': 69}
        player_dbi = player.PlayerDBI()
        val = player_dbi.get_saved_position(1)
        assert isinstance(val, player.PositionData)

    @mock.patch.object(audio_book_tables, 'DB_CONNECTION', sqlite_tools.DBConnectionManager(":memory:"))
    @mock.patch.object(audio_book_tables.JoinTrackFilePlTrackPlayerPosition, 'get_path_position_by_playlist_id')
    def test_returns_none_when_get_path_position_by_playlist_id_returns_none(self, magic_mock):
        """
        Show that get_saved_position returns None when
        audio_book_tables.JoinTrackFilePlTrackPlayerPosition.get_path_position_by_playlist_id
        returns None.
        """
        magic_mock.return_value = None
        player_dbi = player.PlayerDBI()
        val = player_dbi.get_saved_position(1)
        assert val is None


class TestSavePosition:
    """Unit test for player.PlayerDBI.save_position(pl_track_id: int, playlist_id: int, position: int)"""

    @mock.patch.object(audio_book_tables, 'DB_CONNECTION', sqlite_tools.DBConnectionManager(":memory:"))
    @mock.patch.object(audio_book_tables.PlayerPosition, 'upsert_row')
    def test_calls_upsert_row_with_correct_args(self, magic_mock):
        """Assert that save_position calls audio_book_tables.PlayerPosition.upsert_row with the correct kwargs"""
        player_dbi = player.PlayerDBI()
        player_dbi.save_position(pl_track_id=1, playlist_id=2, position=3)
        assert magic_mock.call_args.kwargs['pl_track_id'] == 1
        assert magic_mock.call_args.kwargs['playlist_id'] == 2
        assert magic_mock.call_args.kwargs['position'] == 3


class TestGetTrackIdPlTrackIdByNumber:
    """Unit test for player.PlayerDBI.get_pl_track_by_number(playlist_id: int, track_number: int) -> int"""

    @mock.patch.object(audio_book_tables, 'DB_CONNECTION', sqlite_tools.DBConnectionManager(":memory:"))
    @mock.patch.object(audio_book_tables.PlTrack, 'get_rows_by_playlist_id')
    def test_calls_abt_pl_track_get_rows_by_playlist_id(self, magic_mock):
        """Assert that get_pl_track_by_number calls PlTrack.get_rows_by_playlist_id with correct args"""
        playlist_id = 1
        track_number = 2
        player_dbi = player.PlayerDBI()
        player_dbi.get_track_id_pl_track_id_by_number(playlist_id=playlist_id, track_number=track_number)
        assert magic_mock.called, 'Failed to call method PlTrack.get_rows_by_playlist_id'
        assert magic_mock.call_args.kwargs['playlist_id'] == playlist_id
        assert isinstance(magic_mock.call_args.kwargs['con'], sqlite3.Connection)

    @mock.patch.object(audio_book_tables, 'DB_CONNECTION', sqlite_tools.DBConnectionManager(":memory:"))
    @mock.patch.object(audio_book_tables.PlTrack, 'get_rows_by_playlist_id')
    def test_returns_correct_values_when_get_rows_by_playlist_id_returns_row_with_matching_number(self, magic_mock):
        """
        Assert that get_pl_track_by_number returns the path id and pl_track_id when PlTrack.get_rows_by_playlist_id
        returns a list of sqlite3.Row containing a matching track number.
        """
        playlist_ids = (1, 1, 1)
        track_numbers = (4, 5, 6)
        pl_track_ids = (7, 8, 9)
        track_ids = (10, 11, 12)

        magic_mock.return_value = (
            {
                'id': pl_track_ids[0], 'track_number': track_numbers[0],
                'playlist_id': playlist_ids[0], 'track_id': track_ids[0]
            },
            {
                'id': pl_track_ids[1], 'track_number': track_numbers[1],
                'playlist_id': playlist_ids[1], 'track_id': track_ids[1]
            },
            {
                'id': pl_track_ids[2], 'track_number': track_numbers[2],
                'playlist_id': playlist_ids[2], 'track_id': track_ids[2]}
        )

        player_dbi = player.PlayerDBI()
        return_val = player_dbi.get_track_id_pl_track_id_by_number(
            playlist_id=playlist_ids[1], track_number=track_numbers[1]
        )
        assert isinstance(return_val, tuple)
        assert return_val[0] == track_ids[1]
        assert return_val[1] == pl_track_ids[1]

    @mock.patch.object(audio_book_tables, 'DB_CONNECTION', sqlite_tools.DBConnectionManager(":memory:"))
    @mock.patch.object(audio_book_tables.PlTrack, 'get_rows_by_playlist_id')
    def test_returns_none_when_get_rows_by_playlist_id_returns_row_without_matching_number(self, magic_mock):
        """
        Assert that get_pl_track_by_number returns None when PlTrack.get_rows_by_playlist_id
        returns a list of sqlite3.Row where no rows contain a matching track number.
        """
        playlist_ids = (1, 1, 1)
        track_numbers = (4, 5, 6)
        pl_track_ids = (7, 8, 9)
        track_ids = (10, 11, 12)

        magic_mock.return_value = (
            {
                'id': pl_track_ids[0], 'track_number': track_numbers[0],
                'playlist_id': playlist_ids[0], 'track_id': track_ids[0]
            },
            {
                'id': pl_track_ids[1], 'track_number': track_numbers[1],
                'playlist_id': playlist_ids[1], 'track_id': track_ids[1]
            },
            {
                'id': pl_track_ids[2], 'track_number': track_numbers[2],
                'playlist_id': playlist_ids[2], 'track_id': track_ids[2]}
        )

        player_dbi = player.PlayerDBI()
        return_val = player_dbi.get_track_id_pl_track_id_by_number(
            playlist_id=playlist_ids[1], track_number=77
        )
        assert return_val is None

    @mock.patch.object(audio_book_tables, 'DB_CONNECTION', sqlite_tools.DBConnectionManager(":memory:"))
    @mock.patch.object(audio_book_tables.PlTrack, 'get_rows_by_playlist_id')
    def test_returns_none_when_get_rows_by_playlist_id_returns_none(self, magic_mock):
        """
        Assert that get_pl_track_by_number returns None when PlTrack.get_rows_by_playlist_id
        returns None.
        """
        magic_mock.return_value = None
        player_dbi = player.PlayerDBI()
        return_val = player_dbi.get_track_id_pl_track_id_by_number(
            playlist_id=1, track_number=2
        )
        assert return_val is None


class TestGetPathByID:
    """Unit test for player.PlayerDBI.get_path_by_id(pl_track_id: int) -> str | pathlib.Path"""

    @mock.patch.object(audio_book_tables, 'DB_CONNECTION', sqlite_tools.DBConnectionManager(":memory:"))
    @mock.patch.object(audio_book_tables.TrackFile, 'get_row_by_id')
    def test_calls_abt_track_file_get_row_by_id(self, magic_mock):
        """Assert that get_pl_track_by_number calls TrackFile.get_row_by_id with correct args."""
        track_id = 1
        player_dbi = player.PlayerDBI()
        player_dbi.get_path_by_id(track_id)
        assert magic_mock.called, 'Failed to call method TrackFile.get_row_by_id'
        assert magic_mock.call_args.kwargs['id_'] == track_id, \
            'Failed to pass id_ parameter to TrackFile.get_row_by_id'
        assert isinstance(magic_mock.call_args.kwargs['con'], sqlite3.Connection),\
            'Failed to pass sqlite3.Connection to TrackFile.get_row_by_id as con parameter'

    @mock.patch.object(audio_book_tables, 'DB_CONNECTION', sqlite_tools.DBConnectionManager(":memory:"))
    @mock.patch.object(audio_book_tables.TrackFile, 'get_row_by_id')
    def test_returns_correct_value_when_id_exists(self, magic_mock):
        """
        Assert that get_pl_track_by_number returns the correct path when the path exists in the table.
        """
        magic_mock.return_value = {'id_': 1, 'path': '/some/path/one'}
        track_id = 1
        player_dbi = player.PlayerDBI()
        ret_val = player_dbi.get_path_by_id(track_id)
        assert isinstance(ret_val, str)
        assert ret_val == '/some/path/one'

    @mock.patch.object(audio_book_tables, 'DB_CONNECTION', sqlite_tools.DBConnectionManager(":memory:"))
    @mock.patch.object(audio_book_tables.TrackFile, 'get_row_by_id')
    def test_returns_none_when_id_not_found(self, magic_mock):
        """
        Assert that get_pl_track_by_number returns None when the path doesn't exist in the table.
        """
        magic_mock.return_value = None
        track_id = 1
        player_dbi = player.PlayerDBI()
        ret_val = player_dbi.get_path_by_id(track_id)
        assert ret_val is None
