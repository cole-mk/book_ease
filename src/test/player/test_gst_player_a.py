# -*- coding: utf-8 -*-
#
#  test_gst_player_a.py
#
#  This file is part of book_ease.
#
#  Copyright 2022 mark cole <mark@capstonedistribution.com>
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
# pylint: disable=too-many-lines
# disabled because this needs to be long.
#
# pylint: disable=broad-except
# disabled because it is necessary to catch ALL exceptions and return them to their calling thread
#
# pylint: disable=raising-bad-type
# disabled because pylint doesn't know that There are
# exceptions being stored in dicts and passed to other threads.

"""
Unit test for class player.GstPlayerA
"""
from unittest import mock
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GLib

import player
from player import GstPlayerA
from player import GstPlayerError


class TestLoadStream:
    """Unit test for method load_stream()"""

    def test_calls_load_stream_when_queue_empty(self):
        """
        Show that calling load_stream() queues the load_stream() for GstPlayer
        """
        player_a = GstPlayerA()
        player_a._gst_player = get_mock_gst_player()
        stream_data = get_new_stream_data()

        player_a.load_stream(stream_data)
        assert player_a._gst_player.load_stream.called

    def test_queues_load_stream_when_previous_call_in_progress(self):
        """
        Show that the call to load_stream() gets placed into a queue for later processing
        when GstPlayerA is waiting on a previous call to complete.
        """
        player_a = GstPlayerA()
        player_a._gst_player = get_mock_gst_player()
        stream_data = get_new_stream_data()

        player_a.play()
        player_a.load_stream(stream_data)

        assert player_a._gst_player.load_stream.call_count == 0, \
            'GstPlayer.load_stream() should not have been called'

        player_a._gst_player.transmitter.send('stream_ready')

        assert player_a._gst_player.load_stream.call_count == 1

    def test_signals_stream_loaded(self):
        """
        Show that when a load_stream() command is passed to GstPlayer,
        GstPlayerA signals "stream_loaded" once GstPlayer has finished.
        """
        player_a = GstPlayerA()
        player_a._gst_player = get_mock_gst_player()

        stream_loaded_callback = mock.Mock()
        player_a.transmitter.connect('stream_loaded', stream_loaded_callback)

        stream_data = get_new_stream_data()
        player_a.load_stream(stream_data)

        player_a._gst_player.transmitter.send('stream_ready')
        # send GstPlayer::stream_ready signal a second time to make sure
        # duplicate stream_loaded signals aren't getting sent.
        player_a._gst_player.transmitter.send('stream_ready')

        stream_loaded_callback.assert_called()
        stream_loaded_callback.assert_called_once()


class TestUnloadStream:
    """
    Unit test for method unload_stream()
    """

    def test_queues_unload_stream_when_previous_call_in_progress(self):
        """
        Show that the call to unload_stream() gets placed into a queue for later processing
        when GstPlayerA is waiting on a previous call to complete.
        """
        player_a = GstPlayerA()
        player_a._gst_player = get_mock_gst_player()

        player_a.play()
        player_a.unload_stream()

        assert player_a._gst_player.unload_stream.call_count == 0, \
            'GstPlayer.unload_stream() should not have been called'
        player_a._gst_player.transmitter.send('stream_ready')
        assert player_a._gst_player.unload_stream.call_count == 1

    def test_calls_unload_stream_when_queue_empty(self):
        """
        Show that unload_stream() calls GstPlayer.unload_stream() immediately
        when the queue is empty.
        """
        player_a = GstPlayerA()
        player_a._gst_player = get_mock_gst_player()

        player_a.unload_stream()
        assert player_a._gst_player.unload_stream.called

    def test_clears_queue_before_appending_to_queue(self):
        """
        Show that unload_stream() clears the queue before appending itself to that queue.
        The reason is that unload_stream is just going to undo anything that is queued up.
        """
        player_a = GstPlayerA()
        player_a._gst_player = get_mock_gst_player()

        player_a.play()
        player_a.play()
        player_a.play()
        assert len(player_a._deque) == 2, 'Failed to set baseline for test.'

        player_a.unload_stream()
        assert len(player_a._deque) == 1, 'Failed to clear queue before appending unload_stream().'


