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
# pylint: disable=too-many-lines
# disabled because this needs to be long.
#
# pylint: disable=broad-except
# disabled because it is necessary to catch ALL exceptions and return them to their calling thread
#
# pylint: disable=raising-bad-type
# disabled because pylint doesn't know that There are
# exceptions being stored in dicts and passed to other threads.
#

"""
Unit test for class player.GstPlayer
"""
from unittest import mock
from threading import Thread
from threading import Lock
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import player
from player import GstPlayer


class StatusDict(dict):
    """
    Wrap a dict with some custom functions.
    """
    def __init__(self):
        super().__init__(self.get_new_status())

    def raise_if(self, *statuses):
        """
        Raise exceptions stored during the execution of an @g_control_thread

        @parameter: *statuses
            When given, raise_if() raises only the exception stored in those particular statuses.
            if no statuses are provided, raise_if() will look for exceptions in every status.

        Note:
            status 'unknown_exception' stores unaccounted for exceptions— set inside
            run_gstreamer_and_control_thread. It is a good idea to pass
            'unknown_exception' in addition to any provided *statuses.
        """
        if statuses:
            for status in statuses:
                if self[status]['exception']:
                    raise self[status]['exception']
        else:
            for name, status in self.items():
                if status['exception']:
                    raise status['exception']

    @staticmethod
    def get_new_status(status_name: str | None = None) -> dict:
        """
        Create and return a new status object.
        """
        # 'unknown_exception' stores unaccounted for exceptions. Set inside run_gstreamer_and_control_thread
        statuses = {
            'unknown_exception': {'exception': None},
            'query_state': {'state': None, 'exception': None},
            'load_stream': {'stream_loaded': False, 'exception': None},
            'query_position': {'position': None, 'exception': None},
            'set_playback_state': {'ret_val': None, 'signal_received': False, 'exception': None},
            'set_position': {'ret_val': None, 'signal_received': False, 'exception': None}
        }
        return statuses[status_name] if status_name else statuses


def g_control_thread(func):
    """
    Decorator for the test control threads.
    """
    def gct(loop: GLib.MainLoop,
            gst_player: GstPlayer,
            stream_data: player.StreamData,
            status: StatusDict,
            *args):
        try:
            wait_for_glib_loop_start()
            func(loop, gst_player, stream_data, status, *args)
        except Exception as e:
            status['unknown_exception']['exception'] = e
        finally:
            try:
                unload_stream(gst_player)
            except RuntimeError:
                pass
            GLib.idle_add(loop.quit)
    return gct


def query_state(gst_player: GstPlayer) -> dict:
    """
    query the state of the GStreamer pipeline.
    """
    def qs(gst_player: GstPlayer, lock: Lock, queried_state: dict):
        # Get state, timeout after 10 s.
        success, new, pen = gst_player.pipeline.get_state(player.StreamTime(10, 's').get_time())
        if success == Gst.StateChangeReturn.SUCCESS and pen == Gst.State.VOID_PENDING:
            queried_state['state'] = new
            lock.release()
        else:
            queried_state['exception'] = RuntimeError(
                f'failed to query the pipeline\'s state. state change return = {success}'
            )

    queried_state = {'state': None, 'exception': None}
    lock = Lock()
    lock.acquire()
    GstPlayer._g_idle_add_once(qs, gst_player, lock, queried_state)
    if not lock.acquire(timeout=10):
        raise RuntimeError('failed to query the pipeline\'s state.')
    return queried_state


def query_position(gst_player: GstPlayer, make_player_busy: bool = False) -> dict:
    """
    Call query_position().

    Sets test_gst_player.current_position to queried value.
    blocks until the query is complete.

    Returns: a dict containing the queried position and any exceptionsraised durint query execution.

    Raises: TimeoutError if the query doesn't complete after 10 seconds.
    """

    def qp(gst_player: GstPlayer, lock: Lock, queried_position: dict, make_player_busy: bool):
        """
        Run the query.
        """
        try:
            if make_player_busy:
                # pause() is a arbitrarily chosen method that is suitable
                # for triggering the busy flag inside GstPlayer.
                gst_player.pause()
            queried_position['position'] = gst_player.query_position()
        except Exception as e:
            queried_position['exception'] = e
        finally:
            lock.release()

    lock = Lock()
    lock.acquire()
    queried_position = StatusDict.get_new_status('query_position')

    GstPlayer._g_idle_add_once(qp, gst_player, lock, queried_position, make_player_busy)
    if not lock.acquire(timeout=10):
        raise TimeoutError('Failed to query the current position')
    return queried_position


