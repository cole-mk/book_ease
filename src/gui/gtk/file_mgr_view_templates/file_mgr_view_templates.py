# -*- coding: utf-8 -*-
#
#  file_mgr_view_dialogs.py
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
This module contains all of the dialogs used by the file_mgr_view module.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path
import gi
gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
from gi.repository import Gtk
if TYPE_CHECKING:
    import file_mgr


@Gtk.Template(filename='gui/gtk/file_mgr_view_templates/new_dir_dialog.ui')
class NewDirDialog(Gtk.Dialog):
    """Entry dialog to get the name of the new directory from the user."""
    # pylint:disable=no-member
    # pylint erroneously thinks that template members are of type Child.

    __gtype_name__ = 'NewDirDialog'
    _entry: Gtk.Entry = Gtk.Template.Child('entry')

    class ResponseType:
        """Named responses for the dialog buttons"""
        AND_OPEN = 1

    def get_entry_text(self) -> str:
        """
        Retrieve the new directory name as text from this dialog's
        entry widget.
        """
        return self._entry.get_text()

    def set_entry_text(self, text: str) -> None:
        """Set the text in the new directory entry widget."""
        self._entry.set_text(text)


@Gtk.Template(filename='gui/gtk/file_mgr_view_templates/error_dialog.ui')
class _ErrorDialog(Gtk.MessageDialog):
    """
    Error dialog to report which files failed to be manipulated.
    Implements a Gtk.MessagDialog
    """
    __gtype_name__ = 'ErrorDialog'
    error_description_box: Gtk.Box = Gtk.Template.Child('error_description_box')


class ErrorDialog:
    """
    Error dialog to report which files failed to be manipulated.
    Implements a Gtk.MessagDialog.
    """
    # pylint:disable=no-member
    # pylint erroneously thinks that template members are of type Child.

    def __init__(self, text: str, error_list: list[file_mgr.FileError]):
        # Glade thinks that the default value for 'resizable' is True,
        # so it doesn't include the flag in the .ui file unless it is False.
        self._dialog = _ErrorDialog(resizable=True, message_type=Gtk.MessageType.ERROR, text=text)
        self._add_error_list(error_list)
        self._dialog.run()
        self._dialog.destroy()

    def _add_error_list(self, errors: list[file_mgr.FileError]):
        """Add an error message to the dialog."""
        for error in errors:
            error_label = Gtk.Label(
                'File: ' + str(error.file) + '\nError: ' + str(error.err), selectable=True
            )
            error_label.set_alignment(xalign=0, yalign=0.5)
            self._dialog.error_description_box.pack_start(error_label, expand=False, fill=False, padding=6)
        self._dialog.error_description_box.show_all()


@Gtk.Template(filename='gui/gtk/file_mgr_view_templates/delete_files_dialog.ui')
class DeleteFilesDialog(Gtk.Dialog):
    """
    Verify that the user wants to delete the selected files.
    Determine of the user wants to delete the files or move them to the trash.
    """
    # pylint:disable=no-member
    # pylint erroneously thinks that template members are of type Child.
    __gtype_name__ = 'DeleteFilesDialog'
    _move_to_trash: Gtk.CheckButton = Gtk.Template.Child('move_to_trash')
    _recursive: Gtk.CheckButton = Gtk.Template.Child('recursive')
    _delete_items_box: Gtk.Box = Gtk.Template.Child('delete_items_box')
    _scrolled_window: Gtk.ScrolledWindow = Gtk.Template.Child('scrolled_window')

    def add_files(self, *files: Path):
        """Add files that are to be deleted to the dialog for user examination."""
        for fil in files:
            label = Gtk.Label(fil.name)
            self._delete_items_box.pack_start(label, expand=False, fill=False, padding=2)
            label.set_alignment(xalign=0, yalign=0.5)
        self._delete_items_box.show_all()

    @property
    def trash(self) -> bool:
        """Get the value of the move to trash check box."""
        return self._move_to_trash.get_active()

    @property
    def recursive(self) -> bool:
        """Return the value of the "recursive" check button."""
        return self._recursive.get_active()


@Gtk.Template(filename='gui/gtk/file_mgr_view_templates/file_mgr.ui')
class FileManagerViewOuterT(Gtk.Box):
    """The file manager view"""
    __gtype_name__ = 'FileManagerViewOuter'
    file_view_treeview_gtk: Gtk.TreeView = Gtk.Template.Child('file_view_treeview')
    book_mark_treeview_gtk: Gtk.TreeView = Gtk.Template.Child('book_mark_treeview')
    navigation_box: Gtk.Box = Gtk.Template.Child('navigation_box')
    up_button: Gtk.Button = Gtk.Template.Child('up_button')
    forward_button: Gtk.Button = Gtk.Template.Child('forward_button')
    backward_button: Gtk.Button = Gtk.Template.Child('backward_button')
    path_entry: Gtk.Entry = Gtk.Template.Child('path_entry')
    has_playlist_combo: Gtk.ComboBox = Gtk.Template.Child('has_playlist_combo')
    open_playlist_btn: Gtk.Button = Gtk.Template.Child('open_playlist_btn')
    create_playlist_btn: Gtk.Button = Gtk.Template.Child('create_playlist_btn')
    playlist_opener_box: Gtk.Button = Gtk.Template.Child('playlist_opener_box')
    open_playlist_box: Gtk.Button = Gtk.Template.Child('open_playlist_box')

    ctrl_popup_menu: Gtk.Menu = Gtk.Template.Child('ctrl_popup_menu')
    new_folder_menu_item: Gtk.ImageMenuItem = Gtk.Template.Child('new_folder_menu_item')
    copy_menu_item: Gtk.ImageMenuItem = Gtk.Template.Child('copy_menu_item')
    paste_menu_item: Gtk.ImageMenuItem = Gtk.Template.Child('paste_menu_item')
    cut_menu_item: Gtk.ImageMenuItem = Gtk.Template.Child('cut_menu_item')
    delete_menu_item: Gtk.ImageMenuItem = Gtk.Template.Child('delete_menu_item')
    rename_menu_item: Gtk.ImageMenuItem = Gtk.Template.Child('rename_menu_item')
    properties_menu_item: Gtk.ImageMenuItem = Gtk.Template.Child('properties_menu_item')
