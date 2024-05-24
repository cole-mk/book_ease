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

import os
import gi

gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
from gi.repository import Gtk, Gdk
import book_ease_tables
import file_mgr


class FileMgrView:
    """Display file information for files in the cwd"""

    def __init__(self, file_mgr_view: Gtk.TreeView, file_mgr_: file_mgr.FileMgr) -> None:
        self.file_mgr_view = file_mgr_view
        self.file_mgr_view.connect('destroy', self.on_destroy)
        self.file_mgr_view_dbi = FileMgrViewDBI()
        self.file_mgr = file_mgr_
        # set up the data model and containers
        self.file_lst = self.file_mgr.get_file_list()
        self.file_lst.set_sort_func(1, self.file_mgr.cmp_f_list_dir_fst, None)
        self.file_mgr_view.set_model(self.file_lst)

        # name column
        name_r_icon = Gtk.CellRendererPixbuf()
        name_r_text = Gtk.CellRendererText()
        self.name_col = Gtk.TreeViewColumn("Name")
        self.name_col.pack_start(name_r_icon, False)
        self.name_col.pack_start(name_r_text, True)
        self.name_col.add_attribute(name_r_icon, "pixbuf", 0)
        self.name_col.add_attribute(name_r_text, "text", 1)
        self.name_col.set_sort_column_id(1)
        self.name_col.set_resizable(True)
        # reset name column width to previous size iff previous size exists.
        if name_width := self.file_mgr_view_dbi.get_name_col_width():
            self.name_col.set_fixed_width(name_width)
        self.file_mgr_view.append_column(self.name_col)

        # size column
        size_r_val = Gtk.CellRendererText()
        size_r_units = Gtk.CellRendererText()
        size_col = Gtk.TreeViewColumn("Size")
        size_col.pack_start(size_r_val, False)
        size_col.pack_start(size_r_units, False)
        size_col.add_attribute(size_r_val, "text", 3)
        size_col.add_attribute(size_r_units, "text", 4)
        self.file_mgr_view.append_column(size_col)

        # file creation time column
        c_time_r = Gtk.CellRendererText()
        c_time_col = Gtk.TreeViewColumn("Modified")
        c_time_col.pack_start(c_time_r, True)
        c_time_col.add_attribute(c_time_r, "text", 5)
        self.file_mgr_view.append_column(c_time_col)

        #signals
        self.file_mgr_view.connect('row-activated', self.row_activated)
        self.file_mgr_view.connect('button-release-event', self.on_button_release )

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
                self.file_mgr.cd_previous()
                #print('back button clicked')
            elif event.get_button()[1] == 9:
                self.file_mgr.cd_ahead()
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
            # cd into selected dir
            new_path = os.path.join(self.file_mgr.get_path_current(), value)
            self.file_mgr.cd(new_path)

    def on_destroy(self, _: Gtk.TreeView):
        """save the gui's state"""
        self.file_mgr_view_dbi.save_name_col_width(self.name_col.get_width())


class FileMgrViewDBI:
    """Class to help FilesView interface with a database"""

    def __init__(self):
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

    def save_name_col_width(self, width: int):
        """Save the width of the name column in the FilesView:TreeView to a database."""
        with book_ease_tables.DB_CONNECTION_MANAGER.query() as con:
            if id_ := self.ids['name_col_width']:
                self.settings_numeric.update_value_by_id(con, id_, width)
            else:
                self.settings_numeric.set(con, 'FilesView', 'name_col_width', width)
