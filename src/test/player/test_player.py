# -*- coding: utf-8 -*-
#
#  test_player.py
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
# pylint: disable=invalid-name
# disabled because in the IDE project structure sidebar, I want the test classes sorted in the same order
# as the methods they are testing.
#
# pylint: disable=protected-access
# disabled because this module is testing protected methods.
#
# pylint: disable=too-few-public-methods
# disabled because some of the tested methods only require one test.
#
# pylint: disable=comparison-with-callable
# disabled because this needs to be done regularly during tests.
#

"""
Unit test for class player.Player
"""

from unittest import mock
import pytest
# disabled because that patches use the import, by pylint doesn't see it.
import player  # pylint: disable=unused-import
from player import Player
import book


class TestGoToPosition:
    """Unit test for method go_to_position()"""

    def test_calls_gst_player_set_position(self):
        """
        Assert that player.go_to_position() calls method GstPlayer.set_position()
        with the correct args.
        """
        m_player = Player()
        m_player.player_backend = mock.Mock()
        m_player.player_backend.set_position = mock.Mock()
        time_ = player.StreamTime(30)
        m_player.go_to_position(time_=time_)
        assert m_player.player_backend.set_position.call_args.kwargs['time_'].get_time()\
               == time_.get_time()


class TestPause:
    """Unit test for method pause()"""

    @pytest.fixture()
    @mock.patch('player.GstPlayer')
    @mock.patch('player.PlayerDBI')
    def init_mocks(self, _, m_gst_player):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        player_ = Player()
        m_gst_player.pause = mock.Mock()
        return player_

    def test_calls_gst_player_pause(self, init_mocks):
        """
        Assert that pause() calls method GstPlayer.pause()
        """
        player_ = init_mocks
        player_.pause()
        assert player_.player_backend.pause.called


class TestPlay:
    """Unit test for method play()"""

    @pytest.fixture()
    @mock.patch('player.GstPlayer')
    @mock.patch('player.PlayerDBI')
    def init_mocks(self, _, m_gst_player):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        player_ = Player()
        m_gst_player.play = mock.Mock()
        return player_

    def test_play_calls_gst_player_play(self, init_mocks):
        """
        Assert that pause() calls method GstPlayer.play().
        """
        player_ = init_mocks
        player_.play()
        player_.player_backend.play.assert_called()


class TestSkipForwardLong:
    """Unit test for method skip_forward_long()"""


    @pytest.fixture()
    @mock.patch('player.GstPlayer')
    @mock.patch('player.PlayerDBI')
    def init_mocks(self, _, m_gst_player):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        player_ = Player()
        m_gst_player.set_position_relative = mock.Mock()
        return player_

    def test_skip_forward_long_calls_gst_player_set_position_relative(self, init_mocks):
        """
        Assert that skip_forward_long() calls method GstPlayer.set_position_relative().
        """
        player_ = init_mocks
        player_.skip_forward_long()
        assert player_.player_backend.set_position_relative.call_args.kwargs['delta_t'].get_time()\
               == player_.skip_duration_long.get_time()


class TestSkipForwardShort:
    """Unit test for method skip_forward_short()"""


    @pytest.fixture()
    @mock.patch('player.GstPlayer')
    @mock.patch('player.PlayerDBI')
    def init_mocks(self, _, m_gst_player):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        player_ = Player()
        m_gst_player.set_position_relative = mock.Mock()
        return player_

    def test_skip_skip_forward_short_calls_gst_player_set_position_relative(self, init_mocks):
        """
        Assert that skip_forward_short() calls method GstPlayer.set_position_relative().
        """
        player_ = init_mocks
        player_.skip_forward_short()
        assert player_.player_backend.set_position_relative.call_args.kwargs['delta_t'].get_time()\
               == player_.skip_duration_short.get_time()


class TestSkipReverseLong:
    """Unit test for method skip_reverse_long()"""


    @pytest.fixture()
    @mock.patch('player.GstPlayer')
    @mock.patch('player.PlayerDBI')
    def init_mocks(self, _, m_gst_player):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        player_ = Player()
        m_gst_player.set_position_relative = mock.Mock()
        return player_

    def test_skip_skip_reverse_long_calls_gst_player_set_position_relative(self, init_mocks):
        """
        Assert that skip_reverse_long() calls method GstPlayer.set_position_relative().
        """
        player_ = init_mocks
        player_.skip_reverse_long()
        delta_t = player_.skip_duration_long.get_time() * -1
        assert player_.player_backend.set_position_relative.call_args.kwargs['delta_t'].get_time()\
               == player.StreamTime(delta_t).get_time()


