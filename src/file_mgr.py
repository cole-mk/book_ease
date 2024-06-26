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
import os
from pathlib import Path
from shutil import rmtree
from dataclasses import dataclass
from typing import List
from typing import TYPE_CHECKING
from typing_extensions import Self
import gi
from gi.repository import Gio, GLib
import book_ease_tables
import signal_
from gui.gtk import file_mgr_view
# pylint: disable=no-name-in-module
# pylint seems to think that gui.gtk.file_mgr_view_templates is a module. I don't know why.
from gui.gtk.file_mgr_view_templates import file_mgr_view_templates as fmvt
# pylint: enable=no-name-in-module
import book_mark
from book_ease_path import BEPath
if TYPE_CHECKING:
    gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
    from gi.repository import Gtk


class FileList:
    """
    Iterable of all of the files residing inside parent_dir
    The iterator provides BEPath objects, wrappers for pathlib.Path.
    """

    def __init__(self, parent_dir: Path) -> None:
        if not parent_dir.is_dir():
            raise ValueError("dir_path must be a directory.")
        self.parent_dir = parent_dir
        self._files = [BEPath(file) for file in os.scandir(self.parent_dir)]
        self._iter = None
        self._cur_file = None

    def __iter__(self) -> Self:
        self._iter = iter(self._files)
        return self

    def __next__(self):
        return next(self._iter)

    def has_media_file(self) -> bool:
        """Determine if any of the files in this FileList are media files."""
        for file in self:
            if file.is_media_file():
                return True
        return False


@dataclass
class FileError:
    """
    Container for file error information for sending out to the
    upper application layers for user display.
    """
    file: Path
    err: Exception

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
        else:
            raise RuntimeError("path is not a directory", path)

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

    def cd_up(self) -> None:
        """move up one level in the directory tree"""
        self._append_to_path_back()
        self._path_ahead.clear()
        self.cd(self.get_cwd().parent)
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

    def rename(self, old_path: Path, new_path: Path) -> None | FileError:
        """
        Rename file from 'old_path' to 'new_path'.
        """
        try:
            if new_path.exists():
                raise FileExistsError('File already exists.')
            old_path.rename(new_path)
            signal_.GLOBAL_TRANSMITTER.send('dir_contents_updated', self._current_path)
        except FileNotFoundError as e:
            # Another process likely deleted the file during editing. Inform the
            # user and the application that the directory contents have changed.
            signal_.GLOBAL_TRANSMITTER.send('dir_contents_updated', self._current_path)
            return FileError(new_path, e)
        except FileExistsError as e:
            return FileError(new_path, e)

    def mkdir(self, new_dir_abs_path: Path) -> None | FileError:
        """
        Create a new directory at the location described by new_dir_abs_path.

        Returns an error describing the failed directory creation. Currently
        it only provides information for FileExistsError. No other exceptions
        are caught.
        """
        try:
            new_dir_abs_path.mkdir()
            signal_.GLOBAL_TRANSMITTER.send('dir_contents_updated', self._current_path)
        except  FileExistsError as e:
            return FileError(new_dir_abs_path, e)

    def delete(self, *files: Path | list[Path], move_to_trash=False, recursive=False) -> list[Path]:
        """
        Delete files or send them to the trash.
        Returns a list of failed deletions.
        """
        if move_to_trash:
            return self._trash(*files, recursive=recursive)
        else:
            return self._delete(*files, recursive=recursive)

    def _trash(self, *files: Path | list[Path], recursive=False) -> list[FileError]:
        """
        Send files to the trash.
        Send dir_contents_updated signal upon deletion of all files.

        Return a list of FileError describing any files that failed
        to be moved to the trash.
        """
        failed_deletions = []
        for file in files:
            try:
                if file.is_dir() and not recursive and os.listdir():
                    raise OSError(f"[Errno 39] Directory not empty: {file}")
                fil: Gio.File  = Gio.File.new_for_path(str(file.absolute()))
                fil.trash(None)
            except GLib.Error as e:
                failed_deletions.append(FileError(file, e))
            except OSError as e:
                failed_deletions.append(FileError(file, e))

        signal_.GLOBAL_TRANSMITTER.send('dir_contents_updated', self._current_path)
        return failed_deletions

    def _delete(self, *files: Path | list[Path], recursive=False) -> list[Path]:
        """
        Delete files
        Delete file recursively if one of the files is a directory and recursive is set to True.
            default: False

        Send dir_contents_updated signal upon deletion of all files.
        Return a list of any files that failed to be deleted.
        """
        failed_deletions = []
        for file in files:
            try:
                if file.is_file():
                    file.unlink()
                elif file.is_dir():
                    if recursive:
                        rmtree(file)
                    else:
                        file.rmdir()
            # pylint: disable=broad-exception-caught
            # Disabled because it doesn't matter why it failed, only that
            # the failure can be reported to the user in the gui.
            except Exception as e:
                failed_deletions.append(FileError(file, e))

        signal_.GLOBAL_TRANSMITTER.send('dir_contents_updated', self._current_path)
        return failed_deletions


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
    def __init__(self,
                 file_manager_pane: Gtk.Paned,
                 file_mgr_view_name: str) -> None:

        self.file_mgr = FileMgr()
        self.file_mgr_view_gtk = fmvt.FileManagerViewOuterT()
        self.file_view_gtk = file_mgr_view.FileView(self.file_mgr_view_gtk, self.file_mgr)

        self.book_mark = book_mark.BookMark(self.file_mgr_view_gtk.book_mark_treeview_gtk, self.file_mgr)
        self.navigation = file_mgr_view.NavigationView(self.file_mgr_view_gtk, self.file_mgr)

        if file_mgr_view_name == 'files_1':
            file_manager_pane.pack1(self.file_mgr_view_gtk, True, False)
        elif file_mgr_view_name == 'files_2':
            file_manager_pane.pack2(self.file_mgr_view_gtk, True, False)
        else:
            raise RuntimeError("file_mgr_view didn't didn't match any Gtk object")
        self.playlist_opener = file_mgr_view.PlaylistOpenerView(self.file_mgr, self.file_mgr_view_gtk)
        file_manager_pane.show_all()
        self.file_mgr_view_gtk.show_all()
