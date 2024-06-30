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
import shutil
import errno
from pathlib import Path
from dataclasses import dataclass
import threading
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
import glib_utils
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
    _default_max_depth = 8

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

    def move(self,
             src_file: Path,
             dest_file: Path,
             cancel_event: threading.Event | None = None) -> list[FileError]:
        """
        File move operation. Move source file to destination file.
        """
        error_list = []
        if not src_file.exists():
            error_list.append(FileError(src_file, "Source file does not exist!"))

        if dest_file.exists():
            error_list.append(FileError(src_file, f"Destination file already exists, {dest_file}"))

        if not error_list:
            try:
                src_file.rename(dest_file)
            except IOError as e:
                if e.errno == errno.EXDEV:
                    # errno.EXDEV == Cross-device link
                    # perform the copy instead.
                    copy_errs = self.copy(src_file, dest_file, cancel_event)
                    error_list.extend(copy_errs)
                    if not error_list:
                        delete_errors = self.delete(src_file, cancel_event=cancel_event)
                        error_list.extend(delete_errors)
                else:
                    error_list.append(FileError(src_file, e))
        return error_list

    def delete(self,
               *files: Path | list[Path],
               move_to_trash=False,
               recursive=False,
               cancel_event: threading.Event|None=None) -> list[Path]:
        """
        Delete files or send them to the trash.
        Returns a list of failed deletions.

        threadsafe
        """
        if move_to_trash:
            return self._trash(*files, recursive=recursive, cancel_event=cancel_event)
        else:
            return self._delete(*files, recursive=recursive, cancel_event=cancel_event)

    def copy(self,
             src_file: Path,
             dest_file: Path,
             cancel_event: threading.Event|None=None,
             depth: int=0) -> list[FileError]:
        """
        * Write the contents of src_file to dest_file.

        * Threadsafe

        * Note: All exceptions are caught and returned
        """
        # pylint: disable=broad-exception-caught
        # Disabled because it doesn't matter why it failed, only that
        # the failure can be reported to the user in the gui.
        error_list = []
        if cancel_event.is_set():
            error_list.append(FileError(src_file, f"Failed to Copy to {dest_file}. Cancelled."))
            return error_list

        if depth >= self._default_max_depth:
            error_list.append(FileError(src_file, f"Failed to copy to {dest_file} excedded max depth."))
            return error_list

        elif not src_file.exists():
            error_list.append(FileError(src_file, "Source file does not exist!"))
            return error_list

        elif src_file.is_symlink():
            # This needs to be before the test for is_dir because symlinks to
            # directories also pass the test for is_dir.
            try:
                dest_file.symlink_to(src_file.readlink())
            except Exception as e:
                error_list.append(FileError(src_file, e))

        elif src_file.is_dir():
            if not dest_file.exists():
                try:
                    dest_file.mkdir()
                    shutil.copystat(src_file, dest_file)
                except Exception as e:
                    error_list.append(FileError(src_file, e))

            if dest_file.is_dir():
                # Recursively copy the contents of src_file (directory) into dest_file (directory).
                # testing for same names only matters if the calls from the view get more complex.
                # Currently, the names are always the same.
                if src_file.name == dest_file.name:
                    for fil in os.listdir(src_file):
                        new_src_file = Path(src_file, fil)
                        new_dest_file = Path(dest_file, fil)
                        error_list.extend(self.copy(new_src_file, new_dest_file, cancel_event, depth=depth+1))
                else:
                    # Call self.copy inside the dest_file directory.
                    new_dest_file = Path(dest_file, src_file.name)
                    error_list.extend(self.copy(src_file, new_dest_file, cancel_event, depth=depth+1))
            else:
                # dest_file exists and is not a directory.
                error_list.append(FileError(src_file, f"Failed to copy to {dest_file}: Exists."))
                return error_list

        elif dest_file.exists():
            # dest_file is not a directory and should not be overwritten.
            error_list.append(FileError(src_file, f"Destination file already exists, {dest_file}"))
            return error_list

        elif src_file.is_fifo():
            try:
                os.mkfifo(dest_file)
            except Exception as e:
                error_list.append(FileError(src_file, e))

        elif src_file.is_mount():
            error_list.append(FileError(src_file, "File is a mount point."))
            return error_list

        elif src_file.is_file():
            # Copy a regular file, while periodically checking for a cancellation event
            # and preserving metadata.
            try:
                dest_file_temp = Path(dest_file.parent.absolute(), dest_file.name + '.part')
                with open(src_file, 'rb') as i_put:
                    with open(dest_file_temp, 'wb') as o_put:
                        for byt in i_put:
                            if cancel_event is None or not cancel_event.is_set():
                                o_put.write(byt)
                            else:
                                raise glib_utils.AsyncWorkerCancelledError(f'Failed to Copy to {dest_file}. Cancelled.')
                dest_file_temp.rename(dest_file)
                shutil.copystat(src_file, dest_file)
            except Exception as e:
                error_list.append(FileError(src_file, e))
        else:
            error_list.append(FileError(dest_file, "Cannot copy files of this type."))

        glib_utils.g_idle_add_once(signal_.GLOBAL_TRANSMITTER.send, 'dir_contents_updated', dest_file.parent)
        return error_list

    def _trash(self,
               *files: Path | list[Path],
               recursive=False,
               cancel_event: threading.Event|None=None) -> list[FileError]:
        """
        Send files to the trash.
        Send dir_contents_updated signal if any files were seccessfully trashed.

        Return a list of FileError describing any files that failed
        to be moved to the trash.

        Threadsafe
        """
        failed_deletions = []
        dir_changed = False
        for file in files:
            if cancel_event.is_set():
                failed_deletions.append(FileError(file, 'Delete File to Trash Cancelled.'))
                continue
            try:
                if file.is_dir() and not recursive and os.listdir(file):
                    raise OSError(f"[Errno 39] Directory not empty: {file}")
                fil: Gio.File  = Gio.File.new_for_path(str(file.absolute()))
                fil.trash(None)
                dir_changed = True
            except GLib.Error as e:
                failed_deletions.append(FileError(file, e))
            except OSError as e:
                failed_deletions.append(FileError(file, e))
        if dir_changed:
            glib_utils.g_idle_add_once(signal_.GLOBAL_TRANSMITTER.send, 'dir_contents_updated', self._current_path)
        return failed_deletions

    def _delete(self,
                *files: Path | list[Path],
                recursive=False,
                cancel_event: threading.Event|None=None,
                depth: int = 0) -> list[Path]:
        """
        Delete files
        Delete file recursively if one of the files is a directory and recursive is set to True.
            default: False

        Send dir_contents_updated signal if any files were seccessfully deleted.
        Return a list of any files that failed to be deleted.

        threadsafe
        """
        failed_deletions = []
        if depth >= self._default_max_depth:
            for file in files:
                failed_deletions.append(FileError(file, 'Max Depth Reached.'))
            return failed_deletions

        for file in files:
            if cancel_event is not None and cancel_event.is_set():
                failed_deletions.append(FileError(file, 'Delete File Cancelled.'))
                continue
            try:
                if not file.exists():
                    failed_deletions.append(FileError(file, 'file: does not exist'))
                    continue

                if file.is_file():
                    file.unlink()

                elif file.is_dir():
                    if recursive:
                        file_list_next = []
                        for file_next in os.listdir(file):
                            file_list_next.append(Path(file, file_next))

                        if file_list_next:
                            delete_errs = self._delete(*file_list_next,
                                                       recursive=True,
                                                       cancel_event=cancel_event,
                                                       depth=depth+1)
                            failed_deletions.extend(delete_errs)
                        file.rmdir()
            # pylint: disable=broad-exception-caught
            # Disabled because it doesn't matter why it failed, only that
            # the failure can be reported to the user in the gui.
            except Exception as e:
                failed_deletions.append(FileError(file, e))

        glib_utils.g_idle_add_once(signal_.GLOBAL_TRANSMITTER.send, 'dir_contents_updated', self._current_path)
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
