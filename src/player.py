# -*- coding: utf-8 -*-
#
#  player.py
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
# pylint: disable=consider-using-with
# disabled because the locks need to be released outside the context of where they're acquired.
#

"""
This module controls the playback of playlists.
"""

from __future__ import annotations
import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar
from typing import Literal
from lock_wrapper import Lock
import collections
import gi
gi.require_version('Gst', '1.0')
# gi.require_version('Gtk', '3.0')
# gi.require_version('GdkX11', '3.0')
# gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, GLib
import audio_book_tables
import signal_
if TYPE_CHECKING:
    from pathlib import Path
    import book


class PlayerDBI:
    """Class to interface the Player class with the database."""

    def __init__(self):
        self.player_position = audio_book_tables.PlayerPosition
        self.player_position_joined = audio_book_tables.JoinTrackFilePlTrackPlayerPosition
        self.pl_track = audio_book_tables.PlTrack
        self.track = audio_book_tables.TrackFile
        with audio_book_tables.DB_CONNECTION.query() as con:
            self.player_position.init_table(con)
            self.pl_track.init_table(con)
            self.track.init_table(con)

    def get_number_of_pl_tracks(self, playlist_id: int) -> int:
        """
        Get the number of tracks in the playlist.
        """
        with audio_book_tables.DB_CONNECTION.query() as con:
            return self.pl_track.get_track_count_by_playlist_id(con, playlist_id)

    def get_saved_position(self, playlist_id: int) -> StreamData:
        """Get the playlist's saved position."""
        with audio_book_tables.DB_CONNECTION.query() as con:
            row = self.player_position_joined.get_row_by_playlist_id(con=con, playlist_id=playlist_id)

        if row is not None:
            position = StreamData()
            position.path = row['path']
            position.position = StreamTime(row['time'])
            position.pl_track_id = row['pl_track_id']
            position.playlist_id = row['playlist_id']
            position.track_number = row['track_number']
            position.mark_saved_position()
            return position
        return None

    def get_new_position(self, playlist_id: int, track_number: int, time_: StreamTime) -> StreamData:
        """
        Create a StreamData object set to the beginning of the track_number of the playlist.
        Return an None object if nothing was found.
        """
        track_id, pl_track_id = self.get_track_id_pl_track_id_by_number(
            playlist_id=playlist_id,
            track_number=track_number
        )

        if track_id is not None:
            if path:= self.get_path_by_id(track_id=track_id) is not None:
                position = StreamData(
                    pl_track_id=pl_track_id,
                    track_number=track_number,
                    playlist_id=playlist_id,
                    path=path,
                    position=time_
                )
                return position
        return None

    def save_position(self, pl_track_id: int, playlist_id: int, time_: StreamTime):
        """Save player position to the database."""
        with audio_book_tables.DB_CONNECTION.query() as con:
            self.player_position.upsert_row(
                con=con,
                pl_track_id=pl_track_id,
                playlist_id=playlist_id,
                time=time_.get_time()
            )

    def get_track_id_pl_track_id_by_number(self, playlist_id: int, track_number: int) -> tuple[int | None, int | None]:
        """get the track_id and pl_track_id given a track_number and playlist_id as arguments."""
        with audio_book_tables.DB_CONNECTION.query() as con:
            rows = self.pl_track.get_rows_by_playlist_id(con=con, playlist_id=playlist_id)
        if rows is not None:
            for row in rows:
                if row['track_number'] == track_number:
                    return row['track_id'], row['id']
        return None, None

    def get_path_by_id(self, track_id: int) -> str | pathlib.Path:
        """
        Get a track's path based on track_id

        Return: Path or None
        """
        with audio_book_tables.DB_CONNECTION.query() as con:
            if row := self.track.get_row_by_id(con=con, id_=track_id):
                return row['path']
        return None


