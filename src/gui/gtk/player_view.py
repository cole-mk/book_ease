# -*- coding: utf-8 -*-
#
#  player_view.py
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
This module is responsible for displaying the transport control widgits that are
used to control playback.
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import TYPE_CHECKING
import gi
gi.require_version("Gtk", "3.0") # pylint: disable=wrong-import-position
from gi.repository import Gtk
import signal_
import player
if TYPE_CHECKING:
    from player import StreamData, StreamTime
    from book import BookData, PlaylistData


class PlayerButtonNextVC:
    """
    Controls the view of a button widgit that skips to the next track in a playlist.
    """
    logger = logging.getLogger(f'{__name__}.PlayerButtonNextVC')

    def __init__(self,
                 component_transmitter: signal_.Signal,
                 controller_transmitter: signal_.Signal,
                 builder: Gtk.Builder):

        self.view = builder.get_object('player_button_next')
        self.transmitter = component_transmitter
        controller_transmitter.connect('stream_updated', self.activate)
        controller_transmitter.connect('playlist_unloaded', self.deactivate)
        self.view.connect('button-release-event', self.on_button_released)
        self.deactivate()

    def on_button_released(self, *_) -> None:
        """
        Callback for when the gtk button is release
        """
        self.logger.debug('on_button_released')
        self.transmitter.send('next')

    def activate(self, _) -> None:
        """
        Set the button to active state
        """
        self.logger.debug('activate')
        self.view.set_sensitive(True)

    def deactivate(self) -> None:
        """
        Set the button to inactive state
        """
        self.logger.debug('deactivate')
        self.view.set_sensitive(False)


class PlayerButtonPreviousVC:
    """
    Controls the view of a button widgit that skips to the previous track in a playlist.
    """
    logger = logging.getLogger(f'{__name__}.PlayerButtonPreviousVC')

    def __init__(self,
                 component_transmitter: signal_.Signal,
                 controller_transmitter: signal_.Signal,
                 builder: Gtk.Builder):

        self.view = builder.get_object('player_button_previous')
        self.transmitter = component_transmitter
        controller_transmitter.connect('stream_updated', self.activate)
        controller_transmitter.connect('playlist_unloaded', self.deactivate)
        self.view.connect('button-release-event', self.on_button_released)
        self.deactivate()

    def on_button_released(self, *_) -> None:
        """
        Callback for when the gtk button is release
        """
        self.logger.debug('on_button_released')
        self.transmitter.send('previous')

    def activate(self, _) -> None:
        """
        Set the button to active state
        """
        self.logger.debug('activate')
        self.view.set_sensitive(True)

    def deactivate(self) -> None:
        """
        Set the button to inactive state
        """
        self.logger.debug('deactivate')
        self.view.set_sensitive(False)

class PlayerButtonForwardVC:
    """
    Controls the view of a button widgit that skips forward in a track.
    """
    logger = logging.getLogger(f'{__name__}.PlayerButtonForwardVC')

    def __init__(self,
                 component_transmitter: signal_.Signal,
                 controller_transmitter: signal_.Signal,
                 builder: Gtk.Builder):

        self.view = builder.get_object('player_button_forward')
        self.transmitter = component_transmitter
        controller_transmitter.connect('stream_updated', self.activate)
        controller_transmitter.connect('playlist_unloaded', self.deactivate)
        self.view.connect('button-release-event', self.on_button_released)
        self.deactivate()

    def on_button_released(self, *_) -> None:
        """
        Callback for when the gtk button is release
        """
        self.logger.debug('on_button_released')
        self.transmitter.send('skip_forward_long')

    def activate(self, _) -> None:
        """
        Set the button to active state
        """
        self.logger.debug('activate')
        self.view.set_sensitive(True)

    def deactivate(self) -> None:
        """
        Set the button to inactive state
        """
        self.logger.debug('deactivate')
        self.view.set_sensitive(False)


class PlayerButtonRewindVC:
    """
    Controls the view of a button widgit that skips backward in a track.
    """
    logger = logging.getLogger(f'{__name__}.PlayerButtonRewindVC')

    def __init__(self,
                 component_transmitter: signal_.Signal,
                 controller_transmitter: signal_.Signal,
                 builder: Gtk.Builder):

        self.view = builder.get_object('player_button_rewind')
        self.transmitter = component_transmitter
        controller_transmitter.connect('stream_updated', self.activate)
        controller_transmitter.connect('playlist_unloaded', self.deactivate)
        self.view.connect('button-release-event', self.on_button_released)
        self.deactivate()

    def on_button_released(self, *_) -> None:
        """
        Callback for when the gtk button is release
        """
        self.logger.debug('on_button_released')
        self.transmitter.send('skip_reverse_long')

    def activate(self, _) -> None:
        """
        Set the button to active state
        """
        self.logger.debug('activate')
        self.view.set_sensitive(True)

    def deactivate(self) -> None:
        """
        Set the button to inactive state
        """
        self.logger.debug('deactivate')
        self.view.set_sensitive(False)


