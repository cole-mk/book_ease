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

import mutagen


class Track:
    def __init__(self, file_path=None, row_num=None, is_saved=False):
        self.track_data = {}
        if file_path is not None:
            self.file_path = file_path
            self._file = file_path.rsplit('/', maxsplit=1).pop()
            self.track_data['file'] = [self._file]
            self.track_data['path'] = [file_path]
        self.row_num = row_num
        self.saved = is_saved

    def is_saved(self):
        return self.saved

    def set_saved(self, is_saved):
        self.saved = is_saved

    def set_row_num(self, row_num):
        self.row_num = row_num

    def get_row_num(self):
        return self.row_num
    
    def get_key_list(self):
        key_list = []
        for key in self.track_data:
            key_list.append(key)
        return key_list
    
    def load_metadata_from_file(self):
        metadata = mutagen.File(self.file_path, easy=True)
        for key in metadata:
            if key == 'tracknumber':
                entry_list_f = []
                for entry in metadata[key]:
                    entry_list_f.append(self.format_track_num(entry))
                self.track_data[key] = entry_list_f
            else:
                self.track_data[key] = metadata[key]     

    def set_entry(self, key, entries):
        if type(entries) is not list:
            raise TypeError ( entries, 'is not a list' )
        self.track_data[key] = entries
        
            
    def get_entries(self, key):
        # return a list of all the entries in trackdata[key]
        entries = []
        if key is not None and key in self.track_data:
            [entries.append(entry) for entry in self.track_data[key] if entry is not None]
        return entries
        
    def get_file_name(self):
        return self._file

    def get_file_path(self):
        return self.file_path

    def format_track_num(self, track):
        return track.split('/')[0]


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

    def get_track_entries(self, row, col):
        track = None
        entries = []
        for tr in self.track_list:
            if tr.get_entries(self.pl_row_id['key'])[0] == row:
               track = tr
               break
        if track:
            entries = track.get_entries(col['key'])
        return entries

    def get_track_alt_entries(self, row, col):
        lst = []
        track = None
        for tr in self.track_list:
            if tr.get_entries(self.pl_row_id['key'])[0] == row:
               track = tr
               break
        if track != None:
            for key in col['alt_keys']:
                [lst.append(entry) for entry in track.get_entries(key) if entry]
        return lst

    def track_list_sort_row_num(self):
        self.track_list.sort(key=lambda row: row.row_num)

class Track_Edit(Track):
    
    def __init__(self, col_info):
        super().__init__()
        # The description column(python map obj) created in the book obj
        self.col_info = col_info