class StreamTime:
    """
    Wrapper for storing time values in StreamData.
    Provides unit conversion functionality.
    """

    # Base unit for time storage is nanoseconds.
    _time_conversions: ClassVar[dict] = {
        'ns': 1,
        'ms': pow(10, 6),
        's': pow(10, 9)
    }

    def __init__(self, time_: int | float = None, unit: str = 'ns'):
        if time_ is None:
            self._time = time_
        else:
            self.set_time(time_=time_, unit=unit)

    def __eq__(self, other):
        if isinstance(other, StreamTime):
            if other._time == self._time:
                return True
            return False
        raise TypeError(f'Cannot compare {StreamTime} and {type(other)}')

    def __gt__(self, other):
        if isinstance(other, StreamTime):
            if self._time > other._time:
                return True
            return False
        raise TypeError(f'Cannot compare {StreamTime} and {type(other)}')

    def __add__(self, other):
        if isinstance(other, StreamTime):
            sum_ = self.get_time() + other.get_time()
            return StreamTime(sum_)
        raise TypeError(f'expected {StreamTime} but got {type(other)}')

    def __sub__(self, other):
        if isinstance(other, StreamTime):
            diff = self.get_time() - other.get_time()
            return StreamTime(diff)
        raise TypeError(f'expected {StreamTime} but got {type(other)}')

    def __neg__(self):
        return StreamTime(self._time * -1)

    def __abs__(self):
        if self._time < 0:
            return -self
        return self

    def get_time(self, unit: str = 'ns'):
        """
        Get the stored time in the desired units, truncated to a whole number.
        """
        return int(self._time / self._time_conversions[unit])

    def set_time(self, time_: int | float, unit: str = 'ns'):
        """
        Set the stored time in units, truncated to a whole number.
        """
        self._time = int(time_ * self._time_conversions[unit])


@dataclass
class StreamData:
    """Container for stream data."""

    path: str | None = None
    position: StreamTime | None = None
    duration: StreamTime | None = None
    track_number: int | None = None
    playlist_id: int | None = None
    pl_track_id: int | None = None
    last_saved_position: StreamTime = StreamTime(-1)

    def mark_saved_position(self):
        """
        Record what the time was when the position was last saved to the database.
        """
        self.last_saved_position.set_time(self.position.get_time())


