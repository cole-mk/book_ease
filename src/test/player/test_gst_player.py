# -*- coding: utf-8 -*-
#
#  test_gst_player.py
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
# pylint: disable=wrong-import-position
# disabled because gi.repository requires an import order that pylint dislikes.
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
# pylint: disable=unused-variable
# disabled because that's going to happen with the way I'm calling init_mock methods.
#
# pylint: disable=comparison-with-callable
# disabled because this needs to be done regularly during tests.
#

"""
Unit test for class player.GstPlayer
"""

from unittest import mock
import pytest
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import player
from player import GstPlayer


class TestGetURIFromPath:
    """Unit test for method get_uri_from_path()"""

    def test_returns_uri_from_path(self):
        """
        Show that get_uri_from_path() returns a properly formatted uri when given a file path.
        """
        uri = GstPlayer.get_uri_from_path('/some/path')
        assert uri == 'file:///some/path'

    def test_returns_uri_unchanged_when_passed_uri(self):
        """
        Show that get_uri_from_path() returns an unchanged uri when given a properly formatted uri.
        """
        uri = GstPlayer.get_uri_from_path('https://www.freedesktop.org')
        assert uri == 'https://www.freedesktop.org'


class TestLoadPositionData:
    """Unit tests for method load_position_data()"""

    @staticmethod
    def init_mocks():
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        gst_player = player.GstPlayer()
        gst_player._init_message_bus = m_init_message_bus = mock.Mock()
        gst_player._init_pipeline = m_init_pipeline = mock.Mock()
        return gst_player, m_init_message_bus, m_init_pipeline

    def test_raises_runtime_error_if_already_set(self):
        """Asset that load_position_data() raises a RuntimeError if position is already set."""
        gst_player, m_init_message_bus, m_init_pipeline = self.init_mocks()
        gst_player.position = player.PositionData()
        with pytest.raises(RuntimeError):
            gst_player.load_position_data(player.PositionData())

    def test_not_raise_runtime_error_if_not_already_set(self):
        """
        Assert that load_position_data() does not raise a RuntimeError if 'self.position' has not already been set.
        """
        gst_player, m_init_message_bus, m_init_pipeline = self.init_mocks()
        try:
            gst_player.load_position_data(player.PositionData())
            assert True
        except RuntimeError:
            assert False, 'Raised RuntimeError even though self.position was not already set.'

    def test_method_calls_init_pipeline(self):
        """Assert that load_position_data() calls _init_pipeline()"""
        gst_player, m_init_message_bus, m_init_pipeline = self.init_mocks()
        gst_player.load_position_data(player.PositionData())
        assert m_init_pipeline.called, 'Failed to call method GstPlayer._init_pipeline'

    def test_method_calls_init_message_bus(self):
        """Assert that load_position_data() calls _init_message_bus()"""
        gst_player, m_init_message_bus, m_init_pipeline = self.init_mocks()
        gst_player.load_position_data(player.PositionData())
        assert m_init_message_bus.called, 'Failed to call method GstPlayer._init_pipeline'


class TestPause:
    """Unit test for method GstPlayer.pause"""

    def test_raises_runtime_error_if_gst_fails_to_pause(self):
        """Assert that pause raises RuntimeError if Gstreamer fails to pause media."""
        gst_player = player.GstPlayer()
        gst_player.pipeline = mock.Mock()
        gst_player.pipeline.__class__.set_state = mock.Mock(return_value=Gst.StateChangeReturn.FAILURE)
        with pytest.raises(RuntimeError):
            gst_player.pause()

    def test_sets_playback_state_flag_to_paused(self):
        """Assert that the instance attribute 'playback_state' is set to paused"""
        gst_player = player.GstPlayer()
        gst_player.pipeline = mock.Mock()
        gst_player.pipeline.__class__.set_state = mock.Mock(return_value=Gst.StateChangeReturn.SUCCESS)
        gst_player.pause()
        assert gst_player.playback_state == 'paused'


class TestStop:
    """
    Unit test for 'GstPlayer.stop()'
    """

    @staticmethod
    def init_mocks() -> GstPlayer:
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        gst_player = player.GstPlayer()
        gst_player.pause = mock.Mock()
        gst_player.set_position = mock.Mock()
        gst_player.position = mock.Mock()
        gst_player.position.time = mock.Mock()
        return gst_player

    def test_sets_pipeline_to_paused_state(self):
        """Assert that stop sets the GstPlayer and pipeline to the paused state."""
        gst_player = self.init_mocks()
        gst_player.stop()
        assert gst_player.pause.called

    def test_sets_playback_state_flag_to_stopped(self):
        """Assert that the instance attribute 'playback_state' is set to stopped"""
        gst_player = self.init_mocks()
        gst_player.stop()
        assert gst_player.playback_state == 'stopped'

    def test_calls_set_position_to_t_equals_zero(self):
        """
        Assert that stop calls self.set_position with parameter t_seconds=0
        This shows that playback will be set to the beginning of the stream.
        """
        gst_player = self.init_mocks()
        gst_player.stop()
        assert gst_player.set_position.called, 'gst_player.set_position was not called'
        assert gst_player.set_position.call_args.kwargs['t_seconds'] == 0,\
            'gst_player.set_position was not called with parameter t_seconds=0'

    def test_sets_position_dot_time_to_zero(self):
        """Assert that stop updates the time in the position object."""
        gst_player = self.init_mocks()
        gst_player.stop()
        assert gst_player.position.time == 0, 'stop failed to set self.position.time to zero.'


