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
# pylint: disable=abstract-method
# disabled because the locks need to be released outside the context of where they're acquired.
#

"""
This module controls the playback of playlists.
"""

from __future__ import annotations
import pathlib
import logging
from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar
from typing import Literal
import collections
import gi
gi.require_version('Gst', '1.0')
# gi.require_version('Gtk', '3.0')
# gi.require_version('GdkX11', '3.0')
# gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, GLib
from lock_wrapper import Lock
import audio_book_tables
import signal_
import book
from book_reader import BookReader
from gui.gtk import player_view
if TYPE_CHECKING:
    from pathlib import Path
    gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
    from gi.repository import Gtk


class PlayerDBI:
    """Class to interface the Player class with the database."""

    def __init__(self):
        self.player_position = audio_book_tables.PlayerPosition
        with audio_book_tables.DB_CONNECTION.query() as con:
            self.player_position.init_table(con)

    def get_position(self, playlist_id: int) -> PositionData | None:
        """Get the playlist's saved position."""
        with audio_book_tables.DB_CONNECTION.query() as con:
            row = self.player_position.get_row_by_playlist_id(con, playlist_id)

        position = None
        if row is not None:
            position = PositionData()
            position.time = StreamTime(row['time'])
            position.pl_track_id = row['pl_track_id']
            position.playlist_id = row['playlist_id']
        return position

    def save_position(self, position_data: PositionData) -> None:
        """Save player position to the database."""
        print('#################3 saving')
        with audio_book_tables.DB_CONNECTION.query() as con:
            self.player_position.upsert_row(
                con=con,
                pl_track_id=position_data.pl_track_id,
                playlist_id=position_data.playlist_id,
                time=position_data.time.get_time()
            )