def set_playback_state(gst_player: GstPlayer, state_change_method: callable, call_twice: bool = False) -> dict:
    """Call GstPlayer.play(), pause(), or stop()."""

    def sps(state_change_method: callable,
            status: dict,
            call_twice: bool = False):

        try:
            if call_twice:
                state_change_method(gst_player)
            status['ret_val'] = state_change_method(gst_player)
        except Exception as e:
            status['exception'] = e

    status = StatusDict.get_new_status('set_playback_state')
    lock = Lock()
    lock.acquire()
    gst_player.transmitter.connect_once('stream_ready', lock.release)
    GstPlayer._g_idle_add_once(sps, state_change_method, status, call_twice)

    status['signal_received'] = bool(lock.acquire(timeout=10))
    return status


def run_gstreamer_and_control_thread(control_thread, *additional_ct_args):
    """
    Start GstPlayer and the GLib.MainLoop, and spawn a control thread in the background.
    run_gstreamer_and_control_thread() will block until loop.quit() is called from the ct.

    The control thread will have to interact with GstPlayer via GLib.idle_add

    The control_thread must accept the following args: loop, gst_player, *additional_ct_args
    """
    gst_player = player.GstPlayer()
    loop = GLib.MainLoop()
    new_thread = Thread(target=control_thread, args=(loop, gst_player, *additional_ct_args))
    new_thread.daemon = True
    new_thread.start()
    loop.run()
    new_thread.join()


def wait_for_glib_loop_start():
    """
    Wait on GLib.loop to be functional.
    timeout after 10 s.
    Raises: RuntimeError if loop fails to start.
    """
    lock = Lock()
    # Allow up to 10 seconds for GLib.loop to start.
    lock.acquire()
    GstPlayer()._g_idle_add_once(lock.release)
    if not lock.acquire(timeout=10):
        raise RuntimeError('Failed to start GLib.loop')


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


def set_position(gst_player: GstPlayer, stream_time: player.StreamTime, call_twice: bool = False) -> dict:
    """
    Set the position of a stream.

    call_twice: When True,  GstPlayer.set_position is called two times from the same GLib.idle_Add() call.
    The return value from the second call is recorded.

    returns {'exception': None, 'signal_received': False, 'ret_val': None}
    """

    def sp(gst_player: GstPlayer, stream_time: player.StreamTime, set_position_status: dict, call_twice: bool = False):
        """
        Set the position.
        """
        try:
            if call_twice:
                gst_player.set_position(stream_time)
            set_position_status['ret_val'] = gst_player.set_position(stream_time)
        except Exception as e:
            set_position_status['exception'] = e

    status = StatusDict.get_new_status('set_position')
    lock = Lock()
    lock.acquire()
    gst_player.transmitter.connect_once('stream_ready', lock.release)
    GstPlayer()._g_idle_add_once(sp, gst_player, stream_time, status, call_twice)

    status['signal_received'] = bool(lock.acquire(timeout=3))
    return status


def load_stream(gst_player: GstPlayer, stream_data: player.StreamData, call_twice: bool = False) -> dict:
    """
    Load a stream into GstPlayer and wait for it to finish.

    Raises: RuntimeError if it timeouts after 10 seconds.
    """
    def ls(gst_player: GstPlayer,
           stream_data: player.StreamData,
           status: dict,
           call_twice: bool = False):
        try:
            if call_twice:
                gst_player.load_stream(stream_data)
            gst_player.load_stream(stream_data)
        except Exception as e:
            status['exception'] = e

    lock = Lock()
    lock.acquire()
    status = StatusDict.get_new_status('load_stream')
    gst_player.transmitter.connect_once('stream_ready', lock.release)

    GstPlayer()._g_idle_add_once(ls, gst_player, stream_data, status, call_twice)

    status['stream_loaded'] = bool(lock.acquire(timeout=10))
    return status