class Player:
    """The model class for the media player backend"""

    def __init__(self):
        self.player_dbi = PlayerDBI()

        self.player_backend = GstPlayer()
        self.player_backend.transmitter.connect('time_updated', self._on_time_updated)
        self.player_backend.transmitter.connect('duration_ready', self._on_duration_ready)
        self.player_backend.transmitter.connect('eos', self._on_eos)

        self.stream_data = None
        self.skip_duration_short = StreamTime(3, 's')
        self.skip_duration_long = StreamTime(30, 's')

        self.transmitter = signal_.Signal()
        self.transmitter.add_signal('time_updated', 'duration_ready', 'eos')
        self.state = 'no_playlist_loaded'

    def _on_eos(self):
        """
        The media player backend has reached the end of the stream.
        """
        old_track_num = self.stream_data.track_number
        self.set_track_relative(1)
        if old_track_num < self.stream_data.track_number:
            # The end of the playlist has not yet been reached. Continue playback.
            self.play()

    def _get_incremented_track_number(self, track_delta: Literal[-1, 1]):
        """
        Get a new track number by incrementing the value of self.stream_data.track_number by track_delta,
        providing wrap-around functionality.

        This does not increment self.stream_data.track_number itself.
        """
        track_count = self.player_dbi.get_number_of_pl_tracks(self.stream_data.playlist_id)
        new_track_number = self.stream_data.track_number + track_delta
        if new_track_number >= track_count:
            new_track_number = 0
        elif new_track_number < 0:
            new_track_number = track_count - 1
        return new_track_number

    def set_track_relative(self, track_delta: Literal[-1, 1]):
        """
        Skip a number of tracks based on the value of track_delta.
        """
        new_track_number = self._get_incremented_track_number(track_delta)
        self.set_track(track_number=new_track_number)

    def set_track(self, track_number: int):
        """
        Set the current track to track_number.

        Raises: RuntimeError if set_track() fails to generate a completely instantiated StreamData object.
        """
        new_stream_data = self.player_dbi.get_new_position(
            playlist_id=self.stream_data.playlist_id,
            track_number=track_number,
            time_=StreamTime(0)
        )
        if new_stream_data.is_fully_set():
            try:
                self.player_backend.unload_stream()
            except RuntimeError:
                pass

            self.stream_data = new_stream_data
            self.player_backend.load_stream(stream_data=self.stream_data)
            self._save_position()
            if self.state == 'playing':
                self.play()
        else:
            raise RuntimeError('Failed to load track.')

    def _on_time_updated(self, position: StreamTime):
        """
        The media player backend has updated the playback position.
        """
        self.stream_data.position = position
        self.transmitter.send('time_updated', position)
        # Save position when 30 seconds elapsed.
        if position.get_time('s') - self.stream_data.last_saved_position.get_time('s') > 29:
            self._save_position()

    def _save_position(self):
        self.player_dbi.save_position(pl_track_id=self.stream_data.pl_track_id,
                                      playlist_id=self.stream_data.playlist_id,
                                      time_=self.stream_data.position)
        self.stream_data.mark_saved_position()

    def _on_duration_ready(self, duration: StreamTime):
        """
        The media player backend has found the duration of the stream.
        """
        self.stream_data.duration = duration
        self.transmitter.send('duration_ready', duration)

    def load_playlist(self, playlist_data: book.PlaylistData):
        """
        Load self.stream_data with a StreamData from the database if it exists, or set it to a newly created one that
        starts at the beginning of the first track in the playlist.
        """
        playlist_id = playlist_data.get_id()
        self.stream_data = self.player_dbi.get_saved_position(playlist_id=playlist_id)
        if self.stream_data.is_fully_set():
            self.player_backend.load_stream(stream_data=self.stream_data)
        else:
            # No saved position exists; load the first track.
            self.set_track(track_number=0)
        self.state = 'ready'

    def play(self):
        """
        Transport control method 'play'
        Calls on the media-player backend to play a stream.
        """
        self.player_backend.play()
        self.state = 'playing'

    def pause(self):
        """
        Transport control method 'pause'
        Calls on the media-player backend to pause a playing stream.
        """
        self.player_backend.pause()
        self.stream_data.position = self.player_backend.query_position()
        self._save_position()
        self.state = 'paused'

    def stop(self):
        """
        Transport control method 'stop'
        Calls on the media-player backend to stop a playing stream.
        """
        self.player_backend.stop()
        self.stream_data.position = StreamTime(0)
        self._save_position()
        self.state = 'stopped'

    def go_to_position(self, time_: StreamTime):
        """
        Transport control method to set the position of a stream to time_.
        Calls on the media-player backend to set the position of a playing stream.
        """
        self.player_backend.set_position(time_=time_)

    def skip_forward_short(self):
        """
        Transport control method 'short skip forward'
        Calls on the media-player backend to skip ahead in a playing stream,
        by an amount equal to self.skip_duration_short.
        """
        self.player_backend.set_position_relative(delta_t=self.skip_duration_short)

    def skip_reverse_short(self):
        """
        Transport control method 'short skip reverse'
        Calls on the media-player backend to skip back in a playing stream,
        by an amount equal to self.skip_duration_short.
        """
        rev_skip_time = self.skip_duration_short.get_time() * -1
        self.player_backend.set_position_relative(delta_t=StreamTime(rev_skip_time))

    def skip_forward_long(self):
        """
        Transport control method 'long skip forward'
        Calls on the media-player backend to skip ahead in a playing stream,
        by an amount equal to self.skip_duration_long.
        """
        self.player_backend.set_position_relative(delta_t=self.skip_duration_long)

    def skip_reverse_long(self):
        """
        Transport control method 'long skip backward'
        Calls on the media-player backend to skip back in a playing stream,
        by an amount equal to self.skip_duration_long.
        """
        rev_skip_time = self.skip_duration_long.get_time() * -1
        self.player_backend.set_position_relative(delta_t=StreamTime(rev_skip_time))