class TestPlay:
    """Unit test for method play()"""

    def test_raises_runtime_error_if_gst_fails_to_pause(self):
        """Assert that play() raises RuntimeError if Gstreamer fails to play media."""
        gst_player = player.GstPlayer()

        gst_player.pipeline = mock.Mock()
        gst_player.pipeline.__class__.set_state = mock.Mock(return_value=Gst.StateChangeReturn.FAILURE)
        with pytest.raises(RuntimeError):
            gst_player.play()

    def test_sets_pipeline_to_playing_state(self):
        """Assert that play() sets the gstreamer pipeline to the playing state."""
        gst_player = player.GstPlayer()

        gst_player.pipeline = mock.Mock()
        gst_player.pipeline.__class__.set_state = mock.Mock(return_value=Gst.StateChangeReturn.SUCCESS)

        gst_player.play()
        assert gst_player.pipeline.set_state.called
        assert gst_player.pipeline.set_state.call_args.kwargs['state'] == Gst.State.PLAYING

    def test_sets_playback_state_flag_to_stopped(self):
        """Assert that the instance attribute 'playback_state' is set to playing"""
        gst_player = player.GstPlayer()

        gst_player.pipeline = mock.Mock()
        gst_player.pipeline.__class__.set_state = mock.Mock(return_value=Gst.StateChangeReturn.SUCCESS)

        gst_player.play()
        assert gst_player.playback_state == 'playing'


class TestPopPositionData:
    """Unit test for the method pop_position_data()"""

    @staticmethod
    def init_mocks():
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        gst_player = player.GstPlayer()
        gst_player._close_pipeline = m_close_pipeline = mock.Mock()
        gst_player.position = player.PositionData()
        return gst_player, m_close_pipeline

    def test_raises_runtime_error_if_position_is_not_already_set(self):
        """
        Assert that a RuntimeError is raised if pop_position_data() is called
        when 'self.position' has not been set.
        """
        gst_player, m_close_pipeline = self.init_mocks()
        gst_player.position = None
        with pytest.raises(RuntimeError):
            gst_player.pop_position_data()

    def test_returns_position(self):
        """Assert that pop_position_data() returns self.position"""
        gst_player, m_close_pipeline = self.init_mocks()
        input_test_position = gst_player.position
        output_test_position = gst_player.pop_position_data()
        assert output_test_position is input_test_position

    def test_calls_close_pipeline(self):
        """Assert that the gstreamer pipeline is closed because we must be finished with it."""
        gst_player, m_close_pipeline = self.init_mocks()
        gst_player.pop_position_data()
        assert m_close_pipeline.called

    def test_sets_position_to_none(self):
        """Assert that 'self.position' is set to None."""
        gst_player, m_close_pipeline = self.init_mocks()
        gst_player.pop_position_data()
        assert gst_player.position is None


class TestSetPositionRelative:
    """Unit tests for method set_position_relative()"""
    duration = 100

    def init_mocks(self):
        gst_player = player.GstPlayer()
        gst_player._query_position = mock.Mock()
        gst_player._query_position.return_value = self.duration * Gst.SECOND
        gst_player.set_position = mock.Mock()

        return gst_player

    def test_calls_self_dot_query_position(self):
        """
        Assert that set_position_relative() call self._query_position() to get the current position.
        """
        gst_player = self.init_mocks()
        gst_player.set_position_relative(delta_t_seconds=1)
        gst_player._query_position.assert_called()

    def test_calls_set_position_with_t_seconds_normalized_to_valid_range(self):
        """
        Assert that set_position_relative() normalizes the new position time to the nearest endpoint of the valid
        position range, when (current position + delta_t_seconds) is outside the valid range of positions for this
        stream.
        """
        gst_player = self.init_mocks()

        # New position is far less than zero.
        gst_player.set_position_relative(delta_t_seconds=self.duration * -2)
        assert gst_player.set_position.called
        assert gst_player.set_position.call_args.kwargs['t_seconds'] == 0

        # New position is exactly zero.
        gst_player.set_position_relative(delta_t_seconds=self.duration * -1)
        assert gst_player.set_position.called
        assert gst_player.set_position.call_args.kwargs['t_seconds'] == 0

        # New position is exactly zero-1.
        gst_player.set_position_relative(delta_t_seconds=(self.duration * -1) - 1)
        assert gst_player.set_position.called
        assert gst_player.set_position.call_args.kwargs['t_seconds'] == 0

        # New position is exactly in the middle of the duration.
        gst_player.set_position_relative(delta_t_seconds=int(self.duration / -2))
        assert gst_player.set_position.called
        assert gst_player.set_position.call_args.kwargs['t_seconds'] == int(self.duration/2)