def unload_stream(gst_player):
    """
    Unload a stream from GstPlayer and wait for it to finish.

    Raises: RuntimeError if it timeouts after 10 seconds.
    """
    print('unload_stream')
    lock = Lock()
    lock.acquire()
    gst_player.transmitter.connect_once('stream_ready', lock.release)
    GstPlayer()._g_idle_add_once(gst_player.unload_stream)
    if not lock.acquire(timeout=10):
        raise RuntimeError('Failed to load test_file')


class TestLoadStream:
    """Unit tests for method load_stream()"""
    stream_loaded_flag = False
    runtime_error_raised = False

    def test_loadstream_triggers_ready_callback(self):
        """
        Show that stream_ready signal is sent after load_stream() has finished all of its tasks.
        """

        @g_control_thread
        def control_thread(_,
                           gst_player: GstPlayer,
                           stream_data: player.StreamData,
                           status: dict):
            """
            Instruct GstPlayer to load a stream
            """
            status['load_stream'] |= load_stream(gst_player, stream_data)

        for i in range(100):
            status = StatusDict()
            stream_data = get_new_stream_data()
            run_gstreamer_and_control_thread(control_thread, stream_data, status)
            status.raise_if()

            assert status['load_stream']['stream_loaded'], f'failure on {i}th iteration'

    def test_raises_exception_if_a_stream_is_already_loaded(self):
        """
        Assert that load_stream() raises a RuntimeError if attempting to load a stream without first
        cleaning up any previous stream.
        """

        @g_control_thread
        def control_thread(_,
                           gst_player: GstPlayer,
                           stream_data: player.StreamData,
                           status: dict):
            """
            Instruct GstPlayer to load a stream and immediately call load_stream again.
            """
            status['load_stream'] |= load_stream(gst_player, stream_data, call_twice=True)

        status = StatusDict()
        stream_data = get_new_stream_data()
        run_gstreamer_and_control_thread(control_thread, stream_data, status)
        status.raise_if('unknown_exception')

        assert isinstance(status['load_stream']['exception'], RuntimeError)

    def test_sets_position_to_time_stored_in_stream_data(self):
        """
        Show that load_stream() sets the playback position to the position
        stored in the StreamData parameter.
        """

        @g_control_thread
        def control_thread(_: GLib.MainLoop,
                           gst_player: GstPlayer,
                           stream_data: player.StreamData,
                           status: dict):

            status['load_stream'] |= load_stream(gst_player, stream_data)
            if status['load_stream']['stream_loaded']:
                status['query_position'] |= query_position(gst_player)

        start_positions = [player.StreamTime(0, 's'), player.StreamTime(5, 's')]
        for _ in range(100):
            for position in start_positions:

                stream_data = get_new_stream_data()
                stream_data.position = position
                status = StatusDict()
                run_gstreamer_and_control_thread(control_thread, stream_data, status)
                status.raise_if()

                assert status['query_position']['position'].get_time() == position.get_time()

    def test_loads_stream_in_paused_state(self):
        """
        Show that after calling load_stream(), that stream will be in the paused state.
        """

        @g_control_thread
        def control_thread(_,
                           gst_player: GstPlayer,
                           stream_data: player.StreamData,
                           status: dict):
            """
            From a background thread, instruct GstPlayer to load a stream and query its state.
            """
            status['load_stream'] |= load_stream(gst_player, stream_data)
            if status['load_stream']['stream_loaded']:
                status['query_state'] |= query_state(gst_player)

        for _ in range(100):
            status = StatusDict()
            stream_data = get_new_stream_data()
            run_gstreamer_and_control_thread(control_thread, stream_data, status)
            status.raise_if()

            assert status['query_state']['state'] == Gst.State.PAUSED