class MetaTask:
    """
    MetaTask acquires a lock when any sub-task is acquired and releases it
    when all sub-tasks have been completed.

    MetaTask emits an 'meta_task_complete' signal when all subtasks are ended.
    It can be subscribed to via MetaTask.transmitter.
    """

    def __init__(self):
        self.transmitter = signal_.Signal()
        self.transmitter.add_signal('meta_task_complete')
        self._meta_task = Lock()
        self._tasks = {}

    def add_subtask(self, task_name: str):
        """
        Add a sub-task to the MetaTask
        """
        if task_name in self._tasks:
            raise ValueError(f'Can\'t add duplicate task: {task_name}')
        self._tasks[task_name] = Lock()

    def begin_subtask(self, subtask_name: str) -> bool:
        """
        Begin a sub-task, which begins a MetaTask if its not already began.

        Returns True if the sub-task was began.
        Returns False if the subtask was already running.
        """
        subtask_began = self._tasks[subtask_name].acquire(blocking=False)
        if subtask_began:
            self._meta_task.acquire(blocking=False)
        return subtask_began

    def subtask_running(self, subtask_name: str) -> bool:
        """
        Get the status of a sub-task.
        """
        return self._tasks[subtask_name].locked()

    def get_running_subtasks(self) -> tuple[str]:
        """
        Return a set of all running subtasks
        """
        return set(task for task in self._tasks if self.subtask_running(task))

    def running(self) -> bool:
        """
        Get the status of the MetaTask.
        """
        return self._meta_task.locked()

    def end_subtask(self, subtask_name: str, abort: bool = False):
        """
        complete a sub-task, which finishes the MetaTask if all sub-tasks have been completed.

        Transmits the 'meta_task_complete' signal if ending the MetaTask.
        """
        self._tasks[subtask_name].release()
        all_sub_tasks_ended = True
        for _, task in self._tasks.items():
            if task.locked():
                all_sub_tasks_ended = False
                break
        if all_sub_tasks_ended:
            self._meta_task.release()
            if not abort:
                self.transmitter.send('meta_task_complete')


class GstPlayerError(Exception):
    """Exeption raised by the GstPlayer class."""