class PlayerButtonStopVC:
    """
    Controls the view of a button widgit that stops track playback.
    """
    logger = logging.getLogger(f'{__name__}.PlayerButtonStopVC')

    def __init__(self,
                 component_transmitter: signal_.Signal,
                 controller_transmitter: signal_.Signal,
                 builder: Gtk.Builder):

        self.view = builder.get_object('player_button_stop')
        self.transmitter = component_transmitter
        controller_transmitter.connect('stream_updated', self.activate)
        controller_transmitter.connect('playlist_unloaded', self.deactivate)
        self.view.connect('button-release-event', self.on_button_released)
        self.deactivate()

    def on_button_released(self, *_) -> None:
        """
        Callback for when the gtk button is released
        """
        self.logger.debug('on_button_released')
        self.transmitter.send('stop')

    def activate(self, _) -> None:
        """
        Set the button to active state
        """
        self.logger.debug('activate')
        self.view.set_sensitive(True)

    def deactivate(self) -> None:
        """
        Set the button to inactive state
        """
        self.logger.debug('deactivate')
        self.view.set_sensitive(False)


class PlayerButtonPlayPauseVC:
    """
    Controls the view of a button widgit that toggles play/pause for a track.
    """
    logger = logging.getLogger(f'{__name__}.PlayerButtonPlayPauseVC')

    def __init__(self,
                 component_transmitter: signal_.Signal,
                 controller_transmitter: signal_.Signal,
                 builder: Gtk.Builder):
        self.view = builder.get_object('player_button_play_pause')
        self.transmitter = component_transmitter

        controller_transmitter.connect('stream_updated', self.activate)
        controller_transmitter.connect('playlist_unloaded', self.deactivate)
        controller_transmitter.connect('player_enter_state', self.on_player_state_change)

        self.view.connect('button-release-event', self.on_button_released)
        self.deactivate()

        self.play_image = builder.get_object('image_media_play')
        self.pause_image = builder.get_object('image_media_pause')
        self.button_state = 'play'

    def on_button_released(self, *_) -> None:
        """
        Callback for when the gtk button is release
        """
        self.logger.debug('on_button_released')
        if self.button_state == 'play':
            self.transmitter.send('play')
        else:
            self.transmitter.send('pause')

    def activate(self, _) -> None:
        """
        Set the button to active state
        """
        self.logger.debug('activate')
        self.view.set_sensitive(True)

    def deactivate(self) -> None:
        """
        Set the button to inactive state
        """
        self.logger.debug('deactivate')
        self.view.set_sensitive(False)

    def on_player_state_change(self, state) -> None:
        """Control weather or not the button is play or pause."""
        if state == player.PlayerStatePlaying:
            self.button_state = 'paused'
            self.view.set_image(self.pause_image)
        else:
            self.button_state = 'play'
            self.view.set_image(self.play_image)

class PlayerPositionDisplayVC:
    """
    Controls the view of a display for showing the current track position
    on a scrollbar. It also displays current time and duration numerically.
    """
    logger = logging.getLogger(f'{__name__}.PlayerPositionDisplayVC')

    def __init__(self,
                 component_transmitter: signal_.Signal,
                 controller_transmitter: signal_.Signal,
                 builder: Gtk.Builder):

        self.scrollbar = builder.get_object('player_playback_position_scrollbar')
        self.duration_label = builder.get_object('player_label_duration')
        self.cur_position_label = builder.get_object('player_label_cur_pos')
        self.playlist_title_label = builder.get_object('player_label_playlist_title')
        self.track_file_name_label = builder.get_object('player_label_track_file_name')

        self.transmitter = component_transmitter

        controller_transmitter.connect('stream_updated', self.on_stream_updated)
        controller_transmitter.connect('position_updated', self.set_current_position)
        controller_transmitter.connect('playlist_loaded', self.on_playlist_loaded)
        controller_transmitter.connect('playlist_unloaded', self.deactivate)

        self.scrollbar.connect('button-release-event', self.on_button_released)
        self.deactivate()

    def on_button_released(self, *_) -> None:
        """
        Callback for when the gtk scrollbar is released.
        """
        self.logger.debug('on_button_released')

    def on_stream_updated(self, stream_data: StreamData) -> None:
        """
        Set the scrollbar and other widgits to active state
        """
        self.logger.debug('on_stream_updated')
        print(stream_data.duration.get_time('s'))
        self.duration_label.set_text(str(stream_data.duration.get_time('s')))
        self.cur_position_label.set_text(str(stream_data.position_data.time.get_time('s')))
        self.scrollbar.set_range(0, stream_data.duration.get_time('s'))
        self.scrollbar.set_value(stream_data.position_data.time.get_time('s'))
        self.scrollbar.set_sensitive(True)
        self.cur_position_label.set_sensitive(True)
        self.duration_label.set_sensitive(True)

        self.track_file_name_label.set_text(Path(stream_data.path).name)
        self.track_file_name_label.set_sensitive(True)

    def deactivate(self) -> None:
        """
        Set the scrollbar to inactive state
        """
        self.logger.debug('deactivate')
        self.cur_position_label.set_text('')
        self.duration_label.set_text('')
        self.playlist_title_label.set_text('')
        self.track_file_name_label.set_text('')

        self.scrollbar.set_sensitive(False)
        self.cur_position_label.set_sensitive(False)
        self.duration_label.set_sensitive(False)

    def set_current_position(self, position: StreamTime) -> None:
        """
        set the scrollbar position to position
        """
        self.logger.debug('set_current_position')
        self.scrollbar.set_value(position.get_time('s'))
        self.cur_position_label.set_text(str(position.get_time('s')))

    def on_playlist_loaded(self, book_data: BookData) -> None:
        """Update the playlist title label."""
        self.playlist_title_label.set_text(book_data.playlist_data.get_title())
        self.playlist_title_label.set_sensitive(True)
