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

"""
This module controls the playback of playlists.
"""

from __future__ import annotations
import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar
from typing import Literal
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
        position = StreamData()
        if row is not None:
            position.path = row['path']
            position.position = StreamTime(row['time'])
            position.pl_track_id = row['pl_track_id']
            position.playlist_id = row['playlist_id']
            position.track_number = row['track_number']
            position.mark_saved_position()
        return position

    def get_new_position(self, playlist_id: int, track_number: int, time_: StreamTime) -> StreamData:
        """
        Create a StreamData object set to the beginning of the track_number of the playlist.
        Return an empty StreamData object if nothing was found.
        """
        track_id, pl_track_id = self.get_track_id_pl_track_id_by_number(
            playlist_id=playlist_id,
            track_number=track_number
        )
        if track_id is not None:
            path = self.get_path_by_id(track_id=track_id)

            position = StreamData(
                pl_track_id=pl_track_id,
                track_number=track_number,
                playlist_id=playlist_id,
                path=path,
                position=time_
            )
        else:
            position = StreamData()
        return position

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
        """Get a track's path based on track_id"""
        with audio_book_tables.DB_CONNECTION.query() as con:
            row = self.track.get_row_by_id(con=con, id_=track_id)
            return row['path'] if row is not None else None


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
    _required_attributes: ClassVar[tuple] = ('path', 'position', 'track_number', 'playlist_id', 'pl_track_id')

    # instance attributes
    path: str | None = None
    position: StreamTime | None = None
    duration: StreamTime | None = None
    track_number: int | None = None
    playlist_id: int | None = None
    pl_track_id: int | None = None
    last_saved_position: StreamTime = StreamTime(-1)

    def is_fully_set(self):
        """Check that all required attributes have been set."""
        for item in self.__dict__.items():
            if item[1] is None and item[0] in self._required_attributes:
                return False
        return True

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

    def play(self):
        """
        Transport control method 'play'
        Calls on the media-player backend to play a stream.
        """
        self.player_backend.play()

    def pause(self):
        """
        Transport control method 'pause'
        Calls on the media-player backend to pause a playing stream.
        """
        self.player_backend.pause()
        self.stream_data.position = self.player_backend.query_position()
        self._save_position()

    def stop(self):
        """
        Transport control method 'stop'
        Calls on the media-player backend to stop a playing stream.
        """
        self.player_backend.stop()
        self.stream_data.position = StreamTime(0)
        self._save_position()

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