# noinspection PyPep8Naming
class Test_InitDuration:
    """Unit tests for _init_duration()"""
    duration = 100 * Gst.SECOND

    def init_mocks(self):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        gst_player = player.GstPlayer()
        gst_player._query_duration = mock.Mock(return_value=self.duration)
        gst_player.transmitter = mock.Mock()
        gst_player.transmitter.send = mock.Mock()
        m_bus = mock.Mock()
        m_bus.disconnect_by_func = mock.Mock()
        m_msg = mock.Mock()
        return gst_player, m_bus, m_msg

    def test_sets_self_dot_duration_to_correct_value(self):
        """
        Assert that _init_duration() sets self.duration to the correct value retrieved from gstreamer.
        """
        gst_player, m_bus, m_msg = self.init_mocks()
        gst_player._init_duration(m_bus, m_msg)
        assert gst_player.duration == self.duration

    def test_emits_duration_ready(self):
        """
        Assert that GstPlayer emits the 'duration_ready' signal as soon as GStreamer is able to
        successfully acquire the duration from the stream.
        """
        gst_player, m_bus, m_msg = self.init_mocks()
        gst_player._init_duration(m_bus, m_msg)
        gst_player.transmitter.send.assert_called()

    def test_disconnects_callback(self):
        """
        Assert that _init_duration() disconnects itself from the message bus
        by calling bus.disconnect_by_func
        """
        gst_player, m_bus, m_msg = self.init_mocks()
        gst_player._init_duration(m_bus, m_msg)
        m_bus.disconnect_by_func.assert_called_with(gst_player._init_duration)


# noinspection PyPep8Naming
class Test_InitStartPosition:
    """Unit tests for _init_start_position()"""

    def test_calls_set_position_with_t_seconds_equals_position_dot_time(self):
        """
        _init_start_position() should simply call set_position(t_seconds=self.position.time)
        """
        gst_player = player.GstPlayer()
        gst_player.position = mock.Mock()
        gst_player.position.time = mock.Mock()
        gst_player.set_position = mock.Mock()

        gst_player._init_start_position()
        assert gst_player.set_position.called
        assert gst_player.set_position.call_args.kwargs['t_seconds'] == gst_player.position.time


# noinspection PyPep8Naming
class Test_ClosePipeline:
    """Unit tests for _close_pipeline()"""

    def test_raises_runtime_error_if_pipeline_is_already_none(self):
        """Assert that _close_pipeline() raises RuntimeError if 'self.pipeline' is already None"""
        gst_player = player.GstPlayer()
        with pytest.raises(RuntimeError):
            gst_player.pipeline = None
            gst_player._close_pipeline()

    def test_calls_pipeline_dot_set_state_if_pipeline_exists(self):
        """Assert that self.pipeline.set_state() gets called when it exists."""
        gst_player = player.GstPlayer()

        gst_player.pipeline = mock.Mock()
        gst_player.pipeline.set_state = m_set_state = mock.Mock()

        gst_player._close_pipeline()

        assert m_set_state.called, 'Gst.Pipeline.set_state was not called during player.GstPlayer._close_pipeline().'

        # Assert that set_state was called with the 'state' kwarg.
        if 'state' in m_set_state.call_args.kwargs.keys():
            assert True
        else:
            err_msg = """
            Gst.Pipeline.set_state was called with a missing \'state\' kwarg
            during player.GstPlayer._close_pipeline().
            """
            assert False, err_msg

        assert m_set_state.call_args.kwargs['state'] == Gst.State.NULL

    def test_sets_pipeline_to_none_if_pipeline_exists(self):
        """Assert that 'self.pipeline' gets set to None when it exists."""
        gst_player = player.GstPlayer()

        gst_player.pipeline = mock.Mock()
        gst_player.pipeline.set_state = m_set_state = mock.Mock()

        gst_player._close_pipeline()
        err_msg = """
        player.GstPlayer._close_pipeline did not reset self.pipeline to None.
        """
        assert gst_player.pipeline is None, err_msg

    def test_sets_pipeline_to_none_after_calling_set_state_if_pipeline_exists(self):
        """
        Assert that self.pipeline.set_state() gets called before discarding the reference to self.pipeline.
        That is: self.pipeline.set_state() must be called before setting 'self.pipeline' to None.
        """
        gst_player = player.GstPlayer()

        gst_player.pipeline = mock.Mock()
        gst_player.pipeline.set_state = m_set_state = mock.Mock()

        try:
            gst_player._close_pipeline()
            if gst_player.pipeline is not None:
                pytest.skip(reason="player.GstPlayer.pipeline must not be None"
                                   "after _close_pipeline() finishes to perform this test.")
            if not m_set_state.called:
                pytest.skip(reason="player.GstPlayer.pipeline.set_state must have been called"
                                   "during _close_pipeline()  to perform this test.")
        # Doing them in the wrong order triggers the exception.
        except AttributeError:
            err_msg = """
            During player.GstPlayer._close_pipeline(),
            player.GstPlayer.pipeline.set_state() was called after setting 
            player.GstPlayer.pipeline to None. This results in an AttributeError
            during the execution of _close_pipeline().
            """
            assert False, err_msg


