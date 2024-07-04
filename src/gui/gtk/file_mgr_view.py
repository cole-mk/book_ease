#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  file_mgr_view.py
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
This module is the frontend of a Lightweight filemanager for Book Ease's use.
It supports the following basic features:
Copy, Move, Delete, Rename
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Literal
from typing import Callable
from pathlib import Path
import logging
from dataclasses import dataclass
import gi
gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
from gi.repository import Gtk, Gdk
from gi.repository.GdkPixbuf import Pixbuf
import signal_
import book_ease_tables
import book
import glib_utils
from book_ease_path import BEPath
# pylint: disable=no-name-in-module
# pylint seems to think that gui.gtk.file_mgr_view_templates is a module. I don't know why.
from gui.gtk.file_mgr_view_templates import file_mgr_view_templates as fmvt
# pylint: enable=no-name-in-module
if TYPE_CHECKING:
    import file_mgr
    import threading

#logger = logging.getLogger()

@dataclass
class FileMgrClipData:
    """
    Clipboard data container.

    copy_paths: The path(s) to the original copied or cut file.

    on_pasted_callback: Required callback for copy/cut sources to be notified when
        a paste is done. It is intended for this to be assigned when creating a
        copy/paste source. The actual copying/moving/etc of files should be done here.
        The callback signature should be callback(clipboard_data: FileMgrClipData).

    paste_target: Path to the directory where the paste operation will be performed.
    """
    copy_paths: tuple[Path]
    on_pasted_callback: Callable | None = None
    paste_target: Path | None = None


class FileMgrClipboard:
    """
    Clipboard to help with copy/cut/paste files.

    Copy/Cut sources call set_data(on_pasted_callback, copied_paths) to copy a file or
    files to this clipboard.

    In addition set_data() copies the absolute file path to the main Gtk.Cilpboard
    as a string.

    Paste destinations can call paste(paste_target) to post a copy/paste destination
    to the clipboard allowing the source to complete the copy/paste operation via callback.

    For example, in the case of a cut operation, this allows the cut source to either move
    the copied_files to target or copy the copied_files to the target and then delete the
    originals.

    Note: Cut/Paste can only be pasted once. Copy/Paste can be pasted repeatedly until
    new clipboard contents are copied.
    """

    def __init__(self):
        self._clipboard_data: FileMgrClipData|None = None
        self._clipboard: Gtk.Clipboard  = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

    def _copy_data_to_gtk_clipboard(self):
        """
        Generate a string representation of the Paths in self._path
        and copy them to the main Gtk.Clipboard.
        """
        path_string = ''
        for i, pth in enumerate(self._clipboard_data.copy_paths):
            path_string += str(pth.absolute())
            if i < len(self._clipboard_data.copy_paths) - 1:
                path_string += ', '
        self._clipboard.set_text(path_string, -1)

    def set_data(self,
                 on_pasted_callback: Callable[[list[Path]], None],
                 *copied_paths: Path) -> None:
        """
        Save path to clipboard.

        on_pasted_callback: Callback triggered by a paste operation. The
        caller should perform the actual file operation here. The callback signature
        should be `callback(clipboard_data: FileMgrClipData)`.

        copied_paths: Absolute paths of one or more files to be copied.
        """
        self._clipboard_data = FileMgrClipData((*copied_paths,), on_pasted_callback)
        self._copy_data_to_gtk_clipboard()

    def paste(self, target: Path):
        """
        Post a paste target to the clipboard, allowing the copy/cut creator to
        complete the operation.
        """
        self._clipboard_data.paste_target = target
        self._clipboard_data.on_pasted_callback(self._clipboard_data)


file_mgr_clipboard = FileMgrClipboard()
"""The global instance of FileMgrClipboard"""


