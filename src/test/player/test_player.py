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


# noinspection PyPep8Naming
class Test_OnDurationReady:
    """Unit test for method _on_duration_ready()"""

    @staticmethod
    def init_mocks():
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        player_ = Player()
        player_.position = player.StreamData
        player_.transmitter = mock.Mock()
        return player_

    def test_sets_position_dot_duration(self):
        """
        Assert that _on_duration_ready() sets self.position.duration to the passed in duration
        """
        player_ = self.init_mocks()
        time_ = player.StreamTime(30)
        player_._on_duration_ready(time_)
        assert player_.position.duration.get_time() == time_.get_time()

    def test_signals_duration_ready(self):
        """
        Assert that _on_duration_ready() sends the 'duration_ready' signal.
        """
        player_ = self.init_mocks()
        time_ = player.StreamTime(30)
        player_._on_duration_ready(time_)
        player_.transmitter.send.assert_called_with('duration_ready', time_)


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


class TestSetTrackRelative:
    """Unit test for method set_track_relative()"""

    def test_sets_stream_data_to_incremented_track_number(self):
        """
        Assert that set_track_relative() calls Player.set_track() with the correct args.

        It is not necessary to test that the tracks wrap around to the beginning or end.
        That is a test for Player._get_incremented_track_number().
        It is only necessary to show that set_track_relative() is using a method that rotates
        the track numbers.
        """
        player_ = player.Player()
        player_._get_incremented_track_number = mock.Mock()
        player_.set_track = mock.Mock()
        current_track_num = 2
        player_._get_incremented_track_number.side_effect = lambda x: current_track_num + x

        player_.set_track_relative(track_delta=1)
        player_.set_track.assert_called_with(track_number=3)

        player_.set_track_relative(track_delta=-1)
        player_.set_track.assert_called_with(track_number=1)


# noinspection PyPep8Naming
class Test_GetIncrementedTrackNumber:
    """Unit test for method _get_incremented_track_number()"""

    @staticmethod
    def init_mocks():
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        player_ = Player()
        player_.position = player.StreamData
        player_.position.track_number = 3
        player_.player_dbi = mock.Mock()
        player_.player_dbi.get_number_of_pl_tracks = mock.Mock()
        player_.player_dbi.get_number_of_pl_tracks.return_value = 12
        return player_

    def test_returns_track_number_incremented_by_track_delta(self):
        """
        Assert that _get_incremented_track_number() increments
        """
        player_ = self.init_mocks()

        # Increase track number by one.
        new_track_number = player_._get_incremented_track_number(track_delta=1)
        assert new_track_number == 4

        # Decrease track number by one.
        new_track_number = player_._get_incremented_track_number(track_delta=-1)
        assert new_track_number == 2

    def test_wraps_to_beginning_when_passing_end(self):
        """
        Assert that _get_incremented_track_number() returns the first track
        when incrementing past the end of the playlist.
        """
        player_ = self.init_mocks()
        player_.position.track_number = 11

        # Increase track number by one.
        new_track_number = player_._get_incremented_track_number(track_delta=1)
        assert new_track_number == 0

    def test_wraps_to_end_when_passing_beginning(self):
        """
        Assert that _get_incremented_track_number() returns the first track
        when incrementing past the end of the playlist.
        """
        player_ = self.init_mocks()
        player_.position.track_number = 0

        # Decrease track number by one.
        new_track_number = player_._get_incremented_track_number(track_delta=-1)
        assert new_track_number == 11


# noinspection PyPep8Naming
class Test_OnEos:
    """Unit test for method _on_eos()"""
    player_ = None
    go_to_first_track = None

    def m_set_track_relative(self, track_delta):
        """
        Mock set_track_relative() so that it wrapts the track number back to the first track,
        based of on the flag self.go_to_first_track.
        """
        if self.go_to_first_track is False:
            self.player_.position.track_number += track_delta
        elif self.go_to_first_track is True:
            self.player_.position.track_number = 0
        self.player_.position.time = player.StreamTime(0)

    def init_mocks(self):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        self.player_ = Player()
        self.player_.position = player.StreamData(track_number=3,
                                                  path='some/path',
                                                  time=player.StreamTime(120),
                                                  duration=player.StreamTime(200),
                                                  playlist_id=1,
                                                  pl_track_id=2)
        self.go_to_first_track = False
        self.player_.set_track_relative = mock.Mock()
        self.player_.set_track_relative.side_effect = self.m_set_track_relative
        self.player_.player_backend.load_stream = mock.Mock()
        self.player_.play = mock.Mock()
        self.player_.player_dbi.save_position = mock.Mock()
        return self.player_

    def test_saves_position_at_beginning_of_next_track(self):
        """
        Assert that _on_eos() saves the new position at the beginning of the next track.
        """
        player_ = self.init_mocks()
        player_._on_eos()

        self.player_.player_dbi.save_position.assert_called()
        _, kwargs = self.player_.player_dbi.save_position.call_args
        assert kwargs['pl_track_id'] == 2
        assert kwargs['playlist_id'] == 1
        assert kwargs['time_'] == player.StreamTime(0)

    def test_calls_play_if_not_wrapped_back_to_first_track(self):
        """
        Assert that _on_eos() calls self.play if The StreamData was advanced forward to the next track_number.
        """
        player_ = self.init_mocks()
        player_._on_eos()
        player_.play.assert_called()

    def test_not_calls_play_if_wrapped_back_to_first_track(self):
        """
        Assert that _on_eos() does not call self.play if The StreamData was set to track_number 0.
        """
        player_ = self.init_mocks()
        self.go_to_first_track = True
        player_._on_eos()
        player_.play.assert_not_called()

    def test_calls_set_track_relative(self):
        """
        Assert that _on_eos()calls set_track_relative() to advance to the next track.
        """
        player_ = self.init_mocks()
        player_._on_eos()
        player_.set_track_relative.assert_called_with(1)

    def test_calls_backend_dot_load_stream(self):
        """
        Assert that the newly advanced StreamData is loaded into the media player backend.
        """
        player_ = self.init_mocks()
        player_._on_eos()
        player_.player_backend.load_stream.assert_called_with(player_.position)


# noinspection PyPep8Naming
class Test_OnTimeUpdated:
    """Unit test for method _on_time_updated()"""

    def test_updates_time(self):
        """
        Assert that _on_time_updated() updates its stream_data with the new time.
        """
        player_ = Player()
        player_.position = player.StreamData()
        new_stream_time = player.StreamTime(30)

        player_._on_time_updated(new_stream_time)
        assert player_.position.time == new_stream_time

    def test_sends_time_updated_signal(self):
        """
        Assert that _on_time_updated() transmits the 'time_updated' signal
        with time as an argument.
        """
        player_ = Player()
        player_.position = player.StreamData()
        player_.transmitter = mock.Mock()
        player_.transmitter.send = mock.Mock()
        new_stream_time = player.StreamTime(30)

        player_._on_time_updated(new_stream_time)
        player_.transmitter.send.assert_called_with('time_updated', new_stream_time)