# noinspection PyPep8Naming
class Test_InitAttributesThatCanOnlyBeSetAfterPlaybackStarted:
    """Unit tests for _init_attributes_that_can_only_be_set_after_playback_started(self, bus, msg)"""

    @staticmethod
    def init_mocks():
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        gst_player = player.GstPlayer()
        gst_player._init_duration = mock.Mock()
        gst_player._init_start_position = mock.Mock()
        m_message = mock.Mock()
        m_message.parse_state_changed = mock.Mock(return_value=(Gst.State.READY, Gst.State.PAUSED, Gst.State.PLAYING))
        m_message.src = gst_player.pipeline = mock.Mock()
        m_bus = mock.Mock()
        m_bus.disconnect_by_func = mock.Mock()
        glib_idle_add = GLib.timeout_add = mock.Mock()
        return gst_player, m_message, m_bus, glib_idle_add

    def test_calls_init_start_position_if_msg_src_is_pipeline_and_pipeline_is_entering_playing_state(self):
        """
        Assert that _init_start_position() is called when the passed in msg.src is self.pipeline
        and 'self.pipeline' is about to enter the playing state.

         _init_start_position() must not be called before this time or Gst can't set the
         playback position of the pipeline.

        Only do this if the message source is 'self.pipeline'.
        """
        gst_player, m_message, m_bus, _ = self.init_mocks()

        gst_player._init_attributes_that_can_only_be_set_after_playback_started(m_bus, m_message)
        assert gst_player._init_start_position.called

    def test_no_call_init_start_position_if_msg_src_is_not_pipeline_or_pipeline_is_not_entering_playing_state(self):
        """
        Assert that _init_start_position() is not called when the passed in msg.src is not self.pipeline
        or 'self.pipeline' is not about to enter the playing state.
        """

        # 'self.pipeline' is not about to enter the playing state
        gst_player, m_message, m_bus, _ = self.init_mocks()
        m_message.parse_state_changed.return_value = (None, None, None)
        gst_player._init_attributes_that_can_only_be_set_after_playback_started(m_bus, m_message)
        assert not gst_player._init_start_position.called

        #  msg.src is not self.pipeline
        gst_player, m_message, m_bus, _ = self.init_mocks()
        m_message.src = None
        gst_player._init_attributes_that_can_only_be_set_after_playback_started(m_bus, m_message)
        assert not gst_player._init_start_position.called

    def test_disconnects_after_success(self):
        """
        The method only needs to be called once per stream.
        Make sure that the callback is disconnected  when the passed in msg.src is self.pipeline
        and 'self.pipeline' is about to enter the playing state.
        """
        gst_player, m_message, m_bus, _ = self.init_mocks()
        gst_player._init_attributes_that_can_only_be_set_after_playback_started(m_bus, m_message)
        assert m_bus.disconnect_by_func.called

    def test_not_disconnected_if_msg_src_is_not_pipeline_or_pipeline_is_not_entering_playing_state(self):
        """
        The method only needs to be called once per stream.
        Make sure that the callback is disconnected  when the passed in msg.src is self.pipeline
        and 'self.pipeline' is about to enter the playing state.
        """

        # 'self.pipeline' is not about to enter the playing state
        gst_player, m_message, m_bus, _ = self.init_mocks()
        m_message.parse_state_changed.return_value = (None, None, None)
        gst_player._init_attributes_that_can_only_be_set_after_playback_started(m_bus, m_message)
        assert not m_bus.disconnect_by_func.called

        #  msg.src is not self.pipeline
        gst_player, m_message, m_bus, _ = self.init_mocks()
        m_message.src = None
        gst_player._init_attributes_that_can_only_be_set_after_playback_started(m_bus, m_message)
        assert not m_bus.disconnect_by_func.called