class PlaylistOpenerView:
    """Display playlist opener widgets

    class NewBookOpenerV:
    The Gtk view for the ExistingBookOpener
    """

    def __init__(self, file_manager: file_mgr.FileMgr, file_mgr_view_gtk: fmvt.FileManagerViewOuterT):
        self.file_manager = file_manager
        self.file_mgr_view_gtk = file_mgr_view_gtk

        self.has_playlist_combo = self.file_mgr_view_gtk.has_playlist_combo
        self.open_playlist_btn = self.file_mgr_view_gtk.open_playlist_btn
        self.open_playlist_btn.connect('button-release-event', self.on_button_release)

        self.create_playlist_btn = self.file_mgr_view_gtk.create_playlist_btn
        self.create_playlist_btn.set_no_show_all(True)

        self.open_playlist_box = self.file_mgr_view_gtk.open_playlist_box
        self.open_playlist_box.set_no_show_all(True)

        self.playlist_dbi = book.PlaylistDBI()
        self.existing_playlist_opener_m = ExistingPlaylistOpenerM()

        self.has_playlist_combo.set_model(self.existing_playlist_opener_m.get_model())

        renderer_text = Gtk.CellRendererText()
        renderer_text.set_property('width-chars', 10)
        renderer_text.set_property('ellipsize', gi.repository.Pango.EllipsizeMode.END)
        self.has_playlist_combo.pack_start(renderer_text, True)
        self.has_playlist_combo.add_attribute(renderer_text, "text", ExistingPlaylistOpenerM.pl_title['g_col'])

        self.create_playlist_btn.connect('button-release-event', self.on_button_release)
        self.file_manager.transmitter.connect('cwd_changed', self.update_view)
        self.file_manager.transmitter.connect('cwd_changed', self.update_book_list)
        signal_.GLOBAL_TRANSMITTER.connect('book_updated', self.update_book_list)

        self.update_book_list()
        self.update_view()

    def update_view(self):
        """
        Update the visibility of playlist opener widget.
        Set the "create" button's visibility— True if there are
        media files in the file manager's cwd.

        Set the open playlist button's and combo box's visibilites— True if there are
        any playlists associated with file manager's cwd.
        """
        f_list = self.file_manager.get_file_list()
        if f_list.has_media_file():
            self.create_playlist_btn.show()
        else:
            self.create_playlist_btn.hide()

    def on_button_release(self, btn: Gtk.Button, _: Gdk.EventButton) -> None:
        """Relay the message that the user wants to open a book."""
        if btn == self.open_playlist_btn:
            selection = self.has_playlist_combo.get_active_iter()
            book_ = self.existing_playlist_opener_m.get_row(selection)
            signal_.GLOBAL_TRANSMITTER.send('open_book', book_)
        elif btn == self.create_playlist_btn:
            signal_.GLOBAL_TRANSMITTER.send('open_new_book', self.file_manager.get_cwd())


    def update_book_list(self, *_) -> None:
        """
        Check if there are any saved Books associated with the new cwd.
        """
        cur_path = self.file_manager.get_cwd()
        playlists_in_path = self.playlist_dbi.get_by_path(book.PlaylistData(path=cur_path))
        self.existing_playlist_opener_m.update(playlists_in_path)
        if len(playlists_in_path) > 0:
            self.has_playlist_combo.set_active(0)
            self.open_playlist_box.show()
        else:
            self.open_playlist_box.hide()

    def open_book(self) -> None:
        """
        Use transmitter to broadcast the command to open a book.
        Include a PlaylistData object describing the book as an arg.
        """
        selection = self.has_playlist_combo.get_selection()
        book_ = self.existing_playlist_opener_m.get_row(selection)
        signal_.GLOBAL_TRANSMITTER.send('open_book', book_)


class ExistingPlaylistOpenerM:
    """Wrapper for the Gtk.Liststore containing the data displayed in the has_book_combo"""

    # add gui keys to helpers for accessing playlist data stored in db
    pl_id = {'col': 0, 'col_name': 'id', 'g_type': int, 'g_col': 0}
    pl_title = {'col': 1, 'col_name': 'title', 'g_type': str, 'g_col': 1}
    pl_path = {'col': 2, 'col_name': 'path', 'g_type': str, 'g_col': 2}
    pl_helper_l = [pl_id, pl_title, pl_path]
    pl_helper_l.sort(key=lambda col: col['col'])
    # extract list of g_types from self.cur_pl_helper_l that was previously sorted by col number
    # use list to initialize the model for displaying
    # all playlists associated with the current path
    # Cast to list here even though at every other place in the program that uses a liststore
    # is fine with just g_types = map(lambda x: x['g_type'], pl_helper_l)
    g_types = list(map(lambda x: x['g_type'], pl_helper_l))

    def __init__(self):
        self.model = Gtk.ListStore(*self.g_types)

    def get_row(self, row: Gtk.TreeIter) -> book.PlaylistData:
        """return a row from the model as a PlaylistData object"""
        playlist_data = book.PlaylistData()
        playlist_data.set_id(self.model.get_value(row, self.pl_id['g_col']))
        playlist_data.set_title(self.model.get_value(row, self.pl_title['g_col']))
        playlist_data.set_path(Path(self.model.get_value(row, self.pl_path['g_col'])))
        return playlist_data

    def update(self, pl_data_list: list[book.PlaylistData]):
        """Populate the model with the data in the list of PlaylistData objects."""
        self.model.clear()
        for playlist_data in pl_data_list:
            g_iter = self.model.append()
            self.model.set_value(g_iter, self.pl_id['g_col'], playlist_data.get_id())
            self.model.set_value(g_iter, self.pl_title['g_col'], playlist_data.get_title())
            self.model.set_value(g_iter, self.pl_path['g_col'], str(playlist_data.get_path().absolute()))

    def get_model(self) -> Gtk.ListStore:
        """get the Gtk.ListStore that this class encapsulates."""
        return self.model


