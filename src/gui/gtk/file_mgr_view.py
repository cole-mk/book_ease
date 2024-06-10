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
from pathlib import Path
import logging
import gi
gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
from gi.repository import Gtk, Gdk
from gi.repository.GdkPixbuf import Pixbuf
import signal_
import book_ease_tables
import book
# pylint: disable=no-name-in-module
# pylint seems to think that gui.gtk.file_mgr_view_templates is a module. I don't know why.
from gui.gtk.file_mgr_view_templates import file_mgr_view_templates as fmvt
# pylint: enable=no-name-in-module
if TYPE_CHECKING:
    import file_mgr

#logger = logging.getLogger()


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
        name_r_text = Gtk.CellRendererText()
        self._name_col = Gtk.TreeViewColumn("Name")
        self._name_col.pack_start(name_r_icon, False)
        self._name_col.pack_start(name_r_text, True)
        self._name_col.add_attribute(name_r_icon, "pixbuf", self.name_icon['column'])
        self._name_col.add_attribute(name_r_text, "text", self.name_text['column'])
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

        # popup menu signals
        file_mgr_view_name.new_folder_menu_item.connect('button-release-event', self.on_ctrl_menu_released)
        file_mgr_view_name.copy_menu_item.connect('button-release-event', self.on_ctrl_menu_released)
        file_mgr_view_name.paste_menu_item.connect('button-release-event', self.on_ctrl_menu_released)
        file_mgr_view_name.cut_menu_item.connect('button-release-event', self.on_ctrl_menu_released)
        file_mgr_view_name.delete_menu_item.connect('button-release-event', self.on_ctrl_menu_released)
        file_mgr_view_name.rename_menu_item.connect('button-release-event', self.on_ctrl_menu_released)
        file_mgr_view_name.properties_menu_item.connect('button-release-event', self.on_ctrl_menu_released)

        self.menu_items_requiring_selection = [
            file_mgr_view_name.copy_menu_item,
            file_mgr_view_name.paste_menu_item,
            file_mgr_view_name.cut_menu_item,
            file_mgr_view_name.delete_menu_item,
            file_mgr_view_name.rename_menu_item,
            file_mgr_view_name.properties_menu_item
        ]

        #signals
        self._file_mgr_view_gtk.connect('row-activated', self.row_activated)
        self._file_mgr_view_gtk.connect('button-release-event', self.on_button_release)
        self._file_mgr_view_gtk.connect('button-press-event', self.on_button_press)
        self._file_mgr.transmitter.connect('cwd_changed', self.populate_file_list)
        signal_.GLOBAL_TRANSMITTER.connect('dir_contents_updated', self.cb_dir_contents_updated)
        self.populate_file_list()

    def on_ctrl_menu_released(self, menu_item: Gtk.MenuItem, _: Gdk.EventButton, __: any=None) -> None:
        """Handle the response of the file manager control popup."""

        match menu_item:
            case self._file_mgr_view_name.new_folder_menu_item:
                self._create_new_folder()

            case self._file_mgr_view_name.copy_menu_item:
                print('on_ctrl_menu_released _copy_menu_item')
            case self._file_mgr_view_name.paste_menu_item:
                print('on_ctrl_menu_released _paste_menu_item')
            case self._file_mgr_view_name.cut_menu_item:
                print('on_ctrl_menu_released _cut_menu_item')
            case self._file_mgr_view_name.properties_menu_item:
                print('on_ctrl_menu_released _properties_menu_item')
            case self._file_mgr_view_name.delete_menu_item:
                self._delete_selected_files()

            case self._file_mgr_view_name.rename_menu_item:
                print('on_ctrl_menu_released _rename_menu_item')

    def on_button_press(self, _: Gtk.TreeView, event: Gdk.EventButton) -> None:
        """
        Handle callbacks for a button press on the FileView by any mouse button.

        Currently its only action is to call a context menu when the FileView is right clicked.
        Note: It does do some work to manage the selections in the treeview to achieve this.
        """
        if event.get_button()[0] is True:
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
                    # enable/disable relevant parts of the popup menu based
                    # on if there is a selection in the treeview.
                    enable = False if path is None else True
                    for menu_item in self.menu_items_requiring_selection:
                        menu_item.set_sensitive(enable)

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
        # populate liststore
        for i in files:
            if not i.is_file() and not i.is_dir():
                # ignore things like broken symlinks
                continue
            if not self._file_mgr.show_hidden_files and i.is_hidden_file():
                continue

            timestamp_formatted = i.timestamp_formatted
            size_f, units = i.size_formatted
            # set correct icon
            icon = Gtk.IconTheme.get_default().load_icon('multimedia-player', 24, 0)
            if i.is_dir():
                icon = Gtk.IconTheme.get_default().load_icon('folder', 24, 0)
            self._file_lst.append((icon, i.name, i.is_dir(), size_f, units, str(timestamp_formatted)))

    def _delete_selected_files(self):
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
            errors = self._file_mgr.delete(*file_list,
                                            move_to_trash=verify_dialog.trash,
                                            recursive=verify_dialog.recursive)
            if errors:
                fmvt.ErrorDialog("Failed to delete the following files", errors)
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