class TestPlay:
    """
    Unit test for method GstPlayerA.play()
    """

    def test_queues_play_when_previous_call_in_progress(self):
        """
        Show that a call to gst_player.play() is loaded into the queue
        when GstPlayerA is waiting on another call to complete.
        """
        player_a = GstPlayerA()
        player_a._gst_player = get_mock_gst_player()

        player_a.pause()
        player_a.play()
        assert player_a._gst_player.play.call_count == 0, 'GstPlayer.play() should not have been called.'
        player_a._gst_player.transmitter.send('stream_ready')
        assert player_a._gst_player.play.call_count == 1, 'GstPlayer.play() should have been called exactly once.'

    def test_calls_play_when_queue_empty(self):
        """
        Show that GstPlayer.play gets called immediately when the queue is empty.
        """
        player_a = GstPlayerA()
        player_a._gst_player = get_mock_gst_player()

        player_a.play()
        assert player_a._gst_player.play.call_count == 1


class TestPause:
    """
    Unit test for method GstPlayerA.pause()
    """

    def test_queues_pause_when_when_previous_call_in_progress(self):
        """
        Show that a call to gst_player.pause() is loaded into the queue
        when GstPlayerA is waiting on another call to complete.
        """
        player_a = GstPlayerA()
        player_a._gst_player = get_mock_gst_player()

        player_a.play()
        player_a.pause()
        assert player_a._gst_player.pause.call_count == 0, 'GstPlayer.pause() should not have been called'
        player_a._gst_player.transmitter.send('stream_ready')
        assert player_a._gst_player.pause.call_count == 1

    def test_calls_pause_when_queue_empty(self):
        """
        Show that GstPlayer.pause gets called immediately hen the queue is empty.
        """
        player_a = GstPlayerA()
        player_a._gst_player = get_mock_gst_player()

        player_a.pause()
        assert player_a._gst_player.pause.call_count == 1


class TestStop:
    """
    Unit test for method GstPlayerA.stop()
    """

    def test_calls_stop_when_queue_empty(self):
        """
        Show that stop() calls GstPlayer.stop immediately, if there are
        no pending calls in progress.
        """
        player_a = GstPlayerA()
        player_a._gst_player = mock.Mock()

        player_a.stop()
        assert player_a._gst_player.stop.called

    def test_queues_stop_when_previous_call_in_progress(self):
        """
        Show that a call to gst_player.stop() is loaded into the queue,
        when a previous call is pending a stream_ready callback.
        """
        player_a = GstPlayerA()
        player_a._gst_player = get_mock_gst_player()

        player_a.play()
        player_a.stop()

        assert player_a._gst_player.stop.call_count == 0, \
            'GstPlayer.stop() should not have been called.'

        player_a._gst_player.transmitter.send('stream_ready')

        assert player_a._gst_player.stop.call_count == 1, \
            'GstPlayer.stop() should have been called exactly once.'


class TestSetPosition:
    """
    Unit test for method GstPlayerA.set_position()
    """

    def test_queues_set_position_when_previous_call_in_progress(self):
        """
        Show that a call to gst_player.set_position() is loaded into the queue.
        """
        player_a = GstPlayerA()
        player_a._gst_player = get_mock_gst_player()
        new_position = player.StreamTime()

        player_a.pause()
        player_a.set_position(new_position)

        assert player_a._gst_player.set_position.call_count == 0, \
            'GstPlayer.set_position() should not have been called.'
        player_a._gst_player.transmitter.send('stream_ready')
        assert player_a._gst_player.set_position.call_count == 1, \
            'GstPlayer.set_position() should have been called exactly once.'

    def test_updates_previous_position_changes_in_queue(self):
        """
        Show that set_position() updates the position of any previous set_position
        commands in the queue.
        """
        player_a = GstPlayerA()
        player_a._gst_player = get_mock_gst_player()
        position_1 = player.StreamTime(1)
        position_2 = player.StreamTime(2)

        player_a.pause()
        player_a.set_position(position_1)
        player_a.set_position(position_2)

        player_a._gst_player.transmitter.send('stream_ready')
        player_a._gst_player.transmitter.send('stream_ready')

        assert player_a._gst_player.set_position.call_count == 1, \
            'GstPlayer.set_position() should have been called exactly once,' \
            'when the two calls were supposed to be merged.'

        called_position = player_a._gst_player.set_position.call_args[0]
        assert called_position[0].get_time() == 2, \
            'The first call placed inthe queue did not get updated with the new position.'

    def test_calls_set_position_when_queue_empty(self):
        """
        Show that set_position() calls GstPlayer.set_position immediately, if there are
        no pending calls in progress.
        """
        player_a = GstPlayerA()
        player_a._gst_player = get_mock_gst_player()
        position = player.StreamTime(1)

        player_a.set_position(position)
        assert player_a._gst_player.set_position.called