class NavigationView:
    """Display the file navigation buttons"""
    logger = logging.getLogger(f'{__name__}::NavigationView')
    logger.addHandler(logging.NullHandler())

    def __init__(self,
                 file_manager_view: fmvt.FileManagerViewOuterT,
                 file_manager: file_mgr.FileMgr) -> None:

        self.file_manager_view = file_manager_view
        self.file_manager = file_manager
        self.file_manager.transmitter.connect('cwd_changed', self.update_path_entry)

        self.up_button = self.file_manager_view.up_button
        self.up_button.connect('clicked', self.on_button_clicked)

        self.forward_button = self.file_manager_view.forward_button
        self.forward_button.connect('clicked', self.on_button_clicked)

        self.backward_button = self.file_manager_view.backward_button
        self.backward_button.connect('clicked', self.on_button_clicked)

        self.path_entry = self.file_manager_view.path_entry
        self.path_entry.connect('activate', self.on_entry_activate)
        self.update_path_entry()

    def on_entry_activate(self, path_entry: Gtk.Entry) -> None:
        """
        cd into directory described by self.path_entry
        Callback triggered by self.path_entry 'activate' signal.
        """
        new_path = Path(path_entry.get_text()).absolute()
        try:
            self.file_manager.cd(new_path)
        except RuntimeError as e:
            if str(e) == 'path is not a directory':
                self.logger.warning("path is not a directory: %s", new_path)
            else:
                raise e

    def on_button_clicked(self, widget: Gtk.Button) -> None:
        """
        Call the file_manager directory change command corresponding
        to which navigation button was clicked.
        """
        match widget:
            case self.up_button:
                self.file_manager.cd_up()
            case self.forward_button:
                self.file_manager.cd_ahead()
            case self.backward_button:
                self.file_manager.cd_previous()

    def update_path_entry(self, *_) -> None:
        """
        Set the path entry text.
        """
        self.path_entry.set_text(str(self.file_manager.get_cwd()))


