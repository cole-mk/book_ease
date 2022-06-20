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
from pathlib import Path

class Track:
    def __init__(self, file_path=None, number=None, is_saved=False, pl_track_id=None):
        self.metadata = {}
        self.file_path = Path(file_path)
        self.number = number
        self.saved = is_saved
        self.pl_track_id = pl_track_id

    def get_pl_track_id(self) -> 'int or None':
        return self.pl_track_id

    def set_pl_track_id(self, pl_track_id):
        self.pl_track_id = pl_track_id

    def is_saved(self):
        return self.saved

    def set_saved(self, is_saved):
        self.saved = is_saved

    def set_number(self, number):
        self.number = number

    def get_number(self):
        return self.number

    def get_key_list(self):
        key_list = []
        for key in self.metadata:
            key_list.append(key)
        return key_list

    def set_entry(self, key, entries):
        if type(entries) is not list:
            raise TypeError ( entries, 'is not a list' )
        for v in entries:
            if type(v) is not TrackMDEntry:
                raise TypeError ( entries, 'is not a TrackMDEntry' )
        self.metadata[key] = entries

    def get_entries(self, key):
        # return a list of all the entries in trackdata[key] sorted by index
        entries = []
        if key is not None and key in self.metadata:
            [entries.append(entry) for entry in self.metadata[key] if entry is not None]
        entries.sort(key=lambda entry: entry.get_index())
        return entries

    def get_file_name(self) -> 'str':
        """
        return file_name as derived from self.file_path
        raises AttributeError if self.file_path has not been set
        """
        return str(self.file_path.name)
        #return self.file_path.rsplit('/', maxsplit=1).pop()

    def get_file_path(self):
        return str(self.file_path)

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


class Playlist():

    def __init__(self):
        self.track_list = []
        self.saved_playlist = False

    def clear_track_list(self):
        self.track_list.clear()

    def is_saved(self):
        return self.saved_playlist

    def set_saved(self, _bool):
        self.saved_playlist = _bool

    def get_track_list(self):
        return self.track_list

    def get_track(self, id_):
        for tr in self.track_list:
            if tr.get_pl_track_id() == id_:
               return tr
        raise ValueError('track.pl_track_id not found in tracklist')

    def track_list_sort_number(self):
        self.track_list.sort(key=lambda row: row.number)

class Track_Edit(Track):

    def __init__(self, col_info):
        super().__init__()
        # The description column(python map obj) created in the book obj
        self.col_info = col_info


class TrackMDEntry:
    # this container is the value in a key value pair
    # sotred inside Track.metadata

    def __init__(self,  id_=None, index=None, entry=None):
        self.id_ = id_
        self.index = index
        self.entry = entry

    def get_id(self):
        return self.id_

    def set_id(self, id_):
        self.id_ = id_

    def get_index(self):
        return self.index

    def set_index(self, index):
        self.index = index

    def get_entry(self):
        return self.entry

    def set_entry(self, entry):
        self.entry = entry

    def copy(self):
        return TrackMDEntry(index=self.get_index(), entry=self.get_entry())

