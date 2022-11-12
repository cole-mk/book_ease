# -*- coding: utf-8 -*-
#
#  test_player_dbi.py
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

    def test_requirements_exist(self):
        """
        Assert that all methods and classes used in this method actually exist.
        """
        assert player.PlayerDBI
        assert player.PlayerDBI.get_saved_position
        assert audio_book_tables.DB_CONNECTION.query
        assert audio_book_tables.PlayerPosition.get_row_by_playlist_id
        assert player.StreamData

    @mock.patch.object(audio_book_tables, 'DB_CONNECTION', sqlite_tools.DBConnectionManager(":memory:"))
    @mock.patch.object(audio_book_tables.JoinTrackFilePlTrackPlayerPosition, 'get_row_by_playlist_id')
    def test_calls_get_row_by_playlist_id_with_correct_args(self, magic_mock):
        """
        show that audio_book_tables.JoinTrackFilePlTrackPlayerPosition.get_path_position_by_playlist_id is passed an
        sqlite3 Connection object and the playlist_id.
        """
        player_dbi = player.PlayerDBI()
        playlist_id = 1
        player_dbi.get_saved_position(playlist_id=playlist_id)
        assert isinstance(magic_mock.call_args.kwargs['con'], sqlite3.Connection)
        assert magic_mock.call_args.kwargs['playlist_id'] == playlist_id

    @mock.patch.object(audio_book_tables, 'DB_CONNECTION', sqlite_tools.DBConnectionManager(":memory:"))
    @mock.patch.object(audio_book_tables.JoinTrackFilePlTrackPlayerPosition, 'get_row_by_playlist_id')
    def test_returns_position_data_object_when_get_path_position_by_playlist_id_returns_sqlite3_row(self, magic_mock):
        """
        Show that get_saved_position returns a StreamData object when
        audio_book_tables.JoinTrackFilePlTrackPlayerPosition.get_path_position_by_playlist_id
        returns an sqlite3.row object.
        """
        # sqlite3.row objects are accessed in the same way as dicts, which is sufficient similarity for this test.
        magic_mock.return_value = {
            'path': 'some/path',
            'time': 69,
            'pl_track_id': 1,
            'playlist_id': 2,
            'track_number': 3
        }
        player_dbi = player.PlayerDBI()
        val = player_dbi.get_saved_position(1)
        assert isinstance(val, player.StreamData)

    @mock.patch.object(audio_book_tables, 'DB_CONNECTION', sqlite_tools.DBConnectionManager(":memory:"))
    @mock.patch.object(audio_book_tables.JoinTrackFilePlTrackPlayerPosition, 'get_row_by_playlist_id')
    def test_returns_empty_position_data_when_get_row_by_playlist_id_returns_none(self, magic_mock):
        """
        Show that get_saved_position returns None when
        audio_book_tables.JoinTrackFilePlTrackPlayerPosition.get_path_position_by_playlist_id
        returns None.
        """
        magic_mock.return_value = None
        player_dbi = player.PlayerDBI()
        position_data = player_dbi.get_saved_position(playlist_id=1)
        for item in position_data.__dict__.items():
            assert item[1] is None


class TestSavePosition:
    """Unit test for player.PlayerDBI.save_position(pl_track_id: int, playlist_id: int, stream_data: int)"""

    @mock.patch.object(audio_book_tables, 'DB_CONNECTION', sqlite_tools.DBConnectionManager(":memory:"))
    @mock.patch.object(audio_book_tables.PlayerPosition, 'upsert_row')
    def test_calls_upsert_row_with_correct_args(self, magic_mock):
        """Assert that save_position calls audio_book_tables.PlayerPosition.upsert_row with the correct kwargs"""
        player_dbi = player.PlayerDBI()
        player_dbi.save_position(pl_track_id=1, playlist_id=2, time_=player.StreamTime(3))
        assert magic_mock.call_args.kwargs['pl_track_id'] == 1
        assert magic_mock.call_args.kwargs['playlist_id'] == 2
        assert magic_mock.call_args.kwargs['time'] == 3


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
        assert return_val == (None, None)

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
        assert return_val == (None, None)


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

    @mock.patch.object(audio_book_tables, 'DB_CONNECTION', sqlite_tools.DBConnectionManager(":memory:"))
    @mock.patch.object(audio_book_tables.TrackFile, 'get_row_by_id')
    def test_raises_exception_when_id_is_none(self, magic_mock):
        """
        Assert that get_pl_track_by_number raises exception when the passed in parameter is None.
        """
        magic_mock.return_value = None
        track_id = None
        player_dbi = player.PlayerDBI()
        ret_val = player_dbi.get_path_by_id(track_id)
        assert ret_val is None


class TestGetNewPosition:
    """
    Unit test for:
    player.PlayerDBI.get_new_position(self,
                                      playlist_id: int,
                                      track_number: int,
                                      time: int) -> StreamData:
    """

    def test_requirements_exist(self):
        """
        Assert that all methods and classes used in this method actually exist.
        """
        assert player.PlayerDBI.get_track_id_pl_track_id_by_number
        assert player.PlayerDBI.get_track_id_pl_track_id_by_number
        assert player.PlayerDBI.get_path_by_id
        assert player.StreamData

    @mock.patch.object(player.PlayerDBI, 'get_track_id_pl_track_id_by_number')
    @mock.patch.object(player.PlayerDBI, 'get_path_by_id')
    def test_returns_fully_set_position_data(self, mock_get_path_by_id, mock_get_track_id_pl_track_id_by_number):
        """Assert that get_new_position returns a StreamData object fully set with the expected values"""
        time = player.StreamTime(0)
        playlist_id = 1
        track_number = 2
        track_id = 3
        pl_track_id = 4
        path = 'some/path'
        mock_get_track_id_pl_track_id_by_number.return_value = track_id, pl_track_id
        mock_get_path_by_id.return_value = path
        player_dbi = player.PlayerDBI()
        position = player_dbi.get_new_position(
            playlist_id=playlist_id, track_number=track_number, time_=time
        )
        assert position.path == path
        assert position.track_number == track_number
        assert position.playlist_id == playlist_id
        assert position.pl_track_id == pl_track_id
        assert isinstance(position.time, player.StreamTime)


class TestGetNumberOfPlTracks:
    """Unit test for method get_number_of_pl_tracks()"""

    @mock.patch.object(audio_book_tables.PlTrack, 'get_track_count_by_playlist_id')
    def test_calls_abt_get_track_count_by_playlist_id(self, m_get_track_count_by_playlist_id: mock.Mock):
        """
        Assert that get_number_of_pl_tracks() calls audio_book_tables.get_track_count_by_playlist_id()
        with the correct args.
        """
        m_get_track_count_by_playlist_id.return_value = 4
        player_dbi = player.PlayerDBI()
        test_playlist_id = 1
        player_dbi.get_number_of_pl_tracks(test_playlist_id)
        args, _ = m_get_track_count_by_playlist_id.call_args
        assert isinstance(args[0], sqlite3.Connection),\
            'An sqlite3.Connection was not passed to get_track_count_by_playlist_id.'
        assert args[1] == test_playlist_id,\
            'The correct playlist id was not passed to get_track_count_by_playlist_id'
