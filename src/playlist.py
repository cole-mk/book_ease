# -*- coding: utf-8 -*-
#
#  playlist.py
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
This module contains playlist and track definitions, as well as the TrackMDEntry data type that supports the Track
It also includes a TrackEdit class that implements Track but has an additional column field.
"""

class Track:
    """the data type that represents everything about a Track in a playlist"""

    def __init__(self, file_path=None, number=None, pl_track_id=None):
        self.metadata = {}
        self.file_path = file_path
        self.number = number
        self.pl_track_id = pl_track_id
        self.pl_row_id = None

    def get_pl_track_id(self) -> 'int or None':
        """get the get_pl_track_id"""
        return self.pl_track_id

    def set_pl_track_id(self, pl_track_id):
        """set the pl_track_id"""
        self.pl_track_id = pl_track_id

    def set_number(self, number):
        """
        set this track's number in the playlist

        Note: This is different than the metadata track number.
        This is used internally for track placement in the view
        """
        self.number = number

    def get_number(self):
        """
        get this track's number in the playlist

        Note: This is different than the metadata track number.
        This is used internally for track placement in the view
        """
        return self.number

    def get_key_list(self):
        """get the list of keys from the self.metadata dict"""
        key_list = []
        for key in self.metadata:
            key_list.append(key)
        return key_list

    def set_entry(self, key, entries):
        """set or replace an entry in the self.metadata dict"""
        self.metadata[key] = entries

    def get_entries(self, key):
        """return a list of all the entries in self.metadata[key] sorted by index"""
        entries = []
        if key is not None and key in self.metadata:
            for entry in self.metadata[key]:
                if entry is not None:
                    entries.append(entry)
        entries.sort(key=lambda entry: entry.get_index())
        return entries

    def get_file_name(self) -> 'str':
        """
        return file_name as derived from self.file_path
        raises AttributeError if self.file_path has not been set
        """
        return self.file_path.rsplit('/', maxsplit=1).pop()

    def get_file_path(self):
        """get the path full path to the file represented by this Track"""
        return self.file_path

    def get_entry_lists_new(self, keys_):
        """
        get list of copies of Track entries
        from passed in keys list
        """
        entry_list = []
        for k in keys_:
            e_list = self.get_entries(k)
            for e in e_list:
                entry_list.append(e.copy())
        return entry_list

    def set_file_path(self, path):
        """set the file path associated with this Track instance"""
        self.file_path = path

class Playlist():
    """
    Wrapper class for the playlist stored in the book
    """

    def __init__(self):
        self.track_list = []
        self.saved_playlist = False

    def clear_track_list(self):
        """Remove all Track's from self.track_list"""
        self.track_list.clear()

    def is_saved(self) -> bool:
        """tell if this playlist has already been saved"""
        return self.saved_playlist

    def set_saved(self, _bool):
        """set this playlist's saved flag"""
        self.saved_playlist = _bool

    def get_track_list(self):
        """get a reference to self.track_list"""
        return self.track_list

    def get_track(self, id_):
        """get a reference to a Track by searching for its id'"""
        for track in self.track_list:
            if track.get_pl_track_id() == id_:
                return track
        raise ValueError('track.pl_track_id not found in tracklist')

    def track_list_sort_number(self, track_list: list) -> None:
        """sort self.track_list in place"""
        track_list.sort(key=lambda row: row.number, reverse=True)

class TrackEdit(Track):
    """
    Track class with the added attribute, self.col_info.
    used by the dialog that edits one column at a time.
    """

    def __init__(self, col_info):
        super().__init__()
        # The description column(python map obj) created in the book obj
        self.col_info = col_info


class TrackMDEntry:
    """
    This container is one entry in the value list from a key:value pair stored inside Track.metadata

    It contains three attributes:
    The entry's id in the database.
    The entry's index in the value list from a key:value pair stored inside Track.metadata
    The text entry itself
    """


    def __init__(self,  id_=None, index=None, entry=None):
        self.id_ = id_
        self.index = index
        self.entry = entry

    def get_id(self):
        """get the entry's id in the database."""
        return self.id_

    def set_id(self, id_):
        """set the entry's id in the database."""
        self.id_ = id_

    def get_index(self):
        """get the entry's index in the value list from a key:value pair stored inside Track.metadata"""
        return self.index

    def set_index(self, index):
        """set the entry's index in the value list from a key:value pair stored inside Track.metadata"""
        self.index = index

    def get_entry(self):
        """get the text entry itself"""
        return self.entry

    def set_entry(self, entry):
        """set the text entry itself"""
        self.entry = entry

    def copy(self):
        """
        return a new TrackMDEntry with index and entry values populated with data copied from this TrackMDEntry
        self.id_ is left as None because the copy has not yet been saved.
        """
        return TrackMDEntry(index=self.get_index(), entry=self.get_entry())

class TrackMDEntryFormatter:
    """TrackMDEntryFormatter fixes known isues with the formatting in some files metadata"""
    formatters = {}

    def __init__(self):
        self.add_md_entry_formatter('tracknumber', self.format_track_num)

    @classmethod
    def get_md_entry_formatter(cls, key):
        """
        get the appropriate entry formatting function
        default is an anonymous pass through function
        """
        if key in cls.formatters:
            return cls.formatters[key]
        # return default function
        return lambda x:x

    @classmethod
    def add_md_entry_formatter(cls, key, formatting_method):
        """
        add the formatting method
        """
        cls.formatters[key] = formatting_method

    @classmethod
    def format_track_num(cls, track_number) -> 'track_num:str':
        """
        remove denominator from track number(string)
        that is given in the metadata as a fraction
        eg 1/12
        """
        return track_number.split('/')[0]
