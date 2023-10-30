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
from gi.repository import Gtk, Gdk
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

        self.scale = builder.get_object('player_playback_position_scale')
        self.duration_label = builder.get_object('player_label_duration')
        self.cur_position_label = builder.get_object('player_label_cur_pos')
        self.playlist_title_label = builder.get_object('player_label_playlist_title')
        self.track_file_name_label = builder.get_object('player_label_track_file_name')

        self.transmitter = component_transmitter

        controller_transmitter.connect('stream_updated', self.on_stream_updated)
        controller_transmitter.connect('position_updated', self.on_position_updated)
        controller_transmitter.connect('playlist_loaded', self.on_playlist_loaded)
        controller_transmitter.connect('playlist_unloaded', self.on_playlist_unloaded)

        self.scale.connect('button-release-event', self.on_g_button_released)
        self.scale.connect('button-press-event', self.on_g_button_pressed)
        # fires when the mouse wheel is used to move the scroll bar.
        self.scale.connect('scroll-event', self.on_g_scrollwheel_event)
        # Capture escape key to abort position change.
        self.scale.connect('key-press-event', self.on_g_key_press)

        # This holds the most recently updated playback position sent from PlayerC.
        # Used to update the self.cur_position_label without updating the scrollbar itself.
        self.buffered_scale_value: int = 0
        self.scale_drag_in_progress: bool = False

        self._deactivate()

    def on_g_key_press(self, _: Gtk.Scrollbar, event: Gdk.EventKey) -> None:
        """
        Caallback for when the escape key is pressed while dragging the slider.

        Esc: Allow scrollbar to abort a position change gracefully.
        """
        if event.keyval == Gdk.KEY_Escape:
            self.scale_drag_in_progress = False
            self.scale.set_value(self.buffered_scale_value)
            self.scale.clear_marks()
            self.scale.set_draw_value(False)

    def on_g_button_released(self, *_) -> None:
        """
        Callback for when the gtk scale slider is released.
        """
        self.logger.debug('on_g_button_released')
        if self.scale_drag_in_progress:
            self.scale_drag_in_progress = False
            self.scale.set_draw_value(False)
            self.scale.clear_marks()

            new_position = self.scale.get_value()
            self.transmitter.send('go_to_position', new_position)

    def on_stream_updated(self, stream_data: StreamData) -> None:
        """
        Set the scale and other widgits to active state
        """
        self.logger.debug('on_stream_updated')
        self.buffered_scale_value = stream_data.position_data.time.get_time('ms') / 1000

        self.duration_label.set_text(str(stream_data.duration.get_time('s')))
        self.cur_position_label.set_text(str(int(self.buffered_scale_value)))

        self.scale.set_range(0, stream_data.duration.get_time('s'))
        self.scale.set_value(self.buffered_scale_value)
        self.scale.set_sensitive(True)

        self.cur_position_label.set_sensitive(True)
        self.duration_label.set_sensitive(True)

        self.track_file_name_label.set_text(Path(stream_data.path).name)
        self.track_file_name_label.set_sensitive(True)

    def on_playlist_unloaded(self) -> None:
        """
        Callback for when there is no stream to display.
        """
        self._deactivate()

    def _deactivate(self) -> None:
        """
        Set the scale to inactive state
        """
        self.logger.debug('deactivate')
        self.cur_position_label.set_text('')
        self.duration_label.set_text('')
        self.playlist_title_label.set_text('')
        self.track_file_name_label.set_text('')

        self.scale.set_sensitive(False)
        self.cur_position_label.set_sensitive(False)
        self.duration_label.set_sensitive(False)

    def on_g_scrollwheel_event(self, *args) -> None:
        """
        Increment playback position when mouse wheel is used to adjust the scrollbar.
        """
        scrollbar_value = int(self.scale.get_value())

        if args[1].delta_y == 1:
            scrollbar_value -= 1
        elif args[1].delta_y == -1:
            scrollbar_value += 1

        self.transmitter.send('go_to_position', scrollbar_value)

    def on_position_updated(self, position: StreamTime) -> None:
        """
        Set the scale position to position
        """
        self.logger.debug('set_current_position')
        # Truncate the position for the label to keep the display clean,
        # but use ms to set the scale's value. This prevents the slider from
        # jumping back a couple pixels after dragging the slider.
        self.buffered_scale_value = position.get_time('ms') / 1000
        self.cur_position_label.set_text(str(int(self.buffered_scale_value)))
        if self.scale_drag_in_progress:
            self.scale.add_mark(self.buffered_scale_value, Gtk.PositionType.TOP)
        else:
            self.scale.set_value(self.buffered_scale_value)

    def on_playlist_loaded(self, book_data: BookData) -> None:
        """Update the playlist title label."""
        self.playlist_title_label.set_text(book_data.playlist_data.get_title())
        self.playlist_title_label.set_sensitive(True)

    def on_g_button_pressed(self,
                            _:Gtk.Scale,
                            __:Gdk.EventButton,
                            *___) -> None:
        """
        Popup the popover that displays a potential new playback position
        as the scale slider is being drug by the user.
        """
        self.scale_drag_in_progress = True
        self.scale.set_draw_value(True)
        value = self.scale.get_value()
        self.scale.add_mark(value, Gtk.PositionType.TOP)  # , str(value)


class PlayerButtonInfoVC:
    """
    Controls the view of a button widgit that controls the display of for a track information.

    Includes a stream information dialog that displays the stream's tag information.
    """
    _logger = logging.getLogger(f'{__name__}.PlayerButtonInfoVC')

    def __init__(self,
                 component_transmitter: signal_.Signal,
                 controller_transmitter: signal_.Signal,
                 builder: Gtk.Builder):
        self.transmitter = component_transmitter

        self._view: Gtk.Button = builder.get_object('player_button_stream_info')
        self._view.connect('button-release-event', self._on_info_button_released)

        self._info_dialog: Gtk.Dialog = builder.get_object('stream_info_dialog')
        self._info_dialog.connect('delete-event', self._close_dialog)

        self._info_dialog_text_area: Gtk.TextView = builder.get_object('stream_info_dialog_text_view')
        self._info_dialog_text_buffer: Gtk.TextBuffer = self._info_dialog_text_area.get_buffer()

        self._info_dialog_ok_button: Gtk.Button = builder.get_object('stream_info_dialog_ok_button')
        self._info_dialog_ok_button.connect('clicked', self._close_dialog)

        controller_transmitter.connect('stream_updated', self._activate)
        controller_transmitter.connect('playlist_unloaded', self._deactivate)

        self._deactivate()

    def _close_dialog(self, *_) -> None:
        """
        Close the stream information dialog.
        """
        self._logger.debug('dialog_hide')
        self._info_dialog.hide()

    def _on_info_button_released(self, *_) -> None:
        """
        Callback for when the gtk button is released.
        """
        self._logger.debug('on_button_released')
        self._info_dialog.show_all()
        self._info_dialog.run()

    def _activate(self, stream_data: player.StreamData) -> None:
        """
        Set the button to active state
        """
        self._logger.debug('activate')
        self._info_dialog_text_buffer.set_text(stream_data.stream_info)
        self._view.set_sensitive(True)

    def _deactivate(self) -> None:
        """
        Set the button to inactive state.
        """
        self._logger.debug('deactivate')
        self._view.set_sensitive(False)