# noinspection PyPep8Naming
class Test_InitMessageBus:
    """Unit test for method _init_message_bus."""

    @staticmethod
    def init_mocks():
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        gst_player = player.GstPlayer()
        gst_player.pipeline = mock.Mock()

        bus_mock = mock.Mock()
        bus_mock.add_signal_watch = mock.Mock()
        bus_mock.connect = mock.Mock()
        gst_player.pipeline.get_bus = get_bus_mock = mock.Mock()
        gst_player.pipeline.get_bus.return_value = bus_mock
        return gst_player, get_bus_mock, bus_mock

    def test_adds_signal_watch(self):
        """A signal watch must be added to self.pipeline's message bus for callbacks to work."""
        gst_player, get_bus_mock, bus_mock = self.init_mocks()
        gst_player._init_message_bus()
        assert bus_mock.add_signal_watch.called

    def test_connects_the_correct_messages(self):
        """
        Assert that the correct Gst.Bus events are connected to the correct callbacks.
        Assert that those are the only callbacks connected in _init_message_bus().
        """
        gst_player, get_bus_mock, bus_mock = self.init_mocks()
        gst_player._init_message_bus()
        calls = [
            mock.call("message::state-changed", gst_player._start_update_time),
            mock.call("message::error", gst_player._on_error),
            mock.call("message::eos", gst_player._on_eos),
            mock.call("message::state-changed",
                      gst_player._init_attributes_that_can_only_be_set_after_playback_started),
            mock.call("message::duration-changed", gst_player._init_duration)
        ]
        bus_mock.connect.assert_has_calls(calls, any_order=True)
        assert bus_mock.connect.call_count == len(calls),\
            'A new call to bus.connect() has probably been added without updating the test.'


# noinspection PyPep8Naming
class Test_InitPipeline:
    """Unit test for method _init_pipeline()."""

    def init_mocks(self):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        # pylint: disable=attribute-defined-outside-init
        gst_player = player.GstPlayer()
        self.mocked_pipeline = mock.Mock()
        self.mocked_fake_video_sink = "fakevideosink"
        m_element_factory_make = Gst.ElementFactory.make = mock.Mock(side_effect=self.mocked_gst_element_factory_make)
        gst_player.position = mock.Mock()
        gst_player.position.path = '/some/valid/file/path.mp3'

        return gst_player, m_element_factory_make

    def mocked_gst_element_factory_make(self, *args):
        """
        Mock the function Gst.ElementFactory.make()
        """
        if args == ("playbin", "playbin"):
            return self.mocked_pipeline
        if args == ("fakevideosink", "video_sink"):
            return self.mocked_fake_video_sink
        return None

    def test_raises_runtime_error_if_pipeline_already_exists(self):
        """
        Assert that calling _init_pipeline() raises a RuntimeError when self.pipeline is already set.

        Raising the RuntimeError should be the first thing that the method does, so catch and re-raise that error
        while ignoring all other exceptions caused by not completely mocking out the method.
        """
        gst_player, m_element_factory_make = self.init_mocks()
        gst_player.pipeline = True
        with pytest.raises(RuntimeError):
            try:
                gst_player._init_pipeline()
            except RuntimeError:
                raise
            except Exception:  # pylint: disable=broad-except
                pass

    def test_creates_playbin(self):
        """Show that _init_pipeline() sets 'self.pipeline' to object of type Gst.Playbin"""
        gst_player, m_element_factory_make = self.init_mocks()
        gst_player._init_pipeline()
        assert m_element_factory_make.has_calls([mock.call("playbin", "playbin")], any_order=True)
        assert gst_player.pipeline == self.mocked_pipeline

    def test_sets_video_output_to_null_sink(self):
        """
        Some streams contain a video portion that can't be ignored.
        Assert that the pipeline is given a Gst fakevideosink that discards the video stream.
        """
        gst_player, m_element_factory_make = self.init_mocks()
        gst_player._init_pipeline()
        calls = [mock.call("video-sink", self.mocked_fake_video_sink)]
        self.mocked_pipeline.set_property.assert_has_calls(calls, any_order=True)

    def test_sets_stream_path_as_uri(self):
        """
        _init_pipeline() must set the pipeline's uri property to the path of the file being played.
        The path may or may not already be a correctly formatted uri.
        """
        # When gst_player.position.path is a file path
        gst_player, m_element_factory_make = self.init_mocks()
        gst_player._init_pipeline()
        gst_player.pipeline.set_property.assert_called_with('uri', 'file:///some/valid/file/path.mp3')

        # When gst_player.position.path is a web link
        gst_player, m_element_factory_make = self.init_mocks()
        gst_player.position.path = \
            'https://www.freedesktop.org/software/gstreamer-sdk/data/media/sintel_trailer-480p.webm'
        gst_player._init_pipeline()
        gst_player.pipeline.set_property.assert_called_with(
            'uri', 'https://www.freedesktop.org/software/gstreamer-sdk/data/media/sintel_trailer-480p.webm'
        )

    def test_sets_pipeline_to_ready_state(self):
        """
        Assert that _init_pipeline() sets the pipeline to the ready state.
        This must be done, so that we can fail now if the pipeline has a problem.
        """
        gst_player, m_element_factory_make = self.init_mocks()
        gst_player._init_pipeline()
        gst_player.pipeline.set_state.assert_called_with(Gst.State.READY)

    def test_raises_runtime_error_if_set_pipeline_to_ready_state_fails(self):
        """
        Assert that _init_pipeline() raises a RuntimeError when it fails to set the pipeline to the ready state.
        """
        gst_player, m_element_factory_make = self.init_mocks()
        self.mocked_pipeline.set_state = mock.Mock(return_value=Gst.StateChangeReturn.FAILURE)
        with pytest.raises(RuntimeError):
            gst_player._init_pipeline()