class StreamTime:
    """
    Wrapper for storing time values in StreamData.
    Provides unit conversion functionality.
    """

    # Base unit for time storage is nanoseconds.
    # The units must be in ascending order of significance for the
    # get_clock_value() method to operate correctly.
    _time_conversions: ClassVar[dict] = {
        'ns': 1,
        'ms': pow(10, 6),
        's': pow(10, 9),
        'm': pow(10, 9) * 60,
        'h': pow(10, 9) * 60 * 60
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

    def _get_next_larger_time_unit(self, unit) -> str:
        """
        Get the next larger unit in the time_conversions dict.
        """
        found_current_unit = False
        next_unit = None
        for unit_key in self._time_conversions:
            if found_current_unit:
                next_unit = unit_key
                break
            if unit_key == unit:
                found_current_unit = True
        return next_unit

    def get_clock_value(self, unit: str = 'ns') -> int:
        """
        Get the stored time in the desired units, truncated to a whole number
        representing the remainder after stripping all values of larger units
        from the StreamTime's stored time.

        Returns: The stored time in the desired units

        Ex:
        * StreamTime(200, 's').get_clock_value('ms') == 0 is True
        * StreamTime(200, 's').get_clock_value('s') == 20 is True
        * StreamTime(200, 's').get_clock_value('m') == 3 is True
        * StreamTime(200, 's').get_clock_value('h') == 0 is True
        """
        next_unit = self._get_next_larger_time_unit(unit)
        if next_unit is None:
            return self.get_time(unit)

        next_larger_time = StreamTime(self.get_time(next_unit), next_unit)
        return (self - next_larger_time).get_time(unit)

    def get_time(self, unit: str = 'ns'):
        """
        Get the stored time in the desired units, truncated to a whole number.

        param: unit time unit of the return value
        """
        return int(self._time / self._time_conversions[unit])

    def set_time(self, time_: int | float, unit: str = 'ns'):
        """
        Set the stored time in units, truncated to a whole number.
        """
        self._time = int(time_ * self._time_conversions[unit])


@dataclass
class PositionData:
    """Container for a playlist's position information"""

    time: StreamTime | None = None
    playlist_id: int | None = None
    pl_track_id: int | None = None


@dataclass
class StreamData:
    """Container for stream data."""

    path: str | None = None
    duration: StreamTime | None = None
    track_number: int | None = None
    last_saved_position: StreamTime = StreamTime(-1)
    position_data: PositionData | None = None
    stream_info: str | None = None

    def mark_saved_position(self):
        """
        Record what the time was when the position was last saved to the database.
        """
        self.last_saved_position.set_time(self.position_data.time.get_time())


class SeekTime(Enum):
    """Enum containing relative seek times"""
    FORWARD_LONG = StreamTime(30, 's')
    FORWARD_SHORT = StreamTime(5, 's')
    REVERSE_LONG = StreamTime(-30, 's')
    REVERSE_SHORT = StreamTime(-5, 's')


class Player:  # pylint: disable=unused-argument
    """The base class for the media player model."""

    logger = logging.getLogger(f'{__name__}.PlayerState')

    def __init__(self):
        self.player_dbi = PlayerDBI()
        self.track_dbi = book.TrackDBI()
        self.playlist_dbi = book.PlaylistDBI()

        self.player_adapter = GstPlayerA()
        self.player_adapter.transmitter.connect('time_updated', self._on_time_updated)
        self.player_adapter.transmitter.connect('stream_loaded', self._on_stream_loaded)
        self.player_adapter.transmitter.connect('eos', self._on_eos)

        self.stream_data = StreamData()
        self.book_data = book.BookData(book.PlaylistData())

        self.transmitter = signal_.Signal()
        self.transmitter.add_signal('stream_updated',
                                    'position_updated',
                                    'playlist_finished',
                                    'playlist_loaded',
                                    'playlist_unloaded',
                                    'player_enter_state')

        # Set the initial state to Player.
        self._set_state(PlayerStateInitial)

    def state_entry(self) -> None:
        """Initialize a state."""
        self._state_entry()

    def _set_state(self, player_state: Player) -> None:
        """
        Set state
        player_state: State class that implements PlayerState.
        """
        self.__class__ = player_state
        self.state_entry()

    def get_state(self) -> type[Player]:
        """
        Get the Player's state.
        returns the PlayerState class that has inherited Player.
        """
        return self.__class__

    def load_playlist(self, playlist_data: book.PlaylistData) -> None:
        """
        Load self.stream_data with a StreamData from the database if it exists, or set it to a newly created one that
        starts at the beginning of the first track in the playlist.

        Note: PlayerState's should implement this by calling _load_playlist().
        """
        self.logger.warning('calling load_playlist() not implemented in this state, %s.', self.__class__.__name__)

    def set_track(self, track_number: int) -> None:
        """
        Set the current track to track_number.

        Raises: RuntimeError if set_track() fails to generate a completely instantiated StreamData object.

        Note: PlayerState's should call _set_track().
        """
        self.logger.warning('calling set_track() not implemented in this state, %s.', self.__class__.__name__)

    def set_track_relative(self, track_delta: Literal[-1, 1]) -> None:
        """
        Skip a number of tracks based on the value of track_delta.

        Note: PlayerState's should call _set_track_relative().
        """
        self.logger.warning('calling set_track_relative() not implemented in this state, %s.', self.__class__.__name__)

    def unload_playlist(self) -> None:
        """
        Remove all references to the currently loaded playlist.

        Note: PlayerState's should call _unload_playlist().
        """
        self.logger.warning('calling unload_playlist() not implemented in this state, %s.', self.__class__.__name__)

    def play(self) -> None:
        """
        Play a stream.

        Note: PlayerState's should implement this.
        """
        self.logger.warning('method play() not implemented in this state, %s.', self.__class__.__name__)

    def pause(self) -> None:
        """
        Pause a playing stream.

        Note: PlayerState's should implement this.
        """
        self.logger.warning('calling pause() not implemented in this state, %s.', self.__class__.__name__)

    def stop(self) -> None:
        """
        Stop a playing or paused stream.
        While playing, stop() pauses the track.
        While paused, stop() resets the streams position to the beginning of the track.

        Note: PlayerState's should implement this.
        """
        self.logger.warning('calling stop() not implemented in this state, %s.', self.__class__.__name__)

    def go_to_position(self, time_: StreamTime) -> bool:
        """
        Transport control method to set the position of a stream to time_.
        Calls on the media-player backend to set the position of a playing stream.

        return: False if the new position is past the end or beginning of a track.

        Note: PlayerState's should implement this by calling _go_to_position().
        """
        self.logger.warning('calling go_to_position() not implemented in this state, %s.', self.__class__.__name__)
        return False

    def seek(self, time_delta: SeekTime) -> None:
        """
        Seek forward or backward in a track by an amount equal to time_delta.

        time_delta: The amount of time to skip forwad or backward in a track.
        returns: False if the new position is past the end or beginning of a track.

        Note: This method checks first with the player adapter for the most up to date position,
        including any pending position changes that may be in the queue.

        Note: PlayerState's should implement this by calling _seek().
        """
        self.logger.warning('calling seek() not implemented in this state, %s', self.__class__.__name__)

    def activate(self) -> None:
        """Only used by PlayerStateInitial"""
        raise NotImplementedError

    def _load_playlist(self, playlist_data: book.PlaylistData) -> None:
        """Implementation for self.load_playlist"""
        self.logger.warning('_load_playlist class %s', self.__class__)

        new_playlist_data = self.playlist_dbi.get_by_id(playlist_data.get_id())
        if new_playlist_data is None:
            raise RuntimeError('Failed to load playlist')

        new_book_data = book.BookData(new_playlist_data)
        new_book_data.track_list = self.track_dbi.get_track_list_by_pl_id(playlist_data.get_id())
        if not new_book_data.track_list:
            raise RuntimeError('track_list is empty, failed to build StreamData object to load the stream.')
        new_book_data.sort_track_list_by_number()

        position_data = self.player_dbi.get_position(playlist_data.get_id())
        if position_data is None:
            position_data = PositionData()
            position_data.time = StreamTime(0)
            position_data.playlist_id = playlist_data.get_id()
            pl_track_id = new_book_data.get_track_by_track_number(0).get_pl_track_id()
            position_data.pl_track_id = pl_track_id

        current_track = new_book_data.get_track_by_pl_track_id(position_data.pl_track_id)

        self.stream_data.path = current_track.get_file_path()
        self.stream_data.position_data = position_data
        self.stream_data.track_number = current_track.get_number()
        self.book_data = new_book_data
        self.transmitter.send('playlist_loaded', self.book_data)

    def _set_track(self, track_number: int) -> None:
        """Implementation for self.set_track"""
        track = self.book_data.get_track_by_track_number(track_number)

        position_data = PositionData()
        position_data.time = StreamTime(0)
        position_data.playlist_id = self.book_data.playlist_data.get_id()
        position_data.pl_track_id = track.get_pl_track_id()

        new_stream_data = StreamData()
        new_stream_data.path = track.get_file_path()
        new_stream_data.position_data = position_data
        new_stream_data.track_number = track.get_number()

        self.stream_data = new_stream_data

    def _set_track_relative(self, track_delta: Literal[-1, 1]):
        """Implementation for self.set_track_relative"""
        new_track_number = self._get_incremented_track_number(track_delta)
        self._set_track(track_number=new_track_number)

    def _unload_playlist(self) -> None:
        """Implementation for self.unload_playlist"""
        self.stream_data = StreamData()
        self.transmitter.send('playlist_unloaded')

    def _on_eos(self) -> None:
        """
        The media player backend has reached the end of the stream.
        """
        old_track_num = self.stream_data.track_number
        self.set_track_relative(1)
        if old_track_num >= self.stream_data.track_number:
            self.transmitter.send('playlist_finished')

    def _get_incremented_track_number(self, track_delta: Literal[-1, 1]):
        """
        Get a new track number by incrementing the value of self.stream_data.track_number by track_delta,
        providing wrap-around functionality.

        This does not increment self.stream_data.track_number itself.
        """
        track_count = self.book_data.get_n_tracks()
        new_track_number = self.stream_data.track_number + track_delta
        if new_track_number >= track_count:
            new_track_number = 0
        elif new_track_number < 0:
            new_track_number = track_count - 1
        return new_track_number

    def _on_stream_loaded(self) -> None:
        """
        The media player backend adapter has signaled that the stream is fully loaded.
        """
        self.logger.debug('_on_stream_loaded')
        self.stream_data.duration = self.player_adapter.query_duration()
        self.transmitter.send('stream_updated')

    def _on_time_updated(self, position: StreamTime) -> None:
        """
        The media player backend has updated the playback position.
        """
        self.logger.debug('_on_time_updated')
        self.stream_data.position_data.time = position
        self.transmitter.send('position_updated', position)
        # Save position when 30 seconds elapsed.
        if position.get_time('s') - self.stream_data.last_saved_position.get_time('s') > 29:
            self._save_position()

    def _save_position(self) -> None:
        self.player_dbi.save_position(self.stream_data.position_data)
        self.stream_data.mark_saved_position()

    def _go_to_position(self, time_: StreamTime) -> bool:
        """Implementation for self.go_to_position"""
        if(time_ > StreamTime(0) and time_ < self.stream_data.duration):
            self.player_adapter.set_position(position=time_)
            return True
        else:
            return False

    def _seek(self, time_delta: SeekTime) -> bool:
        """Implementation for self.seek"""
        if (position := self.player_adapter.query_position()) is not None:
            position += time_delta.value
        else:
            position = self.stream_data.position_data.time + time_delta.value

        return self._go_to_position(time_=position)

    def _state_entry(self) -> None:
        """Implementation for self.state_entry"""
        self.transmitter.send('player_enter_state', self.__class__)


class PlayerStateInitial(Player):
    """The initial state for the Player model."""

    def activate(self) -> None:
        self._set_state(PlayerStateNoPlaylistLoaded)


class PlayerStateNoPlaylistLoaded(Player):
    """Player State PlayerStateNoPlaylistLoaded"""

    def load_playlist(self, playlist_data: book.PlaylistData) -> None:
        self.logger.warning('PlayerStateNoPlaylistLoaded load_playlist')
        self._load_playlist(playlist_data)
        self.player_adapter.load_stream(self.stream_data)
        self._set_state(PlayerStatePaused)


class  PlayerStatePlaying(Player):
    """Player State PlayerStatePlaying"""

    def load_playlist(self, playlist_data: book.PlaylistData) -> None:
        self.player_adapter.unload_stream()
        self._unload_playlist()
        self._load_playlist(playlist_data)
        self.player_adapter.load_stream(stream_data=self.stream_data)
        self._set_state(PlayerStatePaused)

    def set_track(self, track_number: int) -> None:
        self.player_adapter.unload_stream()
        self._set_track(track_number)
        self.player_adapter.load_stream(self.stream_data)
        self.player_adapter.play()

    def set_track_relative(self, track_delta: Literal[-1, 1]) -> None:
        self.player_adapter.unload_stream()
        self._set_track_relative(track_delta)
        self.player_adapter.load_stream(self.stream_data)
        self.player_adapter.play()

    def unload_playlist(self) -> None:
        self.player_adapter.unload_stream()
        self._unload_playlist()
        self._set_state(PlayerStateNoPlaylistLoaded)

    def pause(self) -> None:
        self.player_adapter.pause()
        self._set_state(PlayerStatePaused)

    def stop(self) -> None:
        self.player_adapter.pause()
        self._set_state(PlayerStatePaused)

    def seek(self, time_delta: SeekTime) -> None:
        self._seek(time_delta)

    def go_to_position(self, time_: StreamTime) -> bool:
        return self._go_to_position(time_)


class  PlayerStatePaused(Player):
    """Player State PlayerStatePaused"""

    def load_playlist(self, playlist_data: book.PlaylistData) -> None:
        self.player_adapter.unload_stream()
        self._unload_playlist()
        self._load_playlist(playlist_data)
        self.player_adapter.load_stream(self.stream_data)

    def set_track(self, track_number: int) -> None:
        self.player_adapter.unload_stream()
        self._set_track(track_number)
        self.player_adapter.load_stream(self.stream_data)

    def set_track_relative(self, track_delta: Literal[-1, 1]) -> None:
        self.player_adapter.unload_stream()
        self._set_track_relative(track_delta)
        self.player_adapter.load_stream(self.stream_data)

    def unload_playlist(self) -> None:
        self.player_adapter.unload_stream()
        self._unload_playlist()
        self._set_state(PlayerStateNoPlaylistLoaded)

    def play(self) -> None:
        self.player_adapter.play()
        self._set_state(PlayerStatePlaying)

    def stop(self) -> None:
        self.player_adapter.set_position(StreamTime(0))

    def seek(self, time_delta: SeekTime) -> None:
        self._seek(time_delta)

    def go_to_position(self, time_: StreamTime) -> bool:
        return self._go_to_position(time_)


class PlayerC:
    """
    PlayerC routes the various signals between Player and the various player control widgits
    as well as come commands that come from Book_Reader.
    """
    logger = logging.getLogger(f'{__name__}.PlayerC')

    def __init__(self, book_reader: BookReader, builder: Gtk.Builder):
        self.book_reader = book_reader
        self.transmitter = signal_.Signal()
        self.transmitter.add_signal('activate',
                                    'deactivate',
                                    'stream_updated',
                                    'playlist_loaded',
                                    'playlist_unloaded',
                                    'position_updated',
                                    'player_enter_state')

        self.component_transmitter = signal_.Signal()
        self.component_transmitter.add_signal('next',
                                              'play',
                                              'pause',
                                              'previous',
                                              'skip_forward_long',
                                              'skip_reverse_long',
                                              'go_to_position',
                                              'stop')

        self.component_transmitter.connect('play', self.on_play)
        self.component_transmitter.connect('pause', self.on_pause)
        self.component_transmitter.connect('next', self.on_next)
        self.component_transmitter.connect('previous', self.on_previous)
        self.component_transmitter.connect('skip_forward_long', self.on_skip_forward_long)
        self.component_transmitter.connect('skip_reverse_long', self.on_skip_reverse_long)
        self.component_transmitter.connect('stop', self.on_stop)

        self.player_button_next = player_view.PlayerButtonNextVC(
            component_transmitter=self.component_transmitter,
            controller_transmitter=self.transmitter,
            builder=builder
        )
        self.player_button_previous = player_view.PlayerButtonPreviousVC(
            component_transmitter=self.component_transmitter,
            controller_transmitter=self.transmitter,
            builder=builder
        )
        self.player_button_play_pause = player_view.PlayerButtonPlayPauseVC(
            component_transmitter=self.component_transmitter,
            controller_transmitter=self.transmitter,
            builder=builder
        )
        self.player_button_forward = player_view.PlayerButtonForwardVC(
            component_transmitter=self.component_transmitter,
            controller_transmitter=self.transmitter,
            builder=builder
        )
        self.player_button_rewind = player_view.PlayerButtonRewindVC(
            component_transmitter=self.component_transmitter,
            controller_transmitter=self.transmitter,
            builder=builder
        )
        self.player_position_display = player_view.PlayerPositionDisplayVC(
            component_transmitter=self.component_transmitter,
            controller_transmitter=self.transmitter,
            builder=builder
        )
        self.player_button_stop = player_view.PlayerButtonStopVC(
            component_transmitter=self.component_transmitter,
            controller_transmitter=self.transmitter,
            builder=builder
        )

        self.player = Player()
        self.player.transmitter.connect('stream_updated', self.on_stream_updated)
        self.player.transmitter.connect('position_updated', self.on_position_updated)
        self.player.transmitter.connect('playlist_finished', self.on_playlist_finished)
        self.player.transmitter.connect('player_enter_state', self.transmitter.send, 'player_enter_state')
        self.player.transmitter.connect('playlist_loaded', self.transmitter.send, 'playlist_loaded')
        self.player.transmitter.connect('playlist_unloaded', self.transmitter.send, 'playlist_unloaded')
        self.player.activate()
        self.book_reader.transmitter.connect('book_opened', self.on_book_opened)
        self.book_reader.transmitter.connect('book_closed', self.on_book_closed)

        self.component_transmitter.connect('go_to_position', self.component_receiver, pass_sig_data_to_cb=True)

    def component_receiver(self, *args, sig_data) -> None:
        """
        Handle signals originating from one of the player control components. eg play button
        """
        match sig_data.handle:

            case 'go_to_position':
                new_position = StreamTime(args[0], 's')
                self.player.go_to_position(new_position)

    def on_stop(self) -> None:
        """
        callback that stops a playlist from playing
        """
        self.player.stop()

    def on_stream_updated(self) -> None:
        """
        Relay the signal 'stream_updated'
        """
        self.transmitter.send('stream_updated', self.player.stream_data)

    def on_position_updated(self, position: StreamTime) -> None:
        """
        Relay the signal 'position_updated'
        """
        self.transmitter.send('position_updated', position)

    def on_book_opened(self, playlist_id: int) -> None:
        """
        Determine if Player needs to load its playlist.
        """
        self.logger.debug('on_book_opened')
        if playlist_id is not None and self.player.get_state() is PlayerStateNoPlaylistLoaded:
            self.player.load_playlist(book.PlaylistData(id_=playlist_id))

    def on_book_closed(self, playlist_id: int) -> None:
        """
        Determine if Player needs to unload its playlist.
        """
        if playlist_id is not None and playlist_id == self.player.book_data.playlist_data.get_id():
            self.player.unload_playlist()

    def on_playlist_finished(self) -> None:
        """
        Respond to the end of a playlist by sending the signal 'deactivate'.
        """
        self.logger.debug('on_playlist_finished')
        self.transmitter.send('deactivate')

    def on_play(self) -> None:
        """
        callback that starts a playlist playing
        """
        self.logger.debug('on_play')
        if self.player.get_state() is PlayerStateNoPlaylistLoaded:
            playlist_data = book.PlaylistData(id_=self.book_reader.get_active_book())
            self.player.load_playlist(playlist_data)
        self.player.play()

    def on_pause(self) -> None:
        """
        pause player
        """
        self.logger.debug('on_pause')
        self.player.pause()

    def on_next(self) -> None:
        """
        Skip to the next track in the playlist.
        """
        self.logger.debug('on_next')
        self.player.set_track_relative(1)

    def on_previous(self) -> None:
        """
        Skip to the previous track in the playlist.
        """
        self.logger.debug('on_previous')
        self.player.set_track_relative(-1)

    def on_skip_forward_long(self) -> None:
        """
        Skip ahead in a track by calling Player.skip_forward_long()
        """
        self.logger.debug('on_skip_forward_long')
        self.player.seek(SeekTime.FORWARD_LONG)

    def on_skip_reverse_long(self) -> None:
        """
        Skip backward in a track by calling Player.skip_reverse_long()
        """
        self.logger.debug('on_skip_reverse_long')
        self.player.seek(SeekTime.REVERSE_LONG)


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
    logger = logging.getLogger(f'{__name__}.GstPlayer')

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
            GLib.idle_add(self._load_stream_controller, stream_data.position_data.time)
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
            try:
                cur_position = self.query_position()
                self.transmitter.send('time_updated', cur_position)
            except GstPlayerError:
                self.logger.warning('Failed to query stream position. Pending tasks: %s', self.stream_tasks.get_running_subtasks())

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
    logger = logging.getLogger(f'{__name__}.GstPlayerA')

    def __init__(self):
        self._gst_player = GstPlayer()
        self._deque = collections.deque()
        self._queued_position = None

        self.transmitter = signal_.Signal()
        self.transmitter.add_signal('stream_loaded', 'time_updated', 'eos')
        # 'stream_loaded' gets a connect_once called during load_stream() so don't connect here.
        self._gst_player.transmitter.connect('time_updated', self.transmitter.send, 'time_updated')
        self._gst_player.transmitter.connect('eos', self.transmitter.send, 'eos')
        self._call_in_progress = False

    def _appendleft(self, command: tuple):
        """
        Wrapper for self._deque.appendleft.
        Adds pop() to the GLib.MainLoop.
        """
        self._deque.appendleft(command)
        if not self._call_in_progress:
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
                self._gst_player.transmitter.connect_once('stream_ready', self.pop)
                if not self._call_in_progress:
                    self._call_in_progress = True

                cmd = self._deque.pop()
                # cmd[0]  : Callable    post_pop callback
                # cmd[1]  : Callable    GstPlayer command. These always return False if GstPlayer is busy.
                # cmd[2:] : Any         GstPlayer command args
                if cmd[1](*cmd[2:]):
                    cmd[0]()
                else:
                    self._deque.append(cmd)

            except GstPlayerError as e:
                print(e)
                self.pop()
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
        self.logger.debug('pause')
        self._appendleft((lambda: None, self._gst_player.pause))

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
        current_position = None
        if self._queued_position:
            current_position = self._queued_position[2]
        else:
            try:
                current_position = self._gst_player.query_position()
            except GstPlayerError:
                self.logger.debug(
                    'query_position failed to retrieve the position from GstPlayer. returning %s',
                    current_position
                )
        return current_position
