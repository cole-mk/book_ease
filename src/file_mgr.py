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

from __future__ import annotations
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Literal
from typing import List
from typing import TYPE_CHECKING
from typing_extensions import Self
import gi
import book_ease_tables
import signal_
from gui.gtk import file_mgr_view
if TYPE_CHECKING:
    gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
    from gi.repository import Gtk


class FileList:
    """Wrapper for os.DirEntry objects created by os.scandir()"""

    def __init__(self, parent_dir: Path) -> None:
        if not parent_dir.is_dir():
            raise ValueError("dir_path must be a directory.")
        self.parent_dir = parent_dir

    class FileListIterator:
        """Iterate outer FileList and provide access to each file's attributes"""
        dot_file_regex = re.compile(r"^[\.]")

        def __init__(self, outer) -> None:
            self.outer = outer
            self.files = os.scandir(outer.parent_dir)
            self._cur_file = None

        def __next__(self) -> Self:
            self._cur_file = next(self.files)
            return self

        @property
        def path(self) -> Path:
            """get the file refered to by self as a pathlib.Path object"""
            return Path(self._cur_file)

        @property
        def name(self) -> str:
            """get the name of the file refered to by self as a string"""
            return self._cur_file.name

        @property
        def timestamp_formatted(self) -> str:
            """Get a formatted timestamp as a string"""
            return datetime.fromtimestamp(self._cur_file.stat().st_ctime).strftime("%y/%m/%d  %H:%M")

        @property
        def size_formatted(self) -> tuple[str, Literal['b', 'kb', 'mb', 'gb', 'tb']]:
            """
            convert file size to string with appropriate units
            This includes generating a units suffix thats returned with the formatted size as a tuple.
            """
            units = 'b'
            size = self._cur_file.stat().st_size
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

        def is_file(self) -> bool:
            """Determine if self refers to an actual file"""
            return self._cur_file.is_file()

        def is_dir(self) -> bool:
            """Determine if self refers to a directory"""
            return self._cur_file.is_dir()

        def is_hidden_file(self) -> bool:
            """determine if the file refered to by self is a hidden file"""
            if self.dot_file_regex.match(self._cur_file.name):
                return True
            return False

    def __iter__(self) -> FileListIterator:
        return self.FileListIterator(self)


class FileMgr():
    """class to manage the file management features of book_ease"""
    _default_library_path = Path.home()

    def __init__(self) -> None:
        self.transmitter = signal_.Signal()
        self._file_mgr_dbi = FileMgrDBI()
        self._current_path: Path = self._file_mgr_dbi.get_library_path() or self._default_library_path
        self._path_back_max_len = 10
        self._path_ahead_max_len = 10
        self._path_back: List[Path] = []
        self._path_ahead = []
        self.show_hidden_files = False
        self.sort_ignore_case = True
        self.sort_dir_first = True
        # Signals
        # Notify of file changes
        self.transmitter.add_signal('cwd_changed')

    def get_file_list(self) -> FileList:
        """retrieve self.file_list"""
        return FileList(self._current_path)

    def _append_to_path_back(self) -> None:
        """track file change history"""
        if len(self._path_back) >= self._path_back_max_len:
            self._path_back.pop(0)
        self._path_back.append(self._current_path)

    def _append_to_path_ahead(self) -> None:
        """track file change history"""
        if len(self._path_ahead) >= self._path_ahead_max_len:
            self._path_ahead.pop(0)
        self._path_ahead.append(self._current_path)


    def get_cwd(self) -> Path:
        """get the current path"""
        return self._current_path

    def cd(self, path: Path) -> None:
        """move to a new working directory determined by path"""
        if path.is_dir():
            self._append_to_path_back()
            self._path_ahead.clear()
            self._current_path = path
            self.transmitter.send('cwd_changed')

    def cd_ahead(self):
        """move forward to directory in the file change history"""
        if len(self._path_ahead) > 0:
            path = self._path_ahead.pop()
            if os.path.isdir(path):
                self._append_to_path_back()
                self._current_path = path
                self.transmitter.send('cwd_changed')
            else:
                self._path_ahead.append(path)

    def cd_up(self, path: str) -> None:
        """move up one level in the directory tree"""
        if os.path.isdir(path):
            self._append_to_path_back()
            self.cd(self.get_cwd().parent)
            #self.cd(os.path.split(self.get_cwd())[0])
            self.transmitter.send('cwd_changed')

    def cd_previous(self) -> None:
        """move back to directory in the file change history"""
        if len(self._path_back) > 0:
            path = self._path_back.pop()
            if path.is_dir():
                self._append_to_path_ahead()
                self._current_path = path
                self.transmitter.send('cwd_changed')
            else:
                self._path_back.append(path)


class FileMgrDBI:
    """Adapter to help Files interface with book_ease.db"""

    def __init__(self) -> None:
        self.settings_string = book_ease_tables.SettingsString()

    def get_library_path(self) -> Path | None:
        """get the saved path to the root directory of the book library"""
        with book_ease_tables.DB_CONNECTION_MANAGER.query() as con:
            library_path_list = self.settings_string.get(con, 'Files', 'library_path')
        return Path(library_path_list[0]['value']) if library_path_list else None

    def set_library_path(self, library_path: Path) -> None:
        """
        Save the path to the root directory of the book library
        Not yet Implemented.
        """


class FileMgrC:
    """Instantate the components of the file manager system."""
    def __init__(self, builder: Gtk.Builder, file_mgr_view_name: str) -> None:
        self.file_mgr = FileMgr()
        self.file_mgr_view = file_mgr_view.FileMgrView(builder, file_mgr_view_name, self.file_mgr)