class TestPlayPauseStop:
    """Unit test for methods play(), pause(), and stop()"""

    def test_play_sets_pipeline_to_playing_state(self):
        """Assert that play() sets the gstreamer pipeline to the playing state."""

        @g_control_thread
        def control_thread(_,
                           gst_player: GstPlayer,
                           stream_data: player.StreamData,
                           status: dict):
            """
            From a background thread, instruct GStreamer to load and play a stream.
            """
            status['load_stream'] |= load_stream(gst_player, stream_data)
            status['initial_state'] |= query_state(gst_player)

            status['set_playback_state'] |= set_playback_state(gst_player, GstPlayer.play)
            # Record the new state for use in the assertion.
            status['query_state'] |= query_state(gst_player)

            # Show that it works when Gstreamer is already in the playing state
            status['set_playback_state_1'] |= set_playback_state(gst_player, GstPlayer.play)
            status['query_state_1'] |= query_state(gst_player)

        for _ in range(100):
            stream_data = get_new_stream_data()
            status = StatusDict()
            status['initial_state'] = StatusDict.get_new_status('query_state')
            status['query_state_1'] = StatusDict.get_new_status('query_state')
            status['set_playback_state_1'] = StatusDict.get_new_status('set_playback_state')

            run_gstreamer_and_control_thread(control_thread, stream_data, status)
            status.raise_if()

            assert status['initial_state']['state'] != status['query_state']['state']
            assert status['query_state']['state'] == Gst.State.PLAYING, 'Failed to set state to playing'
            assert status['query_state_1']['state'] == Gst.State.PLAYING, \
                'Failed to set state to playing when already in the playing state.'

    def test_pause_sets_pipeline_to_paused_state(self):
        """Assert that pause() sets the gstreamer pipeline to the paused state."""

        @g_control_thread
        def control_thread(_,
                           gst_player: GstPlayer,
                           stream_data: player.StreamData,
                           status: dict):

            status['load_stream'] |= load_stream(gst_player, stream_data)

            # set the initial state to playing.
            status['set_playback_state'] |= set_playback_state(gst_player, GstPlayer.play)
            status['initial_state'] |= query_state(gst_player)

            status['set_playback_state_1'] |= set_playback_state(gst_player, GstPlayer.pause)
            status['query_state'] |= query_state(gst_player)

            # Show that it still works when Gstreamer is already in the paused state
            status['set_playback_state_2'] |= set_playback_state(gst_player, GstPlayer.pause)
            status['query_state_1'] |= query_state(gst_player)

        for _ in range(100):
            stream_data = get_new_stream_data()

            status = StatusDict()
            status['initial_state'] = StatusDict.get_new_status('query_state')
            status['query_state_1'] = StatusDict.get_new_status('query_state')
            status['set_playback_state_1'] = StatusDict.get_new_status('set_playback_state')
            status['set_playback_state_2'] = StatusDict.get_new_status('set_playback_state')

            run_gstreamer_and_control_thread(control_thread, stream_data, status)
            status.raise_if()

            # Show that the state actually changed.
            assert status['initial_state']['state'] != status['query_state']['state']
            # Show that GstPlayer is in the paused state.
            assert status['query_state']['state'] == Gst.State.PAUSED, \
                'Failed to set state to paused'
            assert status['query_state_1']['state'] == Gst.State.PAUSED, \
                'Failed to set state to paused when already in the paused state'

    def test_stop_sets_pipeline_to_paused_state_at_position_zero(self):
        """
        Show that stop() sets the pipeine to the paused state
        and moves the playback position to the beginning of the stream.
        """
        @g_control_thread
        def control_thread(_,
                           gst_player: GstPlayer,
                           stream_data: player.StreamData,
                           status: dict):
            """
            From a background thread, instruct GStreamer to load and pause a stream.
            """
            status['load_stream'] |= load_stream(gst_player, stream_data)
            # set the initial state to playing.
            status['set_playback_state'] |= set_playback_state(gst_player, GstPlayer.play)
            status['initial_state'] |= query_state(gst_player)

            # Call GstPlayer.stop().
            status['set_playback_state_1'] |= set_playback_state(gst_player, GstPlayer.stop)
            status['query_state'] |= query_state(gst_player)
            status['query_position'] |= query_position(gst_player)

            # Show that it still works when Gstreamer is already in the paused/stopped state
            status['set_playback_state_2'] |= set_playback_state(gst_player, GstPlayer.stop)
            status['query_state_1'] |= query_state(gst_player)
            status['query_position_1'] |= query_position(gst_player)

        stream_data = get_new_stream_data()

        status = StatusDict()
        status['initial_state'] = StatusDict.get_new_status('query_state')
        status['query_state_1'] = StatusDict.get_new_status('query_state')
        status['query_position_1'] = StatusDict.get_new_status('query_position')
        status['set_playback_state_1'] = StatusDict.get_new_status('set_playback_state')
        status['set_playback_state_2'] = StatusDict.get_new_status('set_playback_state')

        run_gstreamer_and_control_thread(control_thread, stream_data, status)
        status.raise_if()

        # Show that the state actually changed.
        assert status['initial_state']['state'] != status['query_state']['state']

        # stop() should return True if successful, set state to paused, and set position to zero.
        assert status['query_state']['state'] == Gst.State.PAUSED
        assert status['set_playback_state_1']['ret_val'] is True
        assert status['query_position']['position'] == player.StreamTime(0)

        # Show that it works when already stopped(), meaning that it is paused at position zero.
        assert status['query_state_1']['state'] == Gst.State.PAUSED
        assert status['set_playback_state_2']['ret_val'] is True
        assert status['query_position_1']['position'] == player.StreamTime(0)

    def test_state_change_methods_return_false_if_locked(self):
        """
        Show that GstPlayer.play(), pause(), and stop() returns False
        if GstPlayer is already busy with a state-change.
        """

        @g_control_thread
        def control_thread(_,
                           gst_player: GstPlayer,
                           stream_data: player.StreamData,
                           status: dict,
                           state_change_method):
            """
            From a background thread, instruct GStreamer to execute a state change twice consecutively.
            """
            status['load_stream'] |= load_stream(gst_player, stream_data)
            status['set_playback_state'] |= set_playback_state(gst_player, state_change_method, call_twice=True)

        state_change_methods = (GstPlayer.play, GstPlayer.pause, GstPlayer.stop)
        for method in state_change_methods:
            stream_data = get_new_stream_data()
            status = StatusDict()
            run_gstreamer_and_control_thread(control_thread, stream_data, status, method)
            status.raise_if()

            assert status['set_playback_state']['ret_val'] is False


