# -*- coding: utf-8 -*-
#
#  pinned_books_view.py
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
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import signal_


class PinnedBooks_V(Gtk.Box):
    """
    display the list of pinned books in a Gtk.Treeview encapsulated in a Gtk.Box
    """

    def __init__(self, pinned_cols, pinned_books_c):
        """
        initialize the Gtk.Treeview and its model for displayling the list of pinned books

        pinned_cols is pinned.PinnedCols: container for descriptions of the pinned list data
        pinned_books_c: controller for this view
        """
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=0)
        # setup the collumn information for gtk.liststore
        pinned_cols.set_playlist_id_prop('g_type', int)
        pinned_cols.set_title_prop('g_type', str)
        pinned_cols.set_path_prop('g_type', str)
        # save the args for later use
        self.pinned_cols = pinned_cols
        self.pinned_books_c = pinned_books_c

        # create the view
        self.pinned_view = Gtk.TreeView()
        self.pinned_model = self.get_pinned_list_new()
        self.pinned_view.set_model(self.pinned_model)
        # title column
        title_r = Gtk.CellRendererText()
        title_col = Gtk.TreeViewColumn("Title")
        title_col.pack_start(title_r, True)
        title_col.add_attribute(title_r, "text", self.pinned_cols.get_title_prop('col'))
        self.pinned_view.append_column(title_col)
        # path column
        path_r = Gtk.CellRendererText()
        path_col = Gtk.TreeViewColumn("Location")
        path_col.pack_start(path_r, True)
        path_col.add_attribute(path_r, "text", self.pinned_cols.get_path_prop('col'))
        self.pinned_view.append_column(path_col)
        self.pack_start(self.pinned_view, expand=True, fill=True, padding=0)
        self.load_pinned_list()


    def load_pinned_list(self):
        """
        load/reload the data in the Gtk.TreeModel (liststore)
        """
        self.pinned_model.clear()
        pinned_playlists = self.pinned_books_c.get_pinned_playlists()
        for row in pinned_playlists:
            self.pinned_model.append(tuple(row.get_data_sorted_by_prop('col')))

    def get_pinned_list_new(self):
        """
        create a Gtk.ListStore for displaying list of pinned playlists
        returns Gtk.ListStore
        """
        # init liststore with g_types by expanding the sorted col_info[*][g_types]
        pinned_list = Gtk.ListStore(*self.pinned_cols.get_prop_sorted('g_type', 'col'))
        return pinned_list

    def pin(self, playlist_data):
        """
        append a book to the list of pinned books
        """
        model = self.pinned_view.get_model()
        row = model.append(tuple(playlist_data.get_data_sorted_by_prop('col')))

    def remove(self,title, path):
        """remove a row from the list of pinned books"""
        model = self.pinned_view.get_model()
        for row in model:
            if row[self.book_reader.pinned_title['col']] == title and row[self.book_reader.pinned_path['col']] == path:
                model.remove(row.iter)


class PinnedButton_V(Gtk.Box):
    """
    display a Gtk.CheckButton to control wether or not a book is pinned
    """

    def __init__(self, playlist_id):
        """
        Initialize a Gtk.CheckButton and encapsulate it in a Gtk.Box
        playlist_id: the id of the book that this button is associated with
        """
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.signal_ = signal_.Signal_()
        self.playlist_id = playlist_id
        self.signal_.add_signal('toggled')
        self.pinned_button = Gtk.CheckButton(label='pin')
        self.pinned_button.connect('toggled', self.on_button_toggled)
        self.pack_start(self.pinned_button, expand=False, fill=False, padding=0)
        self.show_all()

    def on_button_toggled(self, btn):
        """
        callback function registered with with Gtk
        handles signaling of pinned_button state changed
        """
        if btn is self.pinned_button:
            self.signal_.signal('toggled', playlist_id=self.get_playlist_id())

    def get_playlist_id(self):
        """get the id of the book that this button is associated with"""
        return self.playlist_id

    def set_checked(self, checked):
        """set the state of the pinned_buttin. wether it's checked or not'"""
        self.pinned_button.set_active(checked)