# noinspection PyPep8Naming
class Test_OnEos:
    """Unit tests for _on_eos()"""

    def init_mocks(self):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        gst_player = player.GstPlayer()
        gst_player.stop = mock.Mock()
        gst_player._close_pipeline = mock.Mock()
        gst_player.transmitter.send = mock.Mock()
        return gst_player

    def test_calls_gst_player_stop(self):
        """
        _on_eos() must call stop() to reset the GstPlayer's internal state to 'stopped'
        and reset the position to the beginning of the file.
        """
        gst_player = self.init_mocks()
        gst_player._on_eos('bus', 'msg')
        gst_player.stop.assert_called()

    def test_calls_close_pipeline(self):
        """
        Assert that _on_eos calls self.._close_pipeline().
        """
        gst_player = self.init_mocks()
        gst_player._on_eos('bus', 'msg')
        gst_player._close_pipeline.assert_called()

    def test_emits_eos(self):
        """
        Assert that _on_eos emits the eos signal on self.transmitter.
        """
        gst_player = self.init_mocks()
        gst_player._on_eos('bus', 'msg')
        gst_player.transmitter.send.assert_called_with('eos')



# noinspection PyPep8Naming
class Test_StartUpdateTime:
    """Unit tests for _start_update_time()"""

    @staticmethod
    def init_mocks():
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        gst_player = player.GstPlayer()
        gst_player.pipeline = 'pipeline'
        bus = mock.Mock()
        bus.disconnect_by_func = mock.Mock()

        msg = mock.Mock()
        msg.src = 'pipeline'
        msg.parse_state_changed = mock.Mock(
            return_value=(None, Gst.State.PLAYING, Gst.State.VOID_PENDING)
        )
        m_timeout_add_seconds = GLib.timeout_add_seconds = mock.Mock()
        return gst_player, bus, msg, m_timeout_add_seconds

    def test_starts_update_time_if_caller_msg_src_is_pipeline_and_pipeline_entered_playing_state(self):
        """
        _start_update_time() must start the timer that calls GstPlayer._update_time() periodically.
        _start_update_time() does this by calling GLib.timeout_add_seconds(timeout, callback)
        This test shows that _start_update_time() passes an int for the timeout
        and GstPlayer._update_time for the callback.

        _start_update_time() is a Gst.Bus callback that must first check the message source to see if it is
        self.pipeline.  _start_update_time() must then ensure that the pipeline has fully entered the playing state.
        """
        gst_player, bus, msg, m_timeout_add_seconds = self.init_mocks()
        gst_player._start_update_time(bus, msg)
        assert isinstance(m_timeout_add_seconds.call_args[0][0], int)
        assert m_timeout_add_seconds.call_args[0][1] == gst_player._update_time

    def test_not_starts_update_time_if_caller_msg_src_is_not_pipeline(self):
        """
        This test shows that _start_update_time() does not start the timed calling of _update_time
        when the message source is not the pipeline.

        _start_update_time() must start the timer that calls GstPlayer._update_time() periodically.
        _start_update_time() does this by calling GLib.timeout_add_seconds(timeout, callback)


        _start_update_time() is a Gst.Bus callback that must first check the message source to see if it is
        self.pipeline.  _start_update_time() must then ensure that the pipeline has fully entered the playing state.
        """
        gst_player, bus, msg, m_timeout_add_seconds = self.init_mocks()
        msg.src = 'not the pipeline'

        gst_player._start_update_time(bus, msg)
        m_timeout_add_seconds.assert_not_called()

    def test_not_starts_update_time_if_pipeline_not_entered_playing_state(self):
        """
        This test shows that _start_update_time() does not start the timed calling of _update_time
        when the pipeline has not entered the playing state.

        _start_update_time() must start the timer that calls GstPlayer._update_time() periodically.
        _start_update_time() does this by calling GLib.timeout_add_seconds(timeout, callback)


        _start_update_time() is a Gst.Bus callback that must first check the message source to see if it is
        self.pipeline.  _start_update_time() must then ensure that the pipeline has fully entered the playing state.
        """
        gst_player, bus, msg, m_timeout_add_seconds = self.init_mocks()
        msg.parse_state_changed.return_value = None, None, None

        gst_player._start_update_time(bus, msg)
        m_timeout_add_seconds.assert_not_called()

    def test_removes_itself_from_callback_list_if_caller_msg_src_is_pipeline_and_pipeline_entered_playing_state(self):
        """
        Assert that _start_update_time() calls bus.disconnect_by_func to remove itself from the callback list.

        _start_update_time() must start the timer that calls GstPlayer._update_time() periodically.
        After it does this, it must not be called again.

        _start_update_time() is a Gst.Bus callback that must first check the message source to see if it is
        self.pipeline.  _start_update_time() must then ensure that the pipeline has fully entered the playing state.
        """
        gst_player, bus, msg, m_timeout_add_seconds = self.init_mocks()
        gst_player._start_update_time(bus, msg)
        bus.disconnect_by_func.assert_called()
        bus.disconnect_by_func.assert_called_with(gst_player._start_update_time)

    def test_not_removes_itself_from_callback_list_if_caller_msg_src_is_not_pipeline(self):
        """
        Assert that _start_update_time() does not calls bus.disconnect_by_func to remove itself
        from the callback list if the message source is not the pipeline.

        _start_update_time() must start the timer that calls GstPlayer._update_time() periodically.
        After it does this, it must not be called again.

        _start_update_time() is a Gst.Bus callback that must first check the message source to see if it is
        self.pipeline.  _start_update_time() must then ensure that the pipeline has fully entered the playing state.
        """
        gst_player, bus, msg, m_timeout_add_seconds = self.init_mocks()
        msg.src = 'not the pipeline'

        gst_player._start_update_time(bus, msg)
        bus.disconnect_by_func.assert_not_called()

    def test_not_removes_itself_from_callback_list_if_pipeline_not_entered_playing_state(self):
        """
        Assert that _start_update_time() does not calls bus.disconnect_by_func to remove itself
        from the callback list if the message source is not the pipeline.

        _start_update_time() must start the timer that calls GstPlayer._update_time() periodically.
        After it does this, it must not be called again.

        _start_update_time() is a Gst.Bus callback that must first check the message source to see if it is
        self.pipeline.  _start_update_time() must then ensure that the pipeline has fully entered the playing state.
        """
        gst_player, bus, msg, m_timeout_add_seconds = self.init_mocks()
        msg.parse_state_changed.return_value = None, None, None

        gst_player._start_update_time(bus, msg)
        bus.disconnect_by_func.assert_not_called()