class TestSetPosition:
    """Unit test for method set_position()"""

    def test_sets_correct_position_and_sends_stream_ready_when_complete(self):
        """
        Show that the 'stream_ready' signal is transmitted after the seek is finished.
        Show that the stream has been accurately set to the new position.
        """
        @g_control_thread
        def control_thread(_,
                           gst_player: GstPlayer,
                           stream_data: player.StreamData,
                           status: dict,
                           new_position):
            """
            From a background thread, instruct GstPlayer to set the position of the stream.
            """
            status['load_stream'] |= load_stream(gst_player, stream_data)
            status['set_position'] |= set_position(gst_player, new_position)
            status['query_position'] |= query_position(gst_player)

        status = StatusDict()
        stream_data = get_new_stream_data()
        new_position = player.StreamTime(3, 's')

        run_gstreamer_and_control_thread(control_thread, stream_data, status, new_position)
        status.raise_if()

        assert status['load_stream']['stream_loaded'] is True, 'Failed to set up test'
        assert status['set_position']['signal_received'] is True, 'Failed to send stream_ready signal'
        assert status['query_position']['position'] == new_position, \
            'Failed to set stream to correct position'

    def test_raises_exception_when_new_position_out_of_range(self):
        """
        Show that set_position() raises a RuntimeError if the new
        position is outside the range [0, infinity)

        Show that the stream_ready flag is not transmitted when this is the case.
        """
        @g_control_thread
        def control_thread(_,
                           gst_player: GstPlayer,
                           stream_data: player.StreamData,
                           status: dict,
                           new_position):
            """
            From a background thread, instruct GstPlayer to set the position of the stream.
            """
            status['load_stream'] |= load_stream(gst_player, stream_data)
            status['set_position'] |= set_position(gst_player, new_position)

        stream_data = get_new_stream_data()
        new_position = player.StreamTime(-1, 's')
        status = StatusDict()

        run_gstreamer_and_control_thread(control_thread, stream_data, status, new_position)
        status.raise_if('unknown_exception', 'load_stream')
        assert isinstance(status['set_position']['exception'], RuntimeError)
        assert status['set_position']['signal_received'] is False, \
            "Set_position raised a RuntimeError, but the 'stream_ready' flag was transmitted anyway."

    def test_returns_false_when_gst_player_busy(self):
        """
        Show that set_position returns False when GstPlayer is already busy with another stream task.
        """
        @g_control_thread
        def control_thread(_,
                           gst_player: GstPlayer,
                           stream_data: player.StreamData,
                           status: dict,
                           new_position):
            """
            From a background thread, instruct GstPlayer to set the position of the stream twice.
            """
            status['load_stream'] |= load_stream(gst_player, stream_data)
            status['set_position'] |= set_position(gst_player, new_position, call_twice=True)

        stream_data = get_new_stream_data()
        new_position = player.StreamTime(3, 's')
        status = StatusDict()

        run_gstreamer_and_control_thread(control_thread, stream_data, status, new_position)
        status.raise_if()
        assert status['load_stream']['stream_loaded'] is True, 'Failed to set up test'
        assert status['set_position']['ret_val'] is False