class GstPlayer:
    """The wrapper for the gstreamer backend"""

    def __init__(self):
        Gst.init(None)
        self.playback_state = None
        self.pipeline = None
        self.transmitter = signal_.Signal()
        self.transmitter.add_signal('time_updated', 'stream_ready', 'eos', 'seek_complete')

        self.stream_tasks = MetaTask()
        self.stream_tasks.add_subtask('unload_stream')
        self.stream_tasks.add_subtask('duration_ready')
        self.stream_tasks.add_subtask('start_position_set')
        self.stream_tasks.add_subtask('seek')
        self.stream_tasks.add_subtask('state_change')
        self.stream_tasks.add_subtask('load_stream')
        self.stream_tasks.transmitter.connect('meta_task_complete', self.transmitter.send, 'stream_ready')

    @staticmethod
    def _g_idle_add_once(callback, *cb_args, **g_kwargs):
        """
        Wrap GLib.idle_add() calls with a False return value so the callback only fires once.

          *cb_args: args passed to callback
        **g_kwargs: keyword args that will be passed to GLib.idle_add. ie priority=GLib.PRIORITY_LOW

        """
        def wrap_call_with_false_ret_value(callback, *cb_args):
            # I don't think that any kwargs get passed to the callback by GLib.idle_add
            # so they're not included here.
            callback(*cb_args)
            return False

        # I think that the only kwarg that GLib.idle_add accepts is 'priority'.
        GLib.idle_add(wrap_call_with_false_ret_value, callback, *cb_args, **g_kwargs)

    def load_stream(self, stream_data: StreamData):
        """Load the stream and prepare for playback."""
        if not self.stream_tasks.running():
            self._init_pipeline(stream_data)
            self._init_message_bus()
            self._set_state(state=Gst.State.PAUSED)
            for task in ('duration_ready', 'load_stream', 'start_position_set'):
                self.stream_tasks.begin_subtask(task)
            GLib.idle_add(self._load_stream_controller, stream_data.position)
            return True
        return False

    def unload_stream(self):
        """Cleanup pipeline."""
        if not self.stream_tasks.running() and self._close_pipeline():
            self.stream_tasks.begin_subtask('unload_stream')
            self._g_idle_add_once(self.stream_tasks.end_subtask, 'unload_stream')
            return True
        return False

    def _set_state(self, state: Gst.State, blocking: bool = False) -> bool:
        """
        Change the playback state (play, paused, ready) of the gstreamer pipeline.

        returns True if the state change return is ASYNC or SUCCESS
        returns False if state_change subtask was locked.
        raises GstPlayerError if the state change return is FAILURE or NO_PREROLL.

        If blocking is not set, _set_state() is asynchronous even if Gstreamer
        sets the state synchronously. This is to simplify any methods that call
        _set_state(), allowing them to finish their execution and wait for the
        ready signal. The calling methods don't have to account for both types of
        behavior-- unless explicitly requesting synchronous behavior.

        Note: the 'ready' signal is not called when blocking=True or if an exception is raised.
        """
        if self.stream_tasks.begin_subtask('state_change'):
            state_change_return = self.pipeline.set_state(state=state)

            if state_change_return in (Gst.StateChangeReturn.ASYNC, Gst.StateChangeReturn.SUCCESS):
                if blocking:
                    # get_state() blocks until gstreamer has finished the state change.
                    self.pipeline.get_state(Gst.CLOCK_TIME_NONE)
                    self.stream_tasks.end_subtask('state_change')
                else:
                    # state-changed never gets triggered when new_state==old_state.
                    # End the state_change task anyway.
                    success, cur, pen = self.pipeline.get_state(0)
                    if success and cur == state and pen == Gst.State.VOID_PENDING:
                        self._g_idle_add_once(self.stream_tasks.end_subtask, 'state_change')
                    else:
                        bus = self.pipeline.get_bus()
                        bus.connect("message::state-changed", self._on_state_change_complete, state)
            else:
                # state_change_return == FAILURE, or NO_PREROLL
                self.stream_tasks.end_subtask('state_change', abort=True)
                raise GstPlayerError(f'Failed to set pipeline state to {state}')
            return True
        return False

    def play(self) -> bool:
        """
        Place GstPlayer into the playing state.

        Returns: True if GstPlayer successfuly sets the stream's state to play.
        """
        if not self.stream_tasks.running() and self._set_state(state=Gst.State.PLAYING):
            self.playback_state = 'playing'
            return True
        return False

    def pause(self) -> bool:
        """
        Place GstPlayer into the paused state

        Returns: True if GstPlayer successfuly sets the stream's state to paused.
        """
        if not self.stream_tasks.running() and self._set_state(state=Gst.State.PAUSED):
            self.playback_state = 'paused'
            return True
        return False

    def stop(self):
        """
        Place GstPlayer into the stopped state.
        """
        if not self.stream_tasks.running() \
                and self._set_state(state=Gst.State.PAUSED) \
                and self._set_position(time_=StreamTime(0)):
            self.playback_state = 'stopped'
            return True
        return False

    @staticmethod
    def get_uri_from_path(path: str) -> str:
        """
        Convert a path string to uri.
        Returns path unchanged if it is already a valid uri.
        """
        uri = path
        if not Gst.uri_is_valid(uri):
            uri = Gst.filename_to_uri(path)
        return uri

    def _update_time(self, assigned_pipeline):
        """
        Set self.stream_data.time to the stream's current stream_data.
        """
        if self.pipeline is not assigned_pipeline:
            # returning False stops this from being called again
            return False
        if self.playback_state != 'stopped':
            if not self.stream_tasks.running():
                time_ = self.query_position()
                self._g_idle_add_once(
                    self.transmitter.send, 'time_updated', time_, priority=GLib.PRIORITY_DEFAULT
                )
        # Returning True allows this method to continue being called.
        return True

    def _close_pipeline(self):
        """Cleanup the pipeline"""
        if self.pipeline is None:
            raise GstPlayerError('Pipeline does not exist')
        if self._set_state(state=Gst.State.NULL):
            self.pipeline = None
            return True
        return False

    def _init_message_bus(self):
        """Set up the Gst messages that will be handled"""
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self._on_error)
        bus.connect("message::eos", self._on_eos)
        bus.connect("message::state-changed", self._start_update_time)
        bus.connect("message::duration-changed", self._on_duration_ready)
        # bus.connect("message::application", self.on_application_message)

    def _on_seek_complete(self, bus, _, msg_handle=None):
        """
        Clear the seek subtask and disconnect this callback.
        """
        if msg_handle is not None and msg_handle == '_on_seek_complete':
            bus.disconnect_by_func(self._on_seek_complete)
            self.stream_tasks.end_subtask('seek')

    def _init_pipeline(self, stream_data: StreamData):
        """
        Initialize self.pipeline into a playbin element.
        """
        if self.pipeline is not None:
            raise GstPlayerError('self.pipeline already exists.')
        self.pipeline = Gst.ElementFactory.make("playbin", "playbin")
        # fakevideosink element discards the video portion of the stream
        self.pipeline.set_property(
            'video-sink', Gst.ElementFactory.make("fakevideosink", "video_sink")
        )
        uri = self.get_uri_from_path(stream_data.path)
        self.pipeline.set_property('uri', uri)

    @staticmethod
    def _on_error(_, msg):
        """
        Print an error message.
        """
        err, dbg = msg.parse_error()
        print("ERROR:", msg.src.get_name(), ":", err.message)
        if dbg:
            print("Debug info:", dbg)

    def _on_eos(self, _, __):
        """
        The end of the stream has been reached.
        Start cleanup.
        """
        self._close_pipeline()
        self.playback_state = None
        self.transmitter.send('eos')

    def set_position(self, time_: StreamTime):
        """
        Set the stream to a new playback position.

        Returns False if GstPlayer is busy with another stream task.
        Otherwise it returns the bool value returned from its call to _set_position().

        This method is a wrapper for _set_position that does the following:

            Raises GstPlayerError when the position parameter passed to method
            is not within the range:
            [0, infinity)

            With anything past the end of the stream, Gst.Pipeline.seek_simple() returns True
            and triggers EOS. Hence, there is no upper bound on the range.

            returns True if the seek was successful
            returns False if the seek subtask was locked.
            raises GstPlayerError if seek failed.

            sends the 'ready' signal when a successful seek has completed.
        """
        if not self.stream_tasks.running() and self._set_position(time_):
            return True
        return False

    def _set_position(self, time_: StreamTime) -> bool:
        """
        Attempt to set stream position to time_.

        Raises GstPlayerError when the position parameter passed to method
        is not within the range:
        [0, infinity)

        With anything past the end of the stream, Gst.Pipeline.seek_simple() returns True
        and triggers EOS. Hence, there is no upper bound on the range.

        returns True if the seek was successful
        returns False if the seek subtask was locked.
        raises GstPlayerError if seek failed.

        sends the 'stream_ready' signal when a successful seek has completed.
        """
        if self.stream_tasks.begin_subtask('seek'):
            seek_success = self.pipeline.seek_simple(format=Gst.Format.TIME,
                                                     seek_flags=Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                                     seek_pos=time_.get_time('ns'))
            if seek_success:
                bus = self.pipeline.get_bus()
                bus.connect("message::async-done", self._on_seek_complete, '_on_seek_complete')
            if not seek_success:
                self.stream_tasks.end_subtask('seek', abort=True)
                raise GstPlayerError('Failed to set stream playback position.')
            return True
        return False

    def _start_update_time(self, bus: Gst.Bus, msg: Gst.Message):
        """
        Start the periodic calling of self._update_time once 'self.pipeline' is in the playing state.
        This is a state-changed callback.
        """
        if msg.src == self.pipeline:
            _, new, pending = msg.parse_state_changed()
            if new == Gst.State.PLAYING and pending == Gst.State.VOID_PENDING:
                GLib.timeout_add_seconds(1, self._update_time, self.pipeline)
                bus.disconnect_by_func(self._start_update_time)

    def _on_duration_ready(self, bus: Gst.Bus, _):
        """Simply mark duration_ready subtask as complete."""
        bus.disconnect_by_func(self._on_duration_ready)
        self.stream_tasks.end_subtask('duration_ready')

    def _load_stream_controller(self, start_position: StreamTime) -> bool:
        """
        Manage all of the necessary tasks that GStreamer needs to complete before
        GstPlayer considers the pipeline ready for playback.

        This method is intended to be placed on the GLib.MainLoop by GLib.idle_add
        so that it is called on each iteration of the loop until all tasks are completed.

        Returns:
            True to continue being called by GLib.MainLoop()
            False to stop being called by GLib.MainLoop()
        """
        tasks = self.stream_tasks.get_running_subtasks()

        # wait for stream to enter paused state and then set start position.
        if 'start_position_set' in tasks and 'state_change' not in tasks:
            self._set_position(start_position)
            self.stream_tasks.end_subtask('start_position_set')

        elif {'duration_ready', 'load_stream'} == tasks:
            # Pipeline sometimes needs to be kicked again to free up the duration.
            self._set_position(start_position)

        elif {'load_stream'} == tasks:
            self.stream_tasks.end_subtask('load_stream')
            return False
        return True

    def _on_state_change_complete(self, bus: Gst.Bus, msg: Gst.Message, target_state: Gst.State):
        """
        Clear the lock and disconnect this callback.

        target_state is a user_data parameter supplied by _set_state.
        """
        if msg.src == self.pipeline:
            _, new_state, pen_state = msg.parse_state_changed()
            if new_state == target_state and pen_state == Gst.State.VOID_PENDING:
                bus.disconnect_by_func(self._on_state_change_complete)
                self.stream_tasks.end_subtask('state_change')

    def query_position(self) -> StreamTime:
        """
        Attempt to query the pipeline's position in the stream.

        Returns: current position in StreamTime format

        Raises: GstPlayerError if query_position() fails to retrieve the current position.
        """
        if not self.stream_tasks.running():
            query_success, cur_position = self.pipeline.query_position(Gst.Format.TIME)
            if query_success is True and cur_position is not None:
                return StreamTime(cur_position, 'ns')
        raise GstPlayerError('Failed to query current position.')

    def query_duration(self) -> StreamTime:
        """
        Attempt to query the stream's duration from the pipeline.

        Returns: current duration in Gst time format

        Raises: GstPlayerError if query_duration() fails to retrieve the duration of the current stream.
        """
        query_success, cur_duration = self.pipeline.query_duration(Gst.Format.TIME)
        if query_success:
            return StreamTime(cur_duration, 'ns')
        raise GstPlayerError('Failed to query the current duration.')


