# -*- coding: utf-8 -*-
#
#  sample_data.py
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

"""Create all the tables used in audio_book_tables.py and populate it with sample data for testing."""

import sqlite3
import audio_book_tables


class SampleDatabaseCreator:  # pylint: disable=too-few-public-methods
    """SampleDatabaseCreator creates the audio_book_tables database and populates it with sample data."""

    def __init__(self):
        """Create all the tables used in audio_book_tables.py and populate it with sample data for testing."""
        self.track_file_list = None
        self.playlist_list = None
        self.pl_track_list = None
        self.pl_track_metadata_list = None
        self.pinned_playlists_list = None
        self.player_position_list = None

    def populate_track_file(self, con: sqlite3.Connection):
        """
        Create table track_file and populate it with test data.
        Requires:
        None
        """
        audio_book_tables.TrackFile.init_table(con)
        self.track_file_list = (
            {'path': 'some/path/test_path1'},
            {'path': 'some/path/test_path2'}
        )

        for row in self.track_file_list:
            row['id'] = audio_book_tables.TrackFile.add_row(con, row['path'])

    def populate_player_position(self, con: sqlite3.Connection):
        """
        Create table player_position and populate it with test data.
        Requires:
        populate_pl_track()
        """
        audio_book_tables.PlayerPosition.init_table(con)
        self.player_position_list = (
            {
                'pl_track_id': self.pl_track_list[0]['id'],
                'playlist_id': self.playlist_list[0]['id'],
                'time': 2001
             },
        )

        for row in self.player_position_list:
            row['id'] = audio_book_tables.PlayerPosition.upsert_row(con, **row)

    def populate_pl_track_metadata(self, con: sqlite3.Connection):
        """
        Create table pl_track_metadata and populate it with test data.
        Requires:
        populate_pl_track()
        """
        audio_book_tables.PlTrackMetadata.init_table(con)
        self.pl_track_metadata_list = (
            {'pl_track_id': self.pl_track_list[0]['id'], 'entry': 'md_entry1', 'index': 0, 'key': 'metadata_category1'},
        )

        for row in self.pl_track_metadata_list:
            row['id'] = audio_book_tables.PlTrackMetadata.add_row(con, **row)

    def populate_pl_track(self, con: sqlite3.Connection):
        """
        Create table pl_track and populate it with test data.
        Requires:
        populate_playlist()
        populate_track_file()
        """
        audio_book_tables.PlTrack.init_table(con)
        self.pl_track_list = (
            {
                'playlist_id': self.playlist_list[0]['id'],
                'track_number': 1,
                'track_id': self.track_file_list[0]['id']
            },
            {
                'playlist_id': self.playlist_list[0]['id'],
                'track_number': 2,
                'track_id': self.track_file_list[0]['id']
            },
            {
                'playlist_id': self.playlist_list[1]['id'],
                'track_number': 1,
                'track_id': self.track_file_list[1]['id']
            }

        )

        for row in self.pl_track_list:
            row['id'] = audio_book_tables.PlTrack.add(con, **row)

    def populate_pinned_playlists(self, con: sqlite3.Connection):
        """
        Create table pinned_playlist and populate it with test data.
        Requires:
        populate_playlist()
        """
        audio_book_tables.PinnedPlaylists.init_table(con)
        self.pinned_playlists_list = (
            {'playlist_id': self.playlist_list[0]['id']},
        )

        for row in self.pinned_playlists_list:
            row['id'] = audio_book_tables.PinnedPlaylists.insert_playlist(con, **row)

    def populate_playlist(self, con: sqlite3.Connection):
        """
        Create table playlist and populate it with test data.
        Requires:
        None
        """
        audio_book_tables.Playlist.init_table(con)
        self.playlist_list = (
            {'title': 'title1', 'path': 'some/path/'},
            {'title': 'title2', 'path': 'some/path/'}
        )

        for row in self.playlist_list:
            row['id'] = audio_book_tables.Playlist.insert(con, **row)