class TestQueryPosition:
    """
    Unit test for method query_position().
    """

    def test_queries_position_from_gst_player_when_queue_empty(self):
        """
        Show that query_position() returns a StreamTime object retrieved from GstPlayer.
        """
        player_a = GstPlayerA()
        player_a._gst_player = mock.Mock()
        g_position = player.StreamTime()
        player_a._gst_player.query_position = mock.Mock(return_value=g_position)

        pos = player_a.query_position()
        assert pos is g_position

    def test_returns_queued_position_when_it_exists(self):
        """
        Show that query_position() returns the StreamTime object stored in the queue
        if there is a set_position command in the queue.
        """
        player_a = GstPlayerA()
        player_a._gst_player = get_mock_gst_player()

        player_a._gst_player.query_position = mock.Mock(
            side_effect=GstPlayerError('gst_player.query_position should not have been called')
        )

        position_1 = player.StreamTime(1)
        queued_position = player.StreamTime(2)

        # This first should be popped, the second queued
        player_a.set_position(position_1)
        player_a.set_position(queued_position)

        pos = player_a.query_position()
        assert pos is not position_1
        assert pos is queued_position


def get_new_stream_data() -> player.StreamData:
    """
    Get a new StreamData object prepared for testing
    """
    stream_data = player.StreamData()
    stream_data.path = 'test/data/audio/test_file.mp3'
    stream_data.position = player.StreamTime(0)
    stream_data.playlist_id = 1
    stream_data.pl_track_id = 1
    stream_data.track_number = 13
    return stream_data


class TestPop:
    """
    Unit test for method pop().
    """

    def test_runtime_error_clears_the_queue(self):
        """
        Shows that any pending commands are removed from the queue,
        if the current command results in a GstPlayerError.
        """
        player_a = GstPlayerA()
        player_a._gst_player.play = mock.Mock(side_effect=[True, GstPlayerError, True])

        player_a.play()
        player_a.play()
        player_a.play()

        assert len(player_a._deque) == 2, 'Failed to initialize test correctly.'
        player_a._gst_player.transmitter.send('stream_ready')
        assert len(player_a._deque) == 0

    def test_cmd_not_popped_when_gst_player_busy(self):
        """
        Show that pop() does not remove a command from the queue when GstPlayer is busy, returns False.
        """
        player_a = GstPlayerA()
        player_a._gst_player = get_mock_gst_player(return_values=False)
        position_1 = player.StreamTime(1)

        player_a.set_position(position_1)
        player_a.pop()
        player_a.pop()
        player_a.pop()
        assert player_a._gst_player.set_position.call_count == 4

    def test_pop_called_correct_number_of_times_when_queue_was_filled(self):
        """
        Basicaly make sure that pop() only subscribes once to stream_ready
        """
        player_a = GstPlayerA()
        player_a._gst_player = get_mock_gst_player(return_values=True)

        # Wrap pop() with a mock, so we can use call_count attribute.
        orig_pop = player_a.pop
        player_a.pop = mock.Mock(side_effect=orig_pop)

        # should call pop itself
        player_a.play()
        # These should not call pop themselves
        player_a.play()
        player_a.play()
        player_a.play()
        # pop sould onnly be called one more time
        player_a._gst_player.transmitter.send('stream_ready')
        assert player_a.pop.call_count == 2


