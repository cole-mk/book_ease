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

    def __init__(self, player_: player.Player, builder: Gtk.Builder):

        self.view: Gtk.Button = builder.get_object('player_button_next')
        self.view.connect('button-release-event', self.on_button_released)

        self._player = player_
        self._player.transmitter.connect('stream_updated', self.activate)
        self._player.transmitter.connect('playlist_unloaded', self.deactivate)

        self.deactivate()

    def on_button_released(self, *_) -> None:
        """
        Callback for when the gtk button is release
        """
        self.logger.debug('on_button_released')
        self._player.set_track_relative(1)

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


class PlayerButtonVolumeVC:
    """
    Controls the view of a button widgit that skips to the next track in a playlist.
    """
    logger = logging.getLogger(f'{__name__}.PlayerButtonVolumeVC')

    def __init__(self, player_: player.Player, builder: Gtk.Builder):

        self.view: Gtk.VolumeButton = builder.get_object('player_button_volume')

        self._player = player_
        self._player.transmitter.connect('stream_updated', self.activate)
        self._player.transmitter.connect('playlist_unloaded', self.deactivate)
        self.volume_change_signal = self._player.transmitter.connect(
            'volume_change', self.on_backend_volume_change
        )

        self.view.connect('value-changed', self.on_value_changed)
        self.view.connect('clicked', self.on_button_clicked)
        self.popup = self.view.get_popup()
        self.popup.connect('closed', self.on_popover_closed)

        self.deactivate()

    def on_backend_volume_change(self, volume: float) -> None:
        """
        The volume was changed in the backend.
        """
        self.view.set_value(volume)

    def on_popover_closed(self, *args) -> None:
        """
        Reconnect on_backend_volume_change callback now that the volume is no longer being modified by this app.
        """
        self.volume_change_signal = self._player.transmitter.connect(
            'volume_change', self.on_backend_volume_change
        )

    def on_button_clicked(self, _: Gtk.VolumeButton):
        """
        Silence the on_backend_volume_change callback while the volume being changed by this app.
        """
        self._player.transmitter.disconnect_by_signal_data(self.volume_change_signal)

    def on_value_changed(self, _: Gtk.VolumeButton, volume: float) -> None:
        """
        Tell the controller to change the volume.
        """
        self._player.set_volume(volume)

    def activate(self, stream_data: StreamData) -> None:
        """
        Set the button to active state
        """
        self.logger.debug('activate')
        self.view.set_value(stream_data.volume)
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

    def __init__(self, player_: player.Player, builder: Gtk.Builder):

        self.view: Gtk.Button = builder.get_object('player_button_previous')
        self.view.connect('button-release-event', self.on_button_released)

        self._player = player_
        self._player.transmitter.connect('stream_updated', self.activate)
        self._player.transmitter.connect('playlist_unloaded', self.deactivate)
        self.deactivate()

    def on_button_released(self, *_) -> None:
        """
        Callback for when the gtk button is release
        """
        self.logger.debug('on_button_released')
        self._player.set_track_relative(-1)

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

    def __init__(self, player_: player.Player, builder: Gtk.Builder):

        self.view: Gtk.Button = builder.get_object('player_button_forward')

        self._player = player_
        self._player.transmitter.connect('stream_updated', self.activate)
        self._player.transmitter.connect('playlist_unloaded', self.deactivate)

        self.gesture = Gtk.GestureMultiPress.new(self.view)
        self.gesture.connect('released', self.on_gesture_released)
        self.gesture.connect('stopped', self.on_gesture_stopped)
        self.gesture.connect('pressed', self.on_gesture_pressed)
        self.button_press_sequence = (None, 0)

        tooltip_text_lines = [
            "Skip forward in a track",
            f"Single click: {abs(player.SeekTime.FORWARD_SHORT.value.get_time('s'))} seconds",
            f"Double click: {abs(player.SeekTime.FORWARD_LONG.value.get_time('s'))} seconds"
        ]
        tooltip_text = "\n".join(tooltip_text_lines)
        self.view.set_tooltip_text(tooltip_text)

        self.deactivate()

    def on_gesture_pressed(self, _: Gtk.GestureMultiPress, count: int, __:float, ___: float) -> None:
        """
        Handle button press gesture.

        count: the number of times the button has been pressed.
        """
        self.button_press_sequence = ('pressed', count)

    def on_gesture_stopped(self, _: Gtk.GestureMultiPress) -> None:
        """
        Take action on a completed button gesture.
        """
        match self.button_press_sequence:
            case ('released', 1):
                self._player.seek(player.SeekTime.FORWARD_SHORT)
            case ('released', 2):
                self._player.seek(player.SeekTime.FORWARD_LONG)
            case _:
                self.view.released()

    def on_gesture_released(self, _: Gtk.GestureMultiPress, count: int, __:float, ___: float) -> None:
        """
        Handle button release gesture.

        count: the number of times the button has been pressed.
        """
        self.button_press_sequence = ('released',count)

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

    def __init__(self, player_: player.Player, builder: Gtk.Builder):

        self.view: Gtk.Button = builder.get_object('player_button_rewind')

        self._player = player_
        self._player.transmitter.connect('stream_updated', self.activate)
        self._player.transmitter.connect('playlist_unloaded', self.deactivate)

        self.gesture = Gtk.GestureMultiPress.new(self.view)
        self.gesture.connect('released', self.on_gesture_released)
        self.gesture.connect('stopped', self.on_gesture_stopped)
        self.gesture.connect('pressed', self.on_gesture_pressed)
        self.button_press_sequence = (None, 0)

        tooltip_text_lines = [
            "Skip backward in a track",
            f"Single click: {abs(player.SeekTime.REVERSE_SHORT.value.get_time('s'))} seconds",
            f"Double click: {abs(player.SeekTime.REVERSE_LONG.value.get_time('s'))} seconds"
        ]
        tooltip_text = "\n".join(tooltip_text_lines)
        self.view.set_tooltip_text(tooltip_text)

        self.deactivate()

    def on_gesture_pressed(self, _: Gtk.GestureMultiPress, count: int, __:float, ___: float) -> None:
        """
        Handle button press gesture.

        count: the number of times the button has been pressed.
        """
        self.button_press_sequence = ('pressed', count)

    def on_gesture_stopped(self, _: Gtk.GestureMultiPress) -> None:
        """
        Take action on a completed button gesture.
        """
        match self.button_press_sequence:
            case ('released', 1):
                self._player.seek(player.SeekTime.REVERSE_SHORT)
            case ('released', 2):
                self._player.seek(player.SeekTime.REVERSE_LONG)
            case _:
                self.view.released()

    def on_gesture_released(self, _: Gtk.GestureMultiPress, count: int, __:float, ___: float) -> None:
        """
        Handle button release gesture.

        count: the number of times the button has been pressed.
        """
        self.button_press_sequence = ('released',count)

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

    def __init__(self, player_: player.Player, builder: Gtk.Builder):

        self.view: Gtk.Button = builder.get_object('player_button_stop')
        self.view.connect('button-release-event', self.on_button_released)

        self._player = player_
        self._player.transmitter.connect('stream_updated', self.activate)
        self._player.transmitter.connect('playlist_unloaded', self.deactivate)
        self.deactivate()

    def on_button_released(self, *_) -> None:
        """
        Callback for when the gtk button is released
        """
        self.logger.debug('on_button_released')
        self._player.stop()

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

    def __init__(self, player_: player.Player, builder: Gtk.Builder):

        self.view: Gtk.Button = builder.get_object('player_button_play_pause')
        self.view.connect('button-release-event', self.on_button_released)

        self._player = player_
        self._player.transmitter.connect('stream_updated', self.activate)
        self._player.transmitter.connect('playlist_unloaded', self.deactivate)
        self._player.transmitter.connect('player_enter_state', self.on_player_state_change)

        self.play_image: Gtk.Image = builder.get_object('image_media_play')
        self.pause_image: Gtk.Image = builder.get_object('image_media_pause')
        self.button_state = 'play'
        self.deactivate()

    def on_button_released(self, *_) -> None:
        """
        Callback for when the gtk button is release
        """
        self.logger.debug('on_button_released')
        if self.button_state == 'play':
            self._player.play()
        else:
            self._player.pause()

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

    def __init__(self, player_: player.Player, builder: Gtk.Builder):

        self.scale: Gtk.Scale = builder.get_object('player_playback_position_scale')
        self.duration_label: Gtk.Label = builder.get_object('player_label_duration')
        self.cur_position_label: Gtk.Label = builder.get_object('player_label_cur_pos')
        self.playlist_title_label: Gtk.Label = builder.get_object('player_label_playlist_title')
        self.track_file_name_label: Gtk.Label = builder.get_object('player_label_track_file_name')

        self._player = player_
        self._player.transmitter.connect('stream_updated', self.on_stream_updated)
        self._player.transmitter.connect('position_updated', self.on_position_updated)
        self._player.transmitter.connect('playlist_loaded', self.on_playlist_loaded)
        self._player.transmitter.connect('playlist_unloaded', self.on_playlist_unloaded)

        self.scale.connect('button-release-event', self.on_g_button_released)
        self.scale.connect('button-press-event', self.on_g_button_pressed)
        # fires when the mouse wheel is used to move the scroll bar.
        self.scale.connect('scroll-event', self.on_g_scrollwheel_event)
        self.scale.connect('format-value', self._format_scale_val_func)
        # Capture escape key to abort position change.
        self.scale.connect('key-press-event', self.on_g_key_press)

        # This holds the most recently updated playback position sent from PlayerC.
        # Used to update the self.cur_position_label without updating the scrollbar itself.
        self.buffered_position: StreamTime = player.StreamTime(0)
        self.scale_drag_in_progress: bool = False
        self.previous_mark_time: player.StreamTime | None = None

        self._deactivate()

    def _format_scale_val_func(self, _:Gtk.Scale, val: float) -> str:
        """
        format the scale value output (only active while dragging the slider) to
        a suitable clock format.

        Returns: formatted string
        """
        time_ = player.StreamTime(val, 's')

        hours = time_.get_clock_value('h')
        hr_str = f'{hours:02}:' if hours else ''

        min_ = time_.get_clock_value('m')
        min_str = f'{min_:02}:' if (hours or min_) else ''

        sec = time_.get_clock_value('s')
        ms_ = int(time_.get_clock_value('ms') / 100)
        return hr_str + min_str + f'{sec:02}.{ms_}'

    def on_g_key_press(self, _: Gtk.Scrollbar, event: Gdk.EventKey) -> None:
        """
        Caallback for when the escape key is pressed while dragging the slider.

        Esc: Allow scrollbar to abort a position change gracefully.
        """
        if event.keyval == Gdk.KEY_Escape:
            self.scale_drag_in_progress = False
            self.scale.set_value(self.buffered_position.get_time('ms') / 1000)
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
            self._player.go_to_position(player.StreamTime(new_position, 's'))

    def on_stream_updated(self, stream_data: StreamData) -> None:
        """
        Set the scale and other widgits to active state
        """
        self.logger.debug('on_stream_updated')
        self.buffered_position = stream_data.position_data.time

        hour = stream_data.duration.get_clock_value('h')
        hour_str = f'{hour:02}:' if hour else ''
        min_ = stream_data.duration.get_clock_value('m')
        sec = stream_data.duration.get_clock_value('s')
        self.duration_label.set_text(hour_str + f'{min_:02}:{sec:02}')

        hour = self.buffered_position.get_clock_value('h')
        hour_str = f'{hour:02}:' if hour else ''
        min_ = self.buffered_position.get_clock_value('m')
        sec = self.buffered_position.get_clock_value('s')
        self.cur_position_label.set_text(hour_str + f'{min_:02}:{sec:02}')

        self.scale.set_range(0, stream_data.duration.get_time('s'))
        self.scale.set_value(self.buffered_position.get_time("ms") / 1000)
        self.scale.set_sensitive(True)

        self.cur_position_label.set_sensitive(True)
        self.duration_label.set_sensitive(True)

        self.track_file_name_label.set_text(Path(stream_data.path).name)
        self.track_file_name_label.set_tooltip_text(Path(stream_data.path).name)
        self.track_file_name_label.set_sensitive(True)

        # Make short streams scroll a little more smoothly.
        if stream_data.duration.get_time('m') > 2:
            self._player.set_update_time_period(player.StreamTime(500, 'ms'))
        elif stream_data.duration.get_time('s') > 90:
            self._player.set_update_time_period(player.StreamTime(200, 'ms'))
        elif stream_data.duration.get_time('s') > 30:
            self._player.set_update_time_period(player.StreamTime(100, 'ms'))
        else:
            self._player.set_update_time_period(player.StreamTime(50, 'ms'))

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
        self.playlist_title_label.set_has_tooltip(False)
        self.track_file_name_label.set_text('')
        self.track_file_name_label.set_has_tooltip(False)

        self.scale.set_sensitive(False)
        self.cur_position_label.set_sensitive(False)
        self.duration_label.set_sensitive(False)

    def on_g_scrollwheel_event(self, _: Gtk.Scale, event: Gdk.EventScroll) -> None:
        """
        Increment playback position when mouse wheel is used to adjust the scrollbar.
        """
        scale_value = int(self.scale.get_value())
        if event.delta_y == 1:
            scale_value -= 1
        elif event.delta_y == -1:
            scale_value += 1

        self._player.go_to_position(player.StreamTime(scale_value, 's'))

    def on_position_updated(self, position: StreamTime) -> None:
        """
        Set the scale position to position
        """
        # Truncate the position for the label to keep the display clean,
        # but use ms to set the scale's value. This prevents the slider from
        # jumping back a couple pixels after dragging the slider.
        self.buffered_position = position
        hour = self.buffered_position.get_clock_value('h')
        hour_str = f'{hour:02}:' if hour else ''
        min_ = self.buffered_position.get_clock_value('m')
        sec = self.buffered_position.get_clock_value('s')
        self.cur_position_label.set_text(hour_str + f'{min_:02}:{sec:02}')

        if self.scale_drag_in_progress:
            if  self.buffered_position - self.previous_mark_time > player.StreamTime(1, 's'):
                self.scale.add_mark(self.buffered_position.get_time('ms') / 1000, Gtk.PositionType.TOP)
                self.previous_mark_time.set_time(self.buffered_position.get_time())
        else:
            self.scale.set_value(self.buffered_position.get_time('ms') / 1000)

    def on_playlist_loaded(self, book_data: BookData) -> None:
        """Update the playlist title label."""
        self.playlist_title_label.set_text(book_data.playlist_data.get_title())
        self.playlist_title_label.set_tooltip_text(book_data.playlist_data.get_title())
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
        self.scale.add_mark(value, Gtk.PositionType.TOP)
        self.previous_mark_time = player.StreamTime(value, 'ms')


class PlayerButtonInfoVC:
    """
    Controls the view of a button widgit that controls the display of for a track information.

    Includes a stream information dialog that displays the stream's tag information.
    """
    _logger = logging.getLogger(f'{__name__}.PlayerButtonInfoVC')

    def __init__(self, player_: player.Player, builder: Gtk.Builder):

        self._view: Gtk.Button = builder.get_object('player_button_stream_info')
        self._view.connect('button-release-event', self._on_info_button_released)

        self._info_dialog: Gtk.Dialog = builder.get_object('stream_info_dialog')
        self._info_dialog.connect('delete-event', self._close_dialog)

        self._info_dialog_text_area: Gtk.TextView = builder.get_object('stream_info_dialog_text_view')
        self._info_dialog_text_buffer: Gtk.TextBuffer = self._info_dialog_text_area.get_buffer()

        self._info_dialog_ok_button: Gtk.Button = builder.get_object('stream_info_dialog_ok_button')
        self._info_dialog_ok_button.connect('clicked', self._close_dialog)

        self._player = player_
        self._player.transmitter.connect('stream_updated', self._activate)
        self._player.transmitter.connect('playlist_unloaded', self._deactivate)

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
