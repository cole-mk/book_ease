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
import gi
gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
from gi.repository import Gtk, Gdk
from gi.repository.GdkPixbuf import Pixbuf
import book_ease_tables
if TYPE_CHECKING:
    import file_mgr

class FileMgrView:
    """Display file information for files in the cwd"""

    def __init__(self, builder: Gtk.Builder, file_mgr_view_name: str, file_mgr_: file_mgr.FileMgr) -> None:
        self._file_mgr_view_gtk: Gtk.TreeView = builder.get_object(file_mgr_view_name)
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
        self._name_col.add_attribute(name_r_icon, "pixbuf", 0)
        self._name_col.add_attribute(name_r_text, "text", 1)
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
        size_col.add_attribute(size_r_val, "text", 3)
        size_col.add_attribute(size_r_units, "text", 4)
        self._file_mgr_view_gtk.append_column(size_col)

        # file creation time column
        c_time_r = Gtk.CellRendererText()
        c_time_col = Gtk.TreeViewColumn("Modified")
        c_time_col.pack_start(c_time_r, True)
        c_time_col.add_attribute(c_time_r, "text", 5)
        self._file_mgr_view_gtk.append_column(c_time_col)

        #signals
        self._file_mgr_view_gtk.connect('row-activated', self.row_activated)
        self._file_mgr_view_gtk.connect('button-release-event', self.on_button_release)
        self._file_mgr.transmitter.connect('cwd_changed', self.populate_file_list)
        self.populate_file_list()


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

    def populate_file_list(self) -> None:
        """Determine if files in path, directory, are suitable to be displayed and add them to the file_list"""
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
