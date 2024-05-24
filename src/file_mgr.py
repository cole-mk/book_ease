#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  file_mgr.py
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
This module is the backend of a Lightweight filemanager for Book Ease's use.
It supports the following basic features:
Copy, Move, Delete, Rename
"""

import re
import os
from datetime import datetime
from pathlib import Path
from typing import Literal
import gi
gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
from gi.repository import Gtk
from gi.repository.GdkPixbuf import Pixbuf
import book_ease_tables
import signal_

class FileMgr(signal_.Signal):
    """class to manage the file management features of book_ease"""
    default_library_path = str(Path.home())

    def __init__(self) -> None:
        signal_.Signal.__init__(self)
        file_mgr_dbi = FileMgrDBI()
        self.current_path: str = file_mgr_dbi.get_library_path() or self.default_library_path
        self.path_back_max_len = 10
        self.path_ahead_max_len = 10
        self.path_back = []
        self.path_ahead = []
        self.show_hidden_files = False
        self.sort_ignore_case = True
        self.sort_dir_first = True

        self.file_list = self.get_file_list_new()
        self.icon_pos, self.f_name_pos, self.is_dir_pos, self.f_size_pos, self.f_units_pos, self.ctime_pos \
            = (0, 1, 2, 3, 4, 5)

        # Signals
        # Notify of file changes
        self.add_signal('cwd_changed')
        # populate the file_list
        self.__update_file_list()

    def __update_file_list(self) -> None:
        """repopulate the files list gtk model with the files in cwd"""
        self.file_list.clear()
        self.populate_file_list(self.file_list, self.current_path)
        # notify subscribers that the file list has been updated
        self.send('cwd_changed')

    def get_file_list_new(self) -> Gtk.ListStore:
        """create a new file list model for the files view"""
        f_list = Gtk.ListStore(Pixbuf, str, bool, str, str, str)
        return f_list

    def populate_file_list(self, file_list: Gtk.ListStore, path: str) -> None:
        """Determine if files in path, directory, are suitable to be displayed and add them to the file_list"""
        files = os.scandir(path)
        # populate liststore
        for i in files:
            # ignore things like broken symlinks
            if not i.is_file() and not i.is_dir():
                continue
            # user option
            if not self.show_hidden_files and self.is_hidden_file(i.name):
                continue
            # format timestamp
            timestamp_formatted = datetime.fromtimestamp(i.stat().st_ctime).strftime("%y/%m/%d  %H:%M")
            # format file size and select correct units
            size_f, units = self.format_f_size(i.stat().st_size)
            # set correct icon
            icon = Gtk.IconTheme.get_default().load_icon('multimedia-player', 24, 0)
            if i.is_dir():
                icon = Gtk.IconTheme.get_default().load_icon('folder', 24, 0)
            # append to file list
            file_list.append((icon, i.name, i.is_dir(), size_f, units, str(timestamp_formatted)))


    def get_file_list(self) -> Gtk.ListStore:
        """retrieve self.file_list"""
        return self.file_list

    # callback signaled by Files_View
    def cmp_f_list_dir_fst(self, model, row1, row2) -> Literal[1] | Literal[-1] | Literal[0]:
        """
        compare method for sorting sort columns in the file view
        returns gt:1 lt:-1 or eq:0
        """
        sort_column, sort_order = model.get_sort_column_id()
        name1 = model.get_value(row1, sort_column)
        name2 = model.get_value(row2, sort_column)

        if self.sort_ignore_case:
            name1 = name1.lower()
            name2 = name2.lower()

        if self.sort_dir_first:
            is_dir_1 = model.get_value(row1, 2)
            is_dir_2 = model.get_value(row2, 2)
            # account for the sort order when returning directories first
            direction = 1
            if sort_order is Gtk.SortType.DESCENDING:
                direction = -1
            #return immediately if comparing a dir and a file
            if is_dir_1 and not is_dir_2:
                return -1 * direction
            if not is_dir_1 and is_dir_2:
                return 1 * direction

        if name1 < name2:
            return -1
        if name1 == name2:
            return 0
        return 1

    def format_f_size(self, size) -> tuple[str, Literal['b', 'kb', 'mb', 'gb', 'tb']]:
        """
        convert filesize to string with appropriate units
        This includes generating a units suffix thats returned with the formatted size as a tuple.
        """
        units = 'b'
        length = len(f"{size:.0f}")
        if length <= 3:
            val = str(size)
        elif length <= 6:
            val = f"{size / 10e+2:.1f}"
            units = 'kb'
        elif length <= 9:
            val = f"{size / 10e+5:.1f}"
            units = 'mb'
        elif length <= 12:
            val = f"{size / 10e+8:.1f}"
            units = 'gb'
        else:
            val = f"{size / 10e+11:.1f}"
            units = 'tb'
        return (val, units)

    def append_to_path_back(self) -> None:
        """track file change history"""
        if len(self.path_back) >= self.path_back_max_len:
            self.path_back.pop(0)
        self.path_back.append(self.current_path)

    def append_to_path_ahead(self) -> None:
        """track file change history"""
        if len(self.path_ahead) >= self.path_ahead_max_len:
            self.path_ahead.pop(0)
        self.path_ahead.append(self.current_path)


    def get_path_current(self) -> str:
        """get the current path"""
        return self.current_path

    def cd(self, path: str) -> None:
        """move to a new working directory determined by path"""
        if os.path.isdir(path):
            self.append_to_path_back()
            self.path_ahead.clear()
            self.current_path = path
            self.__update_file_list()

    def cd_ahead(self):
        """move forward to directory in the file change history"""
        if len(self.path_ahead) > 0:
            path = self.path_ahead.pop()
            if os.path.isdir(path):
                self.append_to_path_back()
                self.current_path = path
                self.__update_file_list()
            else:
                self.path_ahead.append(path)

    def cd_up(self, path: str) -> None:
        """move up one level in the directory tree"""
        if os.path.isdir(path):
            self.append_to_path_back()
            self.cd(os.path.split(self.get_path_current())[0])
            self.__update_file_list()

    def cd_previous(self) -> None:
        """move back to directory in the file change history"""
        if len(self.path_back) > 0:
            path = self.path_back.pop()
            if os.path.isdir(path):
                self.append_to_path_ahead()
                self.current_path = path
                self.__update_file_list()
            else:
                self.path_back.append(path)

    def is_hidden_file(self, file_name: str) -> bool:
        """determine if a file is a hidden file"""
        valid = re.compile(r"^[\.]")
        if valid.match(file_name):
            return True
        return False


class FileMgrDBI:
    """Adapter to help Files interface with book_ease.db"""

    def __init__(self) -> None:
        self.settings_string = book_ease_tables.SettingsString()

    def get_library_path(self) -> str | None:
        """get the saved path to the root directory of the book library"""
        with book_ease_tables.DB_CONNECTION_MANAGER.query() as con:
            library_path_list = self.settings_string.get(con, 'Files', 'library_path')
        return library_path_list[0]['value'] if library_path_list else None

    def set_library_path(self, library_path: str) -> None:
        """
        Save the path to the root directory of the book library
        Not yet Implemented.
        """
        pass