# noinspection PyPep8Naming
class Test_UpdateTime:
    """Unit tests for _update_time()"""

    @staticmethod
    def init_mocks():
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        gst_player = player.GstPlayer()
        gst_player.playback_state = 'playing'
        gst_player.pipeline = mock.Mock()
        gst_player.position = mock.Mock()
        gst_player.position.time = None
        cur_time = 12345678
        gst_player._query_position = mock.Mock(return_value=cur_time * Gst.SECOND)
        return gst_player, cur_time

    def test_returns_false_when_pipeline_None(self):
        """
        Assert that _update_time() stops itself from being called when the pipeline has been closed.
        returning False tells the Gst.MessageBus to stop periodically calling _update_time().
        """
        gst_player, _ = self.init_mocks()
        gst_player.pipeline = None
        ret_val = gst_player._update_time()
        assert ret_val is False

    def test_returns_true_when_playback_state_is_stopped(self):
        """
        Assert that _update_time() returns True if playback state is 'stopped' in order to avoid
        updating an unchanging field. Furthermore, the position is set immediately when entering the stopped state.
        """
        gst_player, _ = self.init_mocks()
        gst_player.playback_state = 'stopped'
        ret_val = gst_player._update_time()
        assert ret_val is True

    def test_updates_position_if_queries_pipeline_successfully(self):
        """
        Assert that _update_time() updates self.position.time correctly when it can successfully query the current
        position from the pipeline.

        self.position.time units must be seconds and not the native GStreamer time-stamp.

        This test assumes:
        self.playback_state == 'stopped'
        self.pipeline != None
        """
        gst_player, cur_time = self.init_mocks()
        gst_player._update_time()
        assert gst_player.position.time == cur_time

    def test_not_updates_position_if_not_queries_pipeline_successfully(self):
        """
        Assert that _update_time() does not update self.position.time when it can not successfully query the current
        position from the pipeline.

        This test assumes:
        self.playback_state == 'stopped'
        self.pipeline != None
        """
        gst_player, _ = self.init_mocks()
        gst_player._query_position = mock.Mock(side_effect=RuntimeError)
        gst_player._update_time()
        assert gst_player.position.time is None

    def test_calls_self_dot_query_position(self):

        """
        _update_time() must call self._query_position() in order to update the time
        """
        gst_player, _ = self.init_mocks()
        gst_player._update_time()
        gst_player._query_position.assert_called()

    def test_returns_true_when_time_is_updated_sccessfully(self):
        """
        _update_time() must return True if it wants to continue being called periodically.
        """
        gst_player, _ = self.init_mocks()
        assert gst_player._update_time() is True

    def test_returns_true_when_time_is_not_updated_successfully(self):
        """
        _update_time() must return True if it wants to continue being called periodically.
        """
        gst_player, _ = self.init_mocks()
        gst_player._query_position = mock.Mock(side_effect=RuntimeError)
        assert gst_player._update_time() is True


