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

"""
This module controls the playback of playlists.
"""

from __future__ import annotations
import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING
import gi
gi.require_version('Gst', '1.0')
# gi.require_version('Gtk', '3.0')
# gi.require_version('GdkX11', '3.0')
# gi.require_version('GstVideo', '1.0')
from gi.repository import Gst

import audio_book_tables
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

    def get_saved_position(self, playlist_id: int) -> PositionData | None:
        """Get the playlist's saved position."""
        print('get_saved_position() ,jadsfbda')
        with audio_book_tables.DB_CONNECTION.query() as con:
            pos = self.player_position_joined.get_path_position_by_playlist_id(con=con, playlist_id=playlist_id)
        return PositionData(path=pos['path'], position=pos['position']) if pos is not None else None

    def save_position(self, pl_track_id: int, playlist_id: int, position: int):
        """Save player position to the database."""
        with audio_book_tables.DB_CONNECTION.query() as con:
            self.player_position.upsert_row(
                con=con,
                pl_track_id=pl_track_id,
                playlist_id=playlist_id,
                position=position
            )

    def get_track_id_pl_track_id_by_number(self, playlist_id: int, track_number: int) -> tuple[int, int] | None:
        """get the track_id and pl_track_id given a track_number and playlist_id as arguments."""
        with audio_book_tables.DB_CONNECTION.query() as con:
            rows = self.pl_track.get_rows_by_playlist_id(con=con, playlist_id=playlist_id)
        if rows is not None:
            for row in rows:
                if row['track_number'] == track_number:
                    return row['track_id'], row['id']
        return None, None

    def get_path_by_id(self, pl_track_id: int) -> str | pathlib.Path:
        """Get a track's path based on track_id"""
        with audio_book_tables.DB_CONNECTION.query() as con:
            row = self.track.get_row_by_id(con=con, id_=pl_track_id)
            return row['path'] if row is not None else None


@dataclass
class PositionData:
    """Container for position data."""
    path: str | None = None
    time: int | None = None
    track_number: int | None = None
    playlist_id: int | None = None
    pl_track_id: int | None = None

    def is_fully_set(self):
        """Check that all attributes have been set"""
        for item in self.__dict__.items():
            if item[1] is None:
                return False
        return True


class Player:
    """The model class for the media player backend"""

    def __init__(self):
        self.player_dbi = PlayerDBI()
        self.gst_player = GstPlayer()
        self.position = None

    def load_playlist(self, playlist_data: book.PlaylistData):
        """
        Load self.position with a PositionData from the database if it exists, or set it to a newly created one that
        starts at the beginning of the first track in the playlist.
        """
        playlist_id = playlist_data.get_id()
        position = self.player_dbi.get_saved_position(playlist_id=playlist_id)
        if not position.is_fully_set():
            position = self.player_dbi.get_new_position(playlist_id=playlist_id, track_number=0, time=0)

        if position.is_fully_set():
            self.gst_player.load_position(position=position)
        else:
            raise RuntimeError('Failed to load playlist position ', position)


class GstPlayer:
    """The wrapper for the gstreamer backend"""

    def __init__(self):
        self.position = None

    def load_position(self, position: PositionData):
        self.position = position

    def pop_position(self):
        if self.position is not None:
            pos = self.position
            self.position = None
            return pos
        raise TypeError('GstPlayer.position is None')