class TestQueryPosition:
    """
    Test for method query_position()
    """

    def test_returns_current_position_in_stream(self):
        """
        Show that query_position() returns the current playback position in the stream.
        """

        @g_control_thread
        def control_thread(_,
                           gst_player: GstPlayer,
                           stream_data: player.StreamData,
                           status: dict):
            """
            From a background thread, instruct GstPlayer to query the position of the stream.
            """
            status['load_stream'] |= load_stream(gst_player, stream_data)
            status['query_position'] |= query_position(gst_player)

        for position in (0, 5):
            stream_data = get_new_stream_data()
            stream_data.position.set_time(position, 's')
            status = StatusDict()
            run_gstreamer_and_control_thread(control_thread, stream_data, status)
            status.raise_if()

            assert status['query_position']['position'].get_time('s') == position

    def test_raises_runtime_error_when_gst_player_is_busy(self):
        """
        Show that query_position() raises a RutimeError if
        GstPlayer is busy with another stream task.
        """

        @g_control_thread
        def control_thread(_,
                           gst_player: GstPlayer,
                           stream_data: player.StreamData,
                           status: dict):
            """
            From a background thread, instruct GstPlayer to query the position of the stream
            while GstPlayer is busy with another stream task.
            """
            status['load_stream'] |= load_stream(gst_player, stream_data)
            status['query_position'] |= query_position(gst_player, make_player_busy=True)

        stream_data = get_new_stream_data()
        status = StatusDict()
        run_gstreamer_and_control_thread(control_thread, stream_data, status)
        status.raise_if('unknown_exception', 'load_stream')

        assert isinstance(status['query_position']['exception'], RuntimeError)

    def test_raises_runtime_error_when_gstreamer_fails_to_query_position(self):
        """
        Show that query_position() raises a RutimeError if
        Gstreamer fails to successfully query the position from the pipeline.
        """

        @g_control_thread
        def control_thread(_,
                           gst_player: GstPlayer,
                           stream_data: player.StreamData,
                           status: dict):
            """
            From a background thread, instruct GstPlayer to query the position of the stream.
            Force a False return value for the query performed internally by GstPlayer.query_position()
            """
            status['load_stream'] |= load_stream(gst_player, stream_data)
            gst_player.pipeline.query_position = mock.Mock(return_value=(False, None))
            status['query_position'] |= query_position(gst_player)

        stream_data = get_new_stream_data()
        status = StatusDict()
        run_gstreamer_and_control_thread(control_thread, stream_data, status)
        status.raise_if('unknown_exception', 'load_stream')

        assert isinstance(status['query_position']['exception'], RuntimeError)