class FileView:
    """Display file information for files in the cwd"""
    name_icon = {'column': 0}
    name_text = {'column': 1}
    is_dir = {'column': 2}
    size_val = {'column': 3}
    size_units = {'column': 4}
    c_time = {'column': 5}

    def __init__(self, file_mgr_view_name: fmvt.FileManagerViewOuterT, file_mgr_: file_mgr.FileMgr) -> None:
        self._file_mgr_view_gtk = file_mgr_view_name.file_view_treeview_gtk
        sel: Gtk.TreeSelection = self._file_mgr_view_gtk.get_selection()
        sel.set_mode(Gtk.SelectionMode.MULTIPLE)
        self._file_mgr_view_gtk.connect('destroy', self.on_destroy)
        self._file_mgr_view_dbi = FileMgrViewDBI()
        self._file_mgr = file_mgr_

        # set up the data model and containers
        self._file_lst = Gtk.ListStore(Pixbuf, str, bool, str, str, str)
        self._file_lst.set_sort_func(1, self.cmp_file_list, None)
        self._file_mgr_view_gtk.set_model(self._file_lst)

        # name column
        name_r_icon = Gtk.CellRendererPixbuf()
        self.name_r_text = Gtk.CellRendererText()
        self._name_col = Gtk.TreeViewColumn("Name")
        self._name_col.pack_start(name_r_icon, False)
        self._name_col.pack_start(self.name_r_text, True)
        self._name_col.add_attribute(name_r_icon, "pixbuf", self.name_icon['column'])
        self._name_col.add_attribute(self.name_r_text, "text", self.name_text['column'])
        self._name_col.set_sort_column_id(1)
        self._name_col.set_resizable(True)
        # reset name column width to previous size iff previous size exists.
        if name_width := self._file_mgr_view_dbi.get_name_col_width():
            self._name_col.set_fixed_width(name_width)
        self._file_mgr_view_gtk.append_column(self._name_col)

        # size column
        size_r_val = Gtk.CellRendererText()
        size_r_units = Gtk.CellRendererText()
        size_col = Gtk.TreeViewColumn("Size")
        size_col.pack_start(size_r_val, False)
        size_col.pack_start(size_r_units, False)
        size_col.add_attribute(size_r_val, "text", self.size_val['column'])
        size_col.add_attribute(size_r_units, "text", self.size_units['column'])
        self._file_mgr_view_gtk.append_column(size_col)

        # file creation time column
        c_time_r = Gtk.CellRendererText()
        c_time_col = Gtk.TreeViewColumn("Modified")
        c_time_col.pack_start(c_time_r, True)
        c_time_col.add_attribute(c_time_r, "text", self.c_time['column'])
        self._file_mgr_view_gtk.append_column(c_time_col)

        # right click popup menu widgets
        self._ctrl_popup_menu = file_mgr_view_name.ctrl_popup_menu
        self._new_folder_menu_item = file_mgr_view_name.new_folder_menu_item
        self._copy_menu_item = file_mgr_view_name.copy_menu_item
        self._paste_menu_item = file_mgr_view_name.paste_menu_item
        self._cut_menu_item  = file_mgr_view_name.cut_menu_item
        self._properties_menu_item  = file_mgr_view_name.properties_menu_item
        self._delete_menu_item  = file_mgr_view_name.delete_menu_item
        self._rename_menu_item  = file_mgr_view_name.rename_menu_item
        self._file_mgr_view_name = file_mgr_view_name

        self.hidden_file_manual_toggle_active = False
        self.show_hidden_files = False
        self.show_audio_only = False

        # popup menu signals
        file_mgr_view_name.new_folder_menu_item.connect('button-release-event', self.on_ctrl_menu_released)
        file_mgr_view_name.copy_menu_item.connect('button-release-event', self.on_ctrl_menu_released)
        file_mgr_view_name.paste_menu_item.connect('button-release-event', self.on_ctrl_menu_released)
        file_mgr_view_name.cut_menu_item.connect('button-release-event', self.on_ctrl_menu_released)
        file_mgr_view_name.delete_menu_item.connect('button-release-event', self.on_ctrl_menu_released)
        file_mgr_view_name.rename_menu_item.connect('button-release-event', self.on_ctrl_menu_released)
        file_mgr_view_name.properties_menu_item.connect('button-release-event', self.on_ctrl_menu_released)
        file_mgr_view_name.hidden_files_menu_item.connect('toggled', self.on_menu_item_toggled)
        file_mgr_view_name.audio_only_menu_item.connect('toggled', self.on_menu_item_toggled)

        # Some control menu items are only valid depending
        # on how many files are selected.
        fmvn = file_mgr_view_name
        self.ctrl_menu_items = {
           fmvn.new_folder_menu_item:       {'no_sel': True,  'one_sel': True,  'multi_sel': True },
           fmvn.copy_menu_item:             {'no_sel': False, 'one_sel': True,  'multi_sel': True },
           fmvn.paste_menu_item:            {'no_sel': True,  'one_sel': True,  'multi_sel': True },
           fmvn.cut_menu_item:              {'no_sel': False, 'one_sel': True,  'multi_sel': True },
           fmvn.delete_menu_item:           {'no_sel': False, 'one_sel': True,  'multi_sel': True },
           fmvn.rename_menu_item:           {'no_sel': False, 'one_sel': True,  'multi_sel': False},
           fmvn.properties_menu_item:       {'no_sel': False, 'one_sel': True,  'multi_sel': False},
           fmvn.hidden_files_menu_item:     {'no_sel': True,  'one_sel': True,  'multi_sel': True },
           fmvn.audio_only_menu_item:       {'no_sel': True,  'one_sel': True,  'multi_sel': True },
        }

        #signals
        self.name_r_text.connect("edited", self._rename_finished)
        self.name_r_text.connect("editing-canceled", self._rename_cancelled)
        self._file_mgr_view_gtk.connect('row-activated', self.row_activated)
        self._file_mgr_view_gtk.connect('button-release-event', self.on_button_release)
        self._file_mgr_view_gtk.connect('button-press-event', self.on_button_press)
        self._file_mgr_view_gtk.connect('key-release-event', self.on_key_release)
        self._file_mgr_view_gtk.connect('key-press-event', self.on_key_press)
        self._file_mgr.transmitter.connect('cwd_changed', self.populate_file_list)
        signal_.GLOBAL_TRANSMITTER.connect('dir_contents_updated', self.cb_dir_contents_updated)

        self.populate_file_list()
        # A kludge to prevent the 'Escape' key's 'key-release-event' from unselecting
        # a file when using 'Escape' to cancel file renaming.
        self.mute_escape_key = False


    def _rename_cancelled(self, *_):
        """
        'editing-cancelled' callback
        """
        self.name_r_text.set_property("editable", False)
        self.mute_escape_key = True

    def _rename_finished(self, renderer: Gtk.CellRendererText, path: str, text: str):
        """
        Callback signaled when the 'edited' signal is sent
        upon completion of renaming a file.
        """
        renderer.set_property("editable", False)
        cwd = self._file_mgr.get_cwd()

        # Build absolute paths for the previous and new file names.
        model: Gtk.ListStore = self._file_mgr_view_gtk.get_model()
        itr = model.get_iter_from_string(path)
        val = model.get_value(itr, self.name_text['column'])
        old_name = Path(cwd, val)
        new_name = Path(cwd, text)

        # Clicking outside the cell being edited triggers this
        # signal instead of 'editing-cancelled'.
        if old_name == new_name:
            return

        if error := self._file_mgr.rename(old_name, new_name):
            fmvt.ErrorDialog(f"Failed to rename the following file:\n{old_name}", [error])

    def on_key_press(self, _: Gtk.TreeView, event: Gdk.EventKey):
        """
        'key-press-event' callback
        Using this to prevent the 'key-release-event' from unselecting a file
        when escape is used to cancel file renaming.
        """
        match Gdk.keyval_name(event.keyval):
            case "Escape":
                self.mute_escape_key = False

    def on_key_release(self, treeview: Gtk.TreeView, event: Gdk.EventKey):
        """
        Process Keyboard controls of the treeview.
        """
        sel: Gtk.TreeSelection = treeview.get_selection()
        selection_count = sel.count_selected_rows()
        msk = Gdk.ModifierType

        match Gdk.keyval_name(event.keyval):

            case ("Delete" | "BackSpace"):
                if selection_count:
                    if not event.state & (msk.SHIFT_MASK | msk.MOD1_MASK | msk.CONTROL_MASK):
                        self._delete_start()

            case "Escape":
                if selection_count and not self.mute_escape_key:
                    if not event.state & (msk.SHIFT_MASK | msk.MOD1_MASK | msk.CONTROL_MASK):
                        sel.unselect_all()

            case "F2":
                if selection_count == 1:
                    if not event.state & (msk.SHIFT_MASK | msk.MOD1_MASK | msk.CONTROL_MASK):
                        self._rename_start()

            case "h":
                if event.state & msk.CONTROL_MASK:
                    if not event.state & (msk.SHIFT_MASK | msk.MOD1_MASK):
                        self._show_hidden_files(not self.show_hidden_files)

            case "c":
                if event.state & msk.CONTROL_MASK:
                    if not event.state & (msk.SHIFT_MASK | msk.MOD1_MASK):
                        self._copy_start()

            case "v":
                if event.state & msk.CONTROL_MASK:
                    if not event.state & (msk.SHIFT_MASK | msk.MOD1_MASK):
                        self._paste()

            case "x":
                if event.state & msk.CONTROL_MASK:
                    if not event.state & (msk.SHIFT_MASK | msk.MOD1_MASK):
                        self._cut_start()

    def _rename_start(self):
        """
        Rename the file selected in the tree view.

        This method only works on one row at a time.
        The caller is responsible to ensure that only one row is selected.
        Otherwise This will only act upon the first row returned by
        Gtk.TreeSelection.get_selected_rows().
        """
        sel: Gtk.TreeSelection = self._file_mgr_view_gtk.get_selection()
        _, paths = sel.get_selected_rows()
        self.name_r_text.set_property("editable", True)
        self._file_mgr_view_gtk.set_cursor_on_cell(paths[0],
                                                   self._name_col,
                                                   self.name_r_text,
                                                   True)

    def _show_hidden_files(self, show_hidden_files: bool):
        """Display hidden files in the treeview."""
        # Maintain the state of the check menu item
        menu_item_is_active = self._file_mgr_view_name.hidden_files_menu_item.get_active()
        if menu_item_is_active ^ show_hidden_files:
            # calling set_active triggers the toggled callback
            self.hidden_file_manual_toggle_active = True
            self._file_mgr_view_name.hidden_files_menu_item.set_active(show_hidden_files)

        self.show_hidden_files = show_hidden_files
        self.populate_file_list()


    def _display_properties(self):
        """Collect file information and display it in the FilePropertiesDialog,"""

        sel = self._file_mgr_view_gtk.get_selection()
        model, paths = sel.get_selected_rows()
        itr = model.get_iter(paths[0])

        cwd = self._file_mgr.get_cwd()
        selected_file = BEPath(cwd, model.get_value(itr, self.name_text['column']))
        fpd = fmvt.FilePropertiesDialog()
        fpd.init_properties(selected_file)
        fpd.run()
        fpd.destroy()

    def _delete_finished(self, delete_errors: list[file_mgr.FileError]):
        """
        Report errors to the user upon completion of a delete operation.
        """
        if delete_errors:
            fmvt.ErrorDialog("failed to delete files", delete_errors)

    def _paste(self) -> None:
        """
        Post the cwd to the clipboard as a paste target.
        """
        file_mgr_clipboard.paste(self._file_mgr.get_cwd())

    def _copy_finished(self, paste_errors: list[file_mgr.FileError]):
        """
        Report errors to the user upon completion of a copy operation.
        """
        if paste_errors:
            fmvt.ErrorDialog("failed to paste files", paste_errors)

    def _copy_paste(self, clipboard_data: FileMgrClipData):
        """
        An on_pasted_callback registered with the file_mgr_clipboard.
        Perform the actual copy/paste operation here.
        """
        for src_file in clipboard_data.copy_paths:
            dest_file = Path(clipboard_data.paste_target, src_file.name)

            paster = glib_utils.AsyncWorker(target=self._file_mgr.copy,
                                            args=(src_file, dest_file),
                                            on_finished_cb=self._copy_finished,
                                            pass_ret_val_to_cb=True,
                                            cancellable=True)
            paster.start()

    def _copy_start(self) -> None:
        """
        Generate Path objects for each selected row in the treeview
        and post it to the clipboard.
        """
        cwd = self._file_mgr.get_cwd()
        model: Gtk.ListStore
        paths: list[Gtk.TreePath]
        sel = self._file_mgr_view_gtk.get_selection()
        model, paths = sel.get_selected_rows()

        copied_files = []
        for pth in paths:
            itr = model.get_iter(pth)
            file_name = model.get_value(itr, self.name_text['column'])
            selected_file = Path(cwd, file_name)
            copied_files.append(selected_file)
        file_mgr_clipboard.set_data(self._copy_paste, *copied_files)

    def _cut_start(self) -> None:
        """
        Generate Path objects for each selected row in the treeview
        and post it to the clipboard.

        Registers a callback that will delete the posted file(s) once the
        the data in the clipboard has been posted.
        """
        cwd = self._file_mgr.get_cwd()
        model: Gtk.ListStore
        paths: list[Gtk.TreePath]

        sel = self._file_mgr_view_gtk.get_selection()
        model, paths = sel.get_selected_rows()

        copied_files = []
        for pth in paths:
            itr = model.get_iter(pth)
            file_name = model.get_value(itr, self.name_text['column'])
            selected_file = Path(cwd, file_name)
            if selected_file.is_file() or selected_file.is_dir():
                copied_files.append(selected_file)
        file_mgr_clipboard.set_data(self._cut_paste, *copied_files)

    def _cut_finished(self, paste_errors: list[file_mgr.FileError]):
        if paste_errors:
            fmvt.ErrorDialog("failed to move files", paste_errors)

    def _cut_paste(self, clipboard_data: FileMgrClipData) -> None:
        """
        Move files that have been cut/pasted.
        """
        for src_file in clipboard_data.copy_paths:
            dest_file = Path(clipboard_data.paste_target, src_file.name)

            mover_thread = glib_utils.AsyncWorker(target=self._file_mgr.move,
                                            args=(src_file, dest_file),
                                            on_finished_cb=self._cut_finished,
                                            pass_ret_val_to_cb=True,
                                            cancellable=True)
            mover_thread.start()

    def on_menu_item_toggled(self, menu_item: Gtk.CheckMenuItem, _: any=None):
        """Callback for the CheckMenuItems from the file manager control popup."""
        match menu_item:
            case self._file_mgr_view_name.hidden_files_menu_item:
                if self.hidden_file_manual_toggle_active is True:
                    self.hidden_file_manual_toggle_active = False
                    return
                self._show_hidden_files(self._file_mgr_view_name.hidden_files_menu_item.get_active())

            case self._file_mgr_view_name.audio_only_menu_item:
                show_audio_only = self._file_mgr_view_name.audio_only_menu_item.get_active()
                self.show_audio_only = show_audio_only
                self.populate_file_list()

    def on_ctrl_menu_released(self, menu_item: Gtk.MenuItem, _: Gdk.EventButton, __: any=None) -> None:
        """Handle the response of the file manager control popup."""

        match menu_item:
            case self._file_mgr_view_name.new_folder_menu_item:
                self._create_new_folder()

            case self._file_mgr_view_name.copy_menu_item:
                self._copy_start()

            case self._file_mgr_view_name.paste_menu_item:
                self._paste()

            case self._file_mgr_view_name.cut_menu_item:
                self._cut_start()

            case self._file_mgr_view_name.properties_menu_item:
                self._display_properties()

            case self._file_mgr_view_name.delete_menu_item:
                self._delete_start()

            case self._file_mgr_view_name.rename_menu_item:
                self._rename_start()

    def on_button_press(self, _: Gtk.TreeView, event: Gdk.EventButton) -> None:
        """
        Handle callbacks for a button press on the FileView by any mouse button.

        Currently its only action is to call a context menu when the FileView is right clicked.
        Note: It does do some work to manage the selections in the treeview to achieve this.
        """
        if event.get_button()[0] is False:
            return

        # Clear selected rows if the button press was on an empty area.
        # Select row if button-press was on a row. This second part is neccessary because
        # the row doesn't actually get selected until sometime after this callback exits.
        path = self._file_mgr_view_gtk.get_path_at_pos(int(event.x), int(event.y))
        sel: Gtk.TreeSelection = self._file_mgr_view_gtk.get_selection()
        if path is None:
            sel.unselect_all()
        elif sel.count_selected_rows() == 0:
            sel.select_path(path[0])

        match event.get_button()[1]:
            case 1:  # Left button
                pass
            case 2:  # Middle button
                pass
            case 3:  # Right Button
                # Display a popup menu showing FileMgr commands.

                # enable/disable relevant parts of the popup menu based
                # upon if there is a selection in the treeview.
                if sel.count_selected_rows() == 0:
                    for menu_item, enabled in self.ctrl_menu_items.items():
                        menu_item.set_sensitive(enabled['no_sel'])
                elif sel.count_selected_rows() == 1:
                    for menu_item, enabled in self.ctrl_menu_items.items():
                        menu_item.set_sensitive(enabled['one_sel'])
                elif sel.count_selected_rows() > 1:
                    for menu_item, enabled in self.ctrl_menu_items.items():
                        menu_item.set_sensitive(enabled['multi_sel'])
                # For multiselect, reselect the rows that were unselected
                # by the right mouse button press.
                _, paths = sel.get_selected_rows()
                for pth in paths:
                    sel.select_path(pth)

                self._ctrl_popup_menu.popup_at_pointer()
            case 8:  # Back button
                pass
            case 9:  # Forward button
                pass

    def on_button_release(self, _: Gtk.TreeView, event: Gdk.EventButton) -> None:
        """
        handle mouse button release events.
        Currently:
        column resising
        forward and back buttons to move ahead or back in the file change history.
        """
        if event.get_button()[0] is True:
            if event.get_button()[1] == 1:
                pass
                #print('left button clicked')
            elif event.get_button()[1] == 2:
                pass
                #print('middle button clicked')
            elif event.get_button()[1] == 3:
                pass
                #print('right button clicked')
            elif event.get_button()[1] == 8:
                self._file_mgr.cd_previous()
                #print('back button clicked')
            elif event.get_button()[1] == 9:
                self._file_mgr.cd_ahead()
                #print('forward button clicked')

    def row_activated(self,
                      treeview: Gtk.TreeView,
                      path: Gtk.TreePath,
                      _: Gtk.TreeViewColumn) -> None:
        """
        a file was cicked in the view.
        if file is a directory then change to that directory
        """
        model = treeview.get_model()
        tree_iter = model.get_iter(path)
        value = model.get_value(tree_iter,1)
        is_dir = model.get_value(tree_iter,2)
        if is_dir:
            new_path = Path(self._file_mgr.get_cwd(), value)
            self._file_mgr.cd(new_path)

    def on_destroy(self, _: Gtk.TreeView) -> None:
        """save the gui's state"""
        self._file_mgr_view_dbi.save_name_col_width(self._name_col.get_width())

    def cmp_file_list(self, model, row1, row2, _) -> Literal[1] | Literal[-1] | Literal[0]:
        """
        compare method for sorting sort columns in the file view
        returns gt:1 lt:-1 or eq:0
        """
        sort_column, sort_order = model.get_sort_column_id()
        name1 = model.get_value(row1, sort_column)
        name2 = model.get_value(row2, sort_column)

        if self._file_mgr.sort_ignore_case:
            name1 = name1.lower()
            name2 = name2.lower()

        if self._file_mgr.sort_dir_first:
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

    def cb_dir_contents_updated(self, cwd=None) -> None:
        """Determine if files in path, directory, are suitable to be displayed and add them to the file_list"""
        if cwd == self._file_mgr.get_cwd():
            self.populate_file_list()

    def populate_file_list(self):
        """
        Get the list of files in the cwd and push them to the
        list store for display in the treeview.
        """
        files = self._file_mgr.get_file_list()
        self._file_lst.clear()

        for i in files:
            if self.show_audio_only and not i.is_media_file():
                continue

            if not self.show_hidden_files and i.is_hidden_file():
                continue

            try:
                timestamp_formatted = i.timestamp_formatted
                size_f, units = i.size_formatted
                if i.is_dir():
                    icon = Gtk.IconTheme.get_default().load_icon('folder', 24, 0)
                else:
                    icon = Gtk.IconTheme.get_default().load_icon('multimedia-player', 24, 0)

            except FileNotFoundError:
                if i.is_symlink():
                    timestamp_formatted = '00/00/00 00:00'
                    size_f = '0'
                    units = 'na'
                    icon = Gtk.IconTheme.get_default().load_icon('error', 16, 0)
                else:
                    raise

            self._file_lst.append((icon, i.name, i.is_dir(), size_f, units, str(timestamp_formatted)))

    def _delete_start(self):
        """Delete or trash selected files"""
        file_list = []
        cwd = self._file_mgr.get_cwd()

        # Get the names of the selected files.
        sel = self._file_mgr_view_gtk.get_selection()
        model, paths = sel.get_selected_rows()
        for pth in paths:
            itr = model.get_iter(pth)
            name = model.get_value(itr, self.name_text['column'])
            file_list.append(Path(cwd, name))

        # Present list to user for verification.
        verify_dialog = fmvt.DeleteFilesDialog()
        verify_dialog.add_files(*file_list)
        response = verify_dialog.run()
        verify_dialog.hide_on_delete()
        if response == Gtk.ResponseType.OK:
            sel.unselect_all()
            deleter = glib_utils.AsyncWorker(target=self._file_mgr.delete,
                                             args=(*file_list,),
                                             kwargs={'recursive':verify_dialog.recursive},
                                             on_finished_cb=self._delete_finished,
                                             pass_cancel_event_to_cb=False,
                                             pass_ret_val_to_cb=True,
                                             cancellable=True)
            deleter.start()
        verify_dialog.destroy()

    def _create_new_folder(self):
        """Get the new directry name from the user and create the folder."""
        new_dir_name = ''
        continue_dialog = True
        while continue_dialog:
            continue_dialog = False

            new_dir_dialog = fmvt.NewDirDialog()
            new_dir_dialog.set_entry_text(new_dir_name)
            response = new_dir_dialog.run()
            new_dir_dialog.hide_on_delete()

            if response != Gtk.ResponseType.CANCEL:
                new_dir_name = new_dir_dialog.get_entry_text()
                new_dir = Path(self._file_mgr.get_cwd(), new_dir_name)

                if not (error := self._file_mgr.mkdir(new_dir)):
                    if response == new_dir_dialog.ResponseType.AND_OPEN:
                        self._file_mgr.cd(new_dir)
                else:
                    fmvt.ErrorDialog('Failed to create the following file', [error])
                    continue_dialog = True
            new_dir_dialog.destroy()


class FileMgrViewDBI:
    """Class to help FilesView interface with a database"""

    def __init__(self) -> None:
        self.settings_numeric = book_ease_tables.SettingsNumeric()
        # ids dict stores attribute:rowid to ease calls to update or insert a new row in the database
        self.ids = {}

    def get_name_col_width(self) -> int | None:
        """retrieve the saved width of the name column in the FilesView treeview."""
        with book_ease_tables.DB_CONNECTION_MANAGER.query() as con:
            width_result = self.settings_numeric.get(con, 'FilesView', 'name_col_width')

        if width_result:
            width = width_result[0]['value']
            self.ids['name_col_width'] = width_result[0]['id_']
        else:
            width = None
            self.ids['name_col_width'] = None
        return width

    def save_name_col_width(self, width: int) -> None:
        """Save the width of the name column in the FilesView:TreeView to a database."""
        with book_ease_tables.DB_CONNECTION_MANAGER.query() as con:
            if id_ := self.ids['name_col_width']:
                self.settings_numeric.update_value_by_id(con, id_, width)
            else:
                self.settings_numeric.set(con, 'FilesView', 'name_col_width', width)