class GstPlayerA:
    """
    Adapter to go between Player and GstPlayer.
    Provides queuing services, allowing Player to fire and forget commands to GstPlayer.
    """

    def __init__(self):
        self._gst_player = GstPlayer()
        self._deque = collections.deque()
        self._queued_position = None

        self.transmitter = signal_.Signal()
        self.transmitter.add_signal('stream_loaded')

        self._call_in_progress = False

    def _appendleft(self, command: tuple):
        """
        Wrapper for self._deque.appendleft.
        Adds pop() to the GLib.MainLoop.
        """
        self._deque.appendleft(command)
        if not self._call_in_progress:
            self._call_in_progress = True
            self.pop()

    def load_stream(self, stream_data: StreamData):
        """
        Add a load_stream command to the deque.
        """
        def post_pop():
            self._gst_player.transmitter.connect_once('stream_ready', self.transmitter.send, "stream_loaded")

        self._appendleft((post_pop, self._gst_player.load_stream, stream_data))

    def unload_stream(self):
        """
        Add an unload_stream command to the deque.
        """
        self._deque.clear()
        self._appendleft((lambda: None, self._gst_player.unload_stream))

    def pop(self):
        """
        Remove and execute a command from the deque.

        If the called method returns False, then the command remains in the deque.
        """
        if self._deque:
            try:
                cmd = self._deque.pop()
                # cmd[0]  : Callable    post_pop callback
                # cmd[1]  : Callable    GstPlayer command. These always return False if GstPlayer is busy.
                # cmd[2:] : Any         GstPlayer command args
                if cmd[1](*cmd[2:]):
                    self._gst_player.transmitter.connect_once('stream_ready', self.pop)
                    cmd[0]()
                else:
                    self._deque.append(cmd)

            except GstPlayerError as e:
                print(e)
                self._deque.clear()
            except Exception as e:
                print(e)
                self._deque.clear()
                raise
        else:
            self._call_in_progress = False

    def play(self):
        """
        Add a play command to the deque.
        """
        self._appendleft((lambda: None, self._gst_player.play))

    def pause(self):
        """
        Add a pause command to the deque.
        """
        self._appendleft((lambda: None, self._gst_player.pause))

    def stop(self):
        """
        Add a stop command to the deque.
        """
        self._appendleft((lambda: None, self._gst_player.stop))

    def set_position(self, position: StreamTime):
        """
        Add a set_position command to the deque.
        """
        def post_pop():
            self._queued_position = None

        if self._queued_position is None:
            self._queued_position = (post_pop, self._gst_player.set_position, position)
            self._appendleft(self._queued_position)
        else:
            self._queued_position[2].set_time(position.get_time())

    def query_duration(self) -> StreamTime:
        """
        Query the duration from GstPlayer.
        """
        return self._gst_player.query_duration()

    def query_position(self) -> StreamTime:
        """
        Query the position from GstPlayer.

        Returns the queued position if is exists, or queries the position from GstPlayer.
        """
        if self._queued_position:
            return self._queued_position[2]
        return self._gst_player.query_position()