class TestSkipReverseShort:
    """Unit test for method skip_reverse_short()"""


    @pytest.fixture()
    @mock.patch('player.GstPlayer')
    @mock.patch('player.PlayerDBI')
    def init_mocks(self, _, m_gst_player):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        player_ = Player()
        m_gst_player.set_position_relative = mock.Mock()
        return player_

    def test_skip_skip_reverse_short_calls_gst_player_set_position_relative(self, init_mocks):
        """
        Assert that skip_reverse_short() calls method GstPlayer.set_position_relative().
        """
        player_ = init_mocks
        player_.skip_reverse_short()
        delta_t = player_.skip_duration_short.get_time() * -1
        assert player_.player_backend.set_position_relative.call_args.kwargs['delta_t'].get_time()\
               == player.StreamTime(delta_t).get_time()


class TestStop:
    """Unit test for method stop()"""

    @pytest.fixture()
    @mock.patch('player.GstPlayer')
    @mock.patch('player.PlayerDBI')
    def init_mocks(self, _, m_gst_player):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        player_ = Player()
        m_gst_player.stop = mock.Mock()
        return player_

    def test_stop_calls_gst_player_stop(self, init_mocks):
        """
        Assert that stop() calls method GstPlayer.stop().
        """
        player_ = init_mocks
        player_.stop()
        player_.player_backend.stop.assert_called()


class TestSetTrack:
    """Unit test for method set_track()"""
    sample_data = None

    def init_mocks(self):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        player_ = player.Player()
        player_.player_dbi.get_new_position = mock.Mock()
        self.sample_data = player.StreamData(
            path='some/path.mp3',
            time=player.StreamTime(0),
            duration=player.StreamTime(100),
            track_number=1,
            playlist_id=2,
            pl_track_id=3
        )
        player_.position = player.StreamData(
            path='some/path.mp3',
            time=player.StreamTime(99),
            duration=player.StreamTime(999),
            track_number=9,
            playlist_id=8,
            pl_track_id=7
        )
        player_.player_dbi.get_new_position.return_value = self.sample_data

        return player_

    def test_raises_runtime_error_when_fails_to_fully_set_stream_data(self):
        """
        Assert that set_track() raises RuntimeError if it fails to completely instantiate the StreamData object.
        """
        player_ = self.init_mocks()
        player_.player_dbi.get_new_position.return_value.playlist_id = None
        with pytest.raises(RuntimeError):
            player_.set_track(1)

    def test_sets_self_dot_stream_data_to_new_stream_data(self):
        """
        Assert that set_track() sets self.position to a new StreamData object.
        """
        player_ = self.init_mocks()
        player_.set_track(1)
        assert player_.position is self.sample_data


class TestLoadPlaylist:
    """Unit test for method load_playlist()"""
    player_ = None
    sample_data_new = None
    sample_data_saved = None

    def set_stream_data(self, track_number):
        """
        mock a side effect for player_.set_track()
        """
        _ = track_number
        self.player_.position = self.sample_data_new

    def init_mocks(self):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        self.sample_data_saved = player.StreamData(
            path='some/path.mp3',
            time=player.StreamTime(0),
            duration=player.StreamTime(100),
            track_number=1,
            playlist_id=2,
            pl_track_id=3
        )

        self.sample_data_new = player.StreamData(
            path='some/path.mp3',
            time=player.StreamTime(9),
            duration=player.StreamTime(999),
            track_number=9,
            playlist_id=8,
            pl_track_id=7
        )

        player_ = player.Player()
        self.player_ = player_
        player_.player_dbi.get_saved_position = mock.Mock()
        player_.player_dbi.get_saved_position.return_value = self.sample_data_saved
        player_.set_track = mock.Mock()
        player_.set_track.side_effect = self.set_stream_data
        player_.player_backend = mock.Mock()
        player_.player_backend.load_stream = mock.Mock()
        playlist_data = book.PlaylistData(title='some_title', path='some_path', id_=1)
        return player_, playlist_data

    def test_calls_backend_dot_load_stream_when_get_saved_position_fails(self):
        """
        Assert that load_playlist() calls player_backend.load_stream with
        a fully set StreamData even when there is not an already saved stream_data.
        """
        player_, playlist_data = self.init_mocks()
        player_.player_dbi.get_saved_position.return_value = player.StreamData()
        player_.load_playlist(playlist_data=playlist_data)
        _, kwargs = player_.player_backend.load_stream.call_args
        assert kwargs['stream_data'] is self.sample_data_new

    def test_calls_backend_dot_load_stream_when_saved_position_exists(self):
        """
        Assert that load_playlist() calls player_backend.load_stream with
        a fully set StreamData when there is an already saved stream_data.
        """
        player_, playlist_data = self.init_mocks()
        player_.load_playlist(playlist_data=playlist_data)
        _, kwargs = player_.player_backend.load_stream.call_args
        assert kwargs['stream_data'] is self.sample_data_saved