class _TestGMainLoopIntegration:
    """
    Integration test showing that GstPlayerA adds and removes itself grom the Glib.MainLoop
    as needed.
    """

    def init_mocks(self) -> list[dict]:
        """
        Get a list of the public GstPlayerA commands that make use of the qeue
        """
        m_gst_player = get_mock_gst_player(return_values=True)
        queued_calls = [
            {
                'a_method': GstPlayerA.load_stream,
                'a_args': (get_new_stream_data(),),
                'm_gst_method': m_gst_player.load_stream
            },
            {
                'a_method': GstPlayerA.pause,
                'a_args': tuple(),
                'm_gst_method': m_gst_player.pause
            },
            {
                'a_method': GstPlayerA.play,
                'a_args': tuple(),
                'm_gst_method': m_gst_player.play
            },
            {
                'a_method': GstPlayerA.set_position,
                'a_args': (player.StreamTime(0),),
                'm_gst_method': m_gst_player.set_position
            },
            {
                'a_method': GstPlayerA.stop,
                'a_args': tuple(),
                'm_gst_method': m_gst_player.stop
            },
            {
                'a_method': GstPlayerA.unload_stream,
                'a_args': tuple(),
                'm_gst_method': m_gst_player.unload_stream
            }
        ]
        return m_gst_player, queued_calls

    def test_queable_commands_add_pop_to_loop(self):
        """
        Show that any of the public methods that rely on the queuing mechanism of GstPlayerA
        add GstPlayerA.pop to the event loop.
        """
        stream_data = get_new_stream_data()
        loop = GLib.MainLoop()
        main_context = loop.get_context()

        m_gst_player = get_mock_gst_player(return_values=True)
        queued_calls = [
            {
                'a_method': GstPlayerA.load_stream,
                'a_args': (get_new_stream_data(),),
                'm_gst_method': m_gst_player.load_stream
            },
            {
                'a_method': GstPlayerA.pause,
                'a_args': tuple(),
                'm_gst_method': m_gst_player.pause
            },
            {
                'a_method': GstPlayerA.play,
                'a_args': tuple(),
                'm_gst_method': m_gst_player.play
            },
            {
                'a_method': GstPlayerA.set_position,
                'a_args': (player.StreamTime(0),),
                'm_gst_method': m_gst_player.set_position
            },
            {
                'a_method': GstPlayerA.stop,
                'a_args': tuple(),
                'm_gst_method': m_gst_player.stop
            },
            {
                'a_method': GstPlayerA.unload_stream,
                'a_args': tuple(),
                'm_gst_method': m_gst_player.unload_stream
            }
        ]

        for cmd in queued_calls:
            player_a = GstPlayerA()
            player_a._gst_player = m_gst_player
            cmd['a_method'](player_a, *cmd['a_args'])
            cmd['a_method'](player_a, *cmd['a_args'])
            main_context.iteration(may_block=False)
            assert cmd['m_gst_method'].call_count == 1, cmd['a_method']
            # iterate one more time to empty the que in preparation for the next tested method
            main_context.iteration(may_block=False)

    def test_emptying_the_queue_removes_pop_from_evemt_loop(self):
        """
        Show that the event loop doesn't keep calling pop() once all
        commands in the queue have been executed successfully.
        """
        player_a = GstPlayerA()
        orig_pop = player_a.pop
        player_a.pop = mock.Mock(side_effect=orig_pop)

        loop = GLib.MainLoop()
        main_context = loop.get_context()
        # queue is empty, add pop to the event loop
        GLib.idle_add(player_a.pop)

        main_context.iteration(may_block=False)
        player_a.pop.assert_called_once()

        main_context.iteration(may_block=False)
        player_a.pop.assert_called_once()

        main_context.iteration(may_block=False)
        player_a.pop.assert_called_once()


def get_mock_gst_player(return_values: bool = True) -> player.GstPlayer:
    """
    Return an instance of GstPlayer that has had all public methods mocked out.

    parameter return_values: sets the return values for all mocked methods.
    """
    gst_player = player.GstPlayer()
    gst_player.load_stream = mock.Mock(return_value=return_values)
    gst_player.pause = mock.Mock(return_value=return_values)
    gst_player.play = mock.Mock(return_value=return_values)
    gst_player.set_position = mock.Mock(return_value=return_values)
    gst_player.stop = mock.Mock(return_value=return_values)
    gst_player.unload_stream = mock.Mock(return_value=return_values)
    return gst_player
