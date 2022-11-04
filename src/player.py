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

    def get_saved_position(self, playlist_id: int) -> StreamData:
        """Get the playlist's saved position."""
        with audio_book_tables.DB_CONNECTION.query() as con:
            row = self.player_position_joined.get_row_by_playlist_id(con=con, playlist_id=playlist_id)
        position = StreamData()
        if row is not None:
            position.path = row['path']
            position.time = StreamTime(row['time'])
            position.pl_track_id = row['pl_track_id']
            position.playlist_id = row['playlist_id']
            position.track_number = row['track_number']
        return position

    def get_new_position(self, playlist_id: int, track_number: int, time_: StreamTime) -> StreamData:
        """
        Create a StreamData object set to the beginning of the track_number of the playlist.
        """
        track_id, pl_track_id = self.get_track_id_pl_track_id_by_number(
            playlist_id=playlist_id,
            track_number=track_number
        )
        path = self.get_path_by_id(track_id=track_id)

        position = StreamData(
            pl_track_id=pl_track_id,
            track_number=track_number,
            playlist_id=playlist_id,
            path=path,
            time=time_
        )
        return position

    def save_position(self, pl_track_id: int, playlist_id: int, time_: int):
        """Save player position to the database."""
        with audio_book_tables.DB_CONNECTION.query() as con:
            self.player_position.upsert_row(
                con=con,
                pl_track_id=pl_track_id,
                playlist_id=playlist_id,
                time=time_
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

    def __init__(self, time_: int | float = 0, unit: str = 'ns'):
        self._time = None
        self.set_time(time_=time_, unit=unit)

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
    _required_attributes: ClassVar[tuple] = ('path', 'time', 'track_number', 'playlist_id', 'pl_track_id')

    # instance attributes
    path: str | None = None
    time: StreamTime | None = None
    duration: StreamTime | None = None
    track_number: int | None = None
    playlist_id: int | None = None
    pl_track_id: int | None = None

    def is_fully_set(self):
        """Check that all required attributes have been set."""
        for item in self.__dict__.items():
            if item[1] is None and item[0] in self._required_attributes:
                return False
        return True


class Player:
    """The model class for the media player backend"""

    def __init__(self):
        self.player_dbi = PlayerDBI()
        self.gst_player = GstPlayer()
        self.position = None
        self.skip_duration_short = 3
        self.skip_duration_long = 30

    def load_playlist(self, playlist_data: book.PlaylistData):
        """
        Load self.stream_data with a StreamData from the database if it exists, or set it to a newly created one that
        starts at the beginning of the first track in the playlist.

        Raises: RuntimeError if load_playlist() fails to generate a completely instantiated StreamData object.
        """
        playlist_id = playlist_data.get_id()
        position = self.player_dbi.get_saved_position(playlist_id=playlist_id)
        if not position.is_fully_set():
            position = self.player_dbi.get_new_position(playlist_id=playlist_id, track_number=0, time_=StreamTime(0))

        if position.is_fully_set():
            self.gst_player.load_stream(stream_data=position)
        else:
            raise RuntimeError('Failed to load playlist stream_data ', position)

    def play(self):
        """
        Transport control method 'play'
        Calls on the media-player backend to play a stream.
        """
        self.gst_player.play()

    def pause(self):
        """
        Transport control method 'pause'
        Calls on the media-player backend to pause a playing stream.
        """
        self.gst_player.pause()

    def stop(self):
        """
        Transport control method 'stop'
        Calls on the media-player backend to stop a playing stream.
        """
        self.gst_player.stop()

    def go_to_position(self, t_seconds: int):
        """
        Transport control method to set the position of a stream to t_seconds.
        Calls on the media-player backend to set the position of a playing stream.
        """
        self.gst_player.set_position(t_seconds=t_seconds)

    def skip_forward_short(self):
        """
        Transport control method 'short skip forward'
        Calls on the media-player backend to skip ahead in a playing stream,
        by an amount equal to self.skip_duration_short.
        """
        self.gst_player.set_position_relative(delta_t_seconds=self.skip_duration_short)

    def skip_reverse_short(self):
        """
        Transport control method 'short skip reverse'
        Calls on the media-player backend to skip back in a playing stream,
        by an amount equal to self.skip_duration_short.
        """
        self.gst_player.set_position_relative(delta_t_seconds=self.skip_duration_short * -1)

    def skip_forward_long(self):
        """
        Transport control method 'long skip forward'
        Calls on the media-player backend to skip ahead in a playing stream,
        by an amount equal to self.skip_duration_long.
        """
        self.gst_player.set_position_relative(delta_t_seconds=self.skip_duration_long)

    def skip_reverse_long(self):
        """
        Transport control method 'long skip backward'
        Calls on the media-player backend to skip back in a playing stream,
        by an amount equal to self.skip_duration_long.
        """
        self.gst_player.set_position_relative(delta_t_seconds=self.skip_duration_long * -1)


class GstPlayer:
    """The wrapper for the gstreamer backend"""
    # pylint: disable=unused-argument
    # disabled because GStreamer callbacks automatically supply args that are unused.

    def __init__(self):
        Gst.init(None)
        self.playback_state = None
        self.position = None
        self.pipeline = None
        self.duration = Gst.CLOCK_TIME_NONE
        self.transmitter = signal_.Signal()
        self.transmitter.add_signal('time_updated', 'duration_ready', 'eos')

    def load_stream(self, position: StreamData):
        """Set the player position."""
        if self.position is not None:
            raise RuntimeError('GstPlayer.position is not None')
        self.position = position
        self._init_pipeline()
        self._init_message_bus()

    def pop_position_data(self):
        """remove and return player position."""
        self._close_pipeline()
        if self.position is not None:
            pos = self.position
            self.position = None
            return pos
        raise RuntimeError('GstPlayer.position is None')

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
        self.set_position(t_seconds=0)
        self.position.time = 0

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

    def _update_time(self):
        """
        Set self.position.time to the stream's current position.
        """
        # pylint: disable=lost-exception
        # Disabled because swallowing the exception is exactly the behavior needed.
        # It should output an error message, and then return True so that the callback
        # gets called again later.
        if self.pipeline is None:
            # returning False stops this from being called again
            return False
        if self.playback_state == 'stopped':
            return True
        try:
            cur_time = self._query_position()
            self.position.time = int(cur_time / Gst.SECOND)
        finally:
            return True

    def _close_pipeline(self):
        """Cleanup the pipeline"""
        if self.pipeline is None:
            raise RuntimeError('Pipeline does not exist')
        self.pipeline.set_state(state=Gst.State.NULL)
        self.pipeline = None

    def _init_message_bus(self):
        """Set up the Gst messages that will be handled"""
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self._on_error)
        bus.connect("message::eos", self._on_eos)
        bus.connect("message::state-changed", self._init_attributes_that_can_only_be_set_after_playback_started)
        bus.connect("message::state-changed", self._start_update_time)
        bus.connect("message::duration-changed", self._init_duration)
        # bus.connect("message::application", self.on_application_message)

    def _init_pipeline(self):
        if self.pipeline is not None:
            raise RuntimeError('self.pipeline already exists.')
        self.pipeline = Gst.ElementFactory.make("playbin", "playbin")
        # fakevideosink element discards the video portion of the stream
        self.pipeline.set_property(
            'video-sink', Gst.ElementFactory.make("fakevideosink", "video_sink")
        )
        uri = self.get_uri_from_path(self.position.path)
        self.pipeline.set_property('uri', uri)
        if self.pipeline.set_state(Gst.State.READY) == Gst.StateChangeReturn.FAILURE:
            raise RuntimeError('failed to set playbin state to Ready')

    @staticmethod
    def _on_error(bus, msg):
        err, dbg = msg.parse_error()
        print("ERROR:", msg.src.get_name(), ":", err.message)
        if dbg:
            print("Debug info:", dbg)

    def _on_eos(self, bus, msg):
        """
        The end of the stream has been reached.
        Start cleanup.
        """
        self.stop()
        self._close_pipeline()
        self.transmitter.send('eos')

    def set_position_relative(self, delta_t_seconds: int):
        """
        Set stream position to current position + delta_t_seconds.

        Normalize the new position to values acceptable to self.set_position()
        """
        cur_position = self._query_position()
        new_position = (cur_position / Gst.SECOND) + delta_t_seconds
        # ensure new_position in valid range
        new_position = max(new_position, 0)
        self.set_position(t_seconds=new_position)

    def set_position(self, t_seconds: int | float):
        """
        Attempt to set stream position to t_seconds.

        Raises RuntimeError when the position parameter passed to method
        is not within the range:
        (0, infinity]

        With anything past the end of the stream, Gst.Pipeline.seek_simple() returns True
        and triggers EOS. Hence, there is no upper bound on the range.
        """
        seek_success = self.pipeline.seek_simple(format=Gst.Format.TIME,
                                                 seek_flags=Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                                 seek_pos=int(t_seconds * Gst.SECOND))
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
                GLib.timeout_add_seconds(1, self._update_time)
                bus.disconnect_by_func(self._start_update_time)

    def _init_start_position(self):
        """
        Set playback position to the time saved in self.position or the start of the stream.
        This is a state-changed callback.
        """
        if not self.set_position(t_seconds=self.position.time):
            print('Failed to set start position of stream')

    def _init_duration(self, bus: Gst.Bus, _: Gst.Message):
        bus.disconnect_by_func(self._init_duration)
        self.duration = self._query_duration()
        self.transmitter.send('duration_ready')

    def _init_attributes_that_can_only_be_set_after_playback_started(self, bus: Gst.Bus, msg: Gst.Message):
        """
        Set instance attributes that can only be set after gstreamer has entered the playing state.
        This is a state-changed callback.
        """
        if msg.src == self.pipeline:
            old, new, pen = msg.parse_state_changed()
            if old == Gst.State.READY and new == Gst.State.PAUSED and pen == Gst.State.PLAYING:
                self._init_start_position()
                # This only needs to be done once per stream. Disconnect this callback.
                bus.disconnect_by_func(self._init_attributes_that_can_only_be_set_after_playback_started)

    def _query_position(self) -> int:
        """
        Attempt to query the pipeline's position in the stream.

        Returns: current position in Gst time format

        Raises: RuntimeError if query_position() fails to retrieve the current position.
        """
        query_success, cur_position = self.pipeline.query_position(Gst.Format.TIME)
        if query_success:
            return cur_position
        raise RuntimeError('Failed to query current position.')

    def _query_duration(self) -> int:
        """
        Attempt to query the stream's duration from the pipeline.

        Returns: current duration in Gst time format

        Raises: RuntimeError if _query_duration() fails to retrieve the duration of the current stream.
        """
        query_success, cur_duration = self.pipeline.query_duration(Gst.Format.TIME)
        if query_success:
            return cur_duration
        raise RuntimeError('Failed to query the current duration.')