class GstPlayer:
    """The wrapper for the gstreamer backend"""

    def __init__(self):
        Gst.init(None)
        self.playback_state = None
        self.pipeline = None
        self.transmitter = signal_.Signal()
        self.transmitter.add_signal('time_updated', 'duration_ready', 'eos')

    def load_stream(self, stream_data: StreamData):
        """Set the player position."""
        self._init_pipeline(stream_data)
        self._init_message_bus(stream_data)

    def unload_stream(self):
        """Cleanup pipeline."""
        self._close_pipeline()

    def play(self):
        """
        Place GstPlayer into the playing state
        """
        if self.pipeline.set_state(state=Gst.State.PLAYING) == Gst.StateChangeReturn.FAILURE:
            raise RuntimeError('failed to set pipeline state to Playing')
        self.playback_state = 'playing'

    def pause(self):
        """
        Place GstPlayer into the paused state
        """
        if self.pipeline.set_state(Gst.State.PAUSED) == Gst.StateChangeReturn.FAILURE:
            raise RuntimeError('failed to set playbin state to Paused')
        self.playback_state = 'paused'

    def stop(self):
        """
        Place GstPlayer into the stopped state.
        """
        self.pause()
        self.playback_state = 'stopped'
        self.set_position(time_=StreamTime(0))

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
            time_ = self.query_position()
            GLib.idle_add(self.transmitter.send, 'time_updated', time_, priority=GLib.PRIORITY_DEFAULT)
        # Returning True allows this method to continue being called.
        return True

    def _close_pipeline(self):
        """Cleanup the pipeline"""
        if self.pipeline is None:
            raise RuntimeError('Pipeline does not exist')
        self.pipeline.set_state(state=Gst.State.NULL)
        self.pipeline = None

    def _init_message_bus(self, stream_data: StreamData):
        """Set up the Gst messages that will be handled"""
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self._on_error)
        bus.connect("message::eos", self._on_eos)
        bus.connect("message::state-changed", self._init_start_position, stream_data.position)
        bus.connect("message::state-changed", self._start_update_time)
        bus.connect("message::duration-changed", self._on_duration_ready)
        # bus.connect("message::application", self.on_application_message)

    def _init_pipeline(self, stream_data: StreamData):
        if self.pipeline is not None:
            raise RuntimeError('self.pipeline already exists.')
        self.pipeline = Gst.ElementFactory.make("playbin", "playbin")
        # fakevideosink element discards the video portion of the stream
        self.pipeline.set_property(
            'video-sink', Gst.ElementFactory.make("fakevideosink", "video_sink")
        )
        uri = self.get_uri_from_path(stream_data.path)
        self.pipeline.set_property('uri', uri)
        if self.pipeline.set_state(Gst.State.READY) == Gst.StateChangeReturn.FAILURE:
            raise RuntimeError('failed to set playbin state to Ready')

    @staticmethod
    def _on_error(_, msg):
        err, dbg = msg.parse_error()
        print("ERROR:", msg.src.get_name(), ":", err.message)
        if dbg:
            print("Debug info:", dbg)

    def _on_eos(self, _, __):
        """
        The end of the stream has been reached.
        Start cleanup.
        """
        self.stop()
        self._close_pipeline()
        self.transmitter.send('eos')

    def set_position_relative(self, delta_t: StreamTime):
        """
        Set stream position to current position + delta_t.

        Normalize the new position to values acceptable to self.set_position()
        """
        cur_position = self.query_position()
        new_position = cur_position.get_time() + delta_t.get_time()
        # ensure new_position in valid range
        new_position = max(new_position, 0)
        self.set_position(time_=StreamTime(new_position))

    def set_position(self, time_: StreamTime):
        """
        Attempt to set stream position to time_.

        Raises RuntimeError when the position parameter passed to method
        is not within the range:
        [0, infinity)

        With anything past the end of the stream, Gst.Pipeline.seek_simple() returns True
        and triggers EOS. Hence, there is no upper bound on the range.
        """
        seek_success = self.pipeline.seek_simple(format=Gst.Format.TIME,
                                                 seek_flags=Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                                 seek_pos=time_.get_time('ns'))
        if not seek_success:
            raise RuntimeError('Failed to set stream playback position.')

    def _start_update_time(self, bus: Gst.Bus, msg: Gst.Message):
        """
        Start the periodic calling of self._update_time once 'self.pipeline' is in the playing state.
        This is a state-changed callback.
        """
        if msg.src == self.pipeline:
            old, new, pending = msg.parse_state_changed()  # pylint: disable=unused-variable
            if new == Gst.State.PLAYING and pending == Gst.State.VOID_PENDING:
                GLib.timeout_add_seconds(1, self._update_time, self.pipeline)
                bus.disconnect_by_func(self._start_update_time)

    def _on_duration_ready(self, bus: Gst.Bus, _: Gst.Message):
        bus.disconnect_by_func(self._on_duration_ready)
        duration = self.query_duration()
        self.transmitter.send('duration_ready', duration=duration)

    def _init_start_position(self, bus: Gst.Bus, msg: Gst.Message, time_: StreamTime):
        """
        Set playback position to the time saved in self.stream_data or the start of the stream.
        This is a state-changed callback.
        """
        if msg.src == self.pipeline:
            old, new, pen = msg.parse_state_changed()
            if old == Gst.State.READY and new == Gst.State.PAUSED and pen == Gst.State.PLAYING:
                self.set_position(time_=time_)
                # This only needs to be done once per stream. Disconnect this callback.
                bus.disconnect_by_func(self._init_start_position)

    def query_position(self) -> StreamTime:
        """
        Attempt to query the pipeline's position in the stream.

        Returns: current position in StreamTime format

        Raises: RuntimeError if query_position() fails to retrieve the current position.
        """
        query_success, cur_position = self.pipeline.query_position(Gst.Format.TIME)
        if query_success:
            return StreamTime(cur_position, 'ns')
        raise RuntimeError('Failed to query current position.')

    def query_duration(self) -> StreamTime:
        """
        Attempt to query the stream's duration from the pipeline.

        Returns: current duration in Gst time format

        Raises: RuntimeError if query_duration() fails to retrieve the duration of the current stream.
        """
        query_success, cur_duration = self.pipeline.query_duration(Gst.Format.TIME)
        if query_success:
            return StreamTime(cur_duration, 'ns')
        raise RuntimeError('Failed to query the current duration.')