# noinspection PyPep8Naming
class Test_QueryPosition:
    """Unit tests for method query_position()"""
    cur_time = 12345678

    def init_mocks(self):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        gst_player = player.GstPlayer()
        gst_player.pipeline = mock.Mock()
        gst_player.pipeline.query_position = mock.Mock(return_value=(True, self.cur_time))
        return gst_player

    def test_calls_pipeline_dot_query_position_correctly(self):
        """
        Assert that _query_position() calls gst_player.pipeline.query_position() to retrieve
        the current position in the playback stream.

        Assert that gst_player.pipeline.query_position() is called with Gst.Format.TIME as the parameter.
        This necessary because _query_position() returns the current time, and not frames or something else.
        """
        gst_player = self.init_mocks()
        gst_player._query_position()
        gst_player.pipeline.query_position.assert_called()
        gst_player.pipeline.query_position.assert_called_with(Gst.Format.TIME)

    def test_returns_current_position_if_pipeline_query_was_a_success(self):
        """
        Assert that _query_position() returns the current time if gst_player.pipeline.query_position()
        successfully executes the query.
        """
        gst_player = self.init_mocks()
        cur_time = gst_player._query_position()
        assert cur_time == self.cur_time

    def test_raises_runtime_error_if_pipeline_fails_to_query_position(self):
        """
        Assert that _query_position() raises runtimeError if gst_player.pipeline.query_position()
        fails to execute the query.
        """
        gst_player = self.init_mocks()
        gst_player.pipeline.query_position.return_value = (False, self.cur_time)
        with pytest.raises(RuntimeError):
            gst_player._query_position()


# noinspection PyPep8Naming
class Test_QueryDuration:
    """Unit tests for method _query_duration()"""
    duration = 12345678

    def init_mocks(self):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        gst_player = player.GstPlayer()
        gst_player.pipeline = mock.Mock()
        gst_player.pipeline.query_duration = mock.Mock(return_value=(True, self.duration))
        return gst_player

    def test_calls_pipeline_dot_query_duration_correctly(self):
        """
        Assert that _query_duration() calls gst_player.pipeline.query_duration() to retrieve
        the current duration of the playback stream.

        Assert that gst_player.pipeline.query_duration() is called with Gst.Format.TIME as the parameter.
        This necessary because _query_duration() returns the current duration, and not frames or something else.
        """
        gst_player = self.init_mocks()
        gst_player._query_duration()
        gst_player.pipeline.query_duration.assert_called()
        gst_player.pipeline.query_duration.assert_called_with(Gst.Format.TIME)

    def test_returns_current_duration_if_pipeline_query_was_a_success(self):
        """
        Assert that _query_duration() returns the current duration if gst_player.pipeline.query_duration()
        successfully executes the query.
        """
        gst_player = self.init_mocks()
        duration = gst_player._query_duration()
        assert duration == self.duration

    def test_raises_runtime_error_if_pipeline_fails_to_query_duration(self):
        """
        Assert that _query_duration() raises runtimeError if gst_player.pipeline.query_duration()
        fails to execute the query.
        """
        gst_player = self.init_mocks()
        gst_player.pipeline.query_duration.return_value = (False, self.duration)
        with pytest.raises(RuntimeError):
            gst_player._query_duration()


class TestSetPosition:
    """Unit test for method play()"""

    @staticmethod
    def init_mocks():
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        gst_player = player.GstPlayer()
        gst_player.pipeline = mock.Mock()
        gst_player.pipeline.seek_simple = mock.Mock(return_value=True)
        return gst_player

    def test_cals_self_dot_pipeline_dot_seek_simple(self):
        """
        Assert that set_position() calls self.pipeline.seek_simple() with the correct args.
        """
        gst_player = self.init_mocks()
        time = 30
        gst_time = time * Gst.SECOND
        gst_player.set_position(t_seconds=time)
        call_kwargs = {
            'format': Gst.Format.TIME,
            'seek_flags': Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            'seek_pos': gst_time
        }
        assert gst_player.pipeline.seek_simple.call_args.kwargs == call_kwargs

    def test_raises_runtime_error_if_self_dot_pipeline_dot_seek_simple_fails(self):
        """
        Asert that set_position() raises RuntimeError if self.pipeline.seek_simple()
        returns False.

        self.pipeline.seek_simple() returns False when the pipeline fails
        to set the position.
        """
        gst_player = self.init_mocks()
        gst_player.pipeline.seek_simple.return_value = False
        with pytest.raises(RuntimeError):
            gst_player.set_position(t_seconds=30)

