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

"""
pinned_books_view module contains the views for the pinned buttons attached to each book view and for the list of pinned
books that are displayed by the book reader view
"""

import gi
#pylint: disable=wrong-import-position
gi.require_version("Gtk", "3.0")
#pylint: enable=wrong-import-position
from gi.repository import Gtk
import signal_


class PinnedBooksV(Gtk.Box):
    """
    display the list of pinned books in a Gtk.Treeview encapsulated in a Gtk.Box
    """

    def __init__(self, pinned_cols, pinned_books_c):
        """
        initialize the Gtk.Treeview and its model for displayling the list of pinned books

        pinned_cols is pinned_books.PinnedCols: container for descriptions of the pinned list data
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
        row_iter = model.append(tuple(playlist_data.get_data_sorted_by_prop('col')))
        return row_iter

    def remove_book(self,title, path):
        """remove a row from the list of pinned books"""
        model = self.pinned_view.get_model()
        for row in model:
            if (row[self.pinned_cols.get_title_prop('col')] == title
            and row[self.pinned_cols.get_path_prop('col')] == path):
                model.remove(row.iter)


class PinnedButtonV: #pylint: disable=too-few-public-methods
    """
    display a Gtk.CheckButton to control wether or not a book is pinned
    """

    def __init__(self, book_view_builder):
        """
        Initialize a Gtk.CheckButton and encapsulate it in a Gtk.Box
        playlist_id: the id of the book that this button is associated with
        """
        self.pinned_button = book_view_builder.get_object('pinned_button')


class PinnedButtonVC:
    """
    class controls a Gtk.CheckButton view.
    this class is connected to the pinned_books module as well as book.BookC
    """

    def __init__(self, pinned_books_c, book, book_transmitter, book_view_builder):
        # subscribe to the signals relevant to this class
        book_transmitter.connect('close', self.close)
        book_transmitter.connect('begin_edit_mode', self.begin_edit_mode)
        book_transmitter.connect('begin_display_mode', self.begin_display_mode)
        book_transmitter.connect('update', self.update)
        # save a reference to the book model so PinnedButtonVC can get data when it needs to
        self.book = book
        self.view = PinnedButtonV(book_view_builder)
        self.view.pinned_button.connect('toggled', self.on_button_toggled)
        self.button_transmitter = signal_.Signal()
        self.button_transmitter.add_signal('toggled')
        self.button_transmitter.add_signal('book_updated')
        # The PinnedBooksC that instantiated this class
        self.pinned_books_c = pinned_books_c

    def get_view(self):
        """return self.view.pinned_button"""
        return self.view.pinned_button

    def update(self):
        """if book is saved, tell PinnedBooksC to update list of pinned books"""
        if self.book.is_saved():
            if self.pinned_books_c.is_pinned(self.get_playlist_id()):
                self.view.pinned_button.set_active(True)
            self.button_transmitter.send('book_updated', playlist_id=self.book.get_playlist_id())

    def begin_edit_mode(self):
        """hide the view when told to begin book editing mode"""
        self.view.pinned_button.hide()

    def begin_display_mode(self):
        """show the view when told to begin book editing mode"""
        if self.book.is_saved():
            self.view.pinned_button.show()

    def close(self):
        """cleanup by closing the view"""
        self.view.pinned_button.destroy()

    def on_button_toggled(self, btn): #pylint: disable=unused-argument
        """
        callback function registered with with Gtk
        handles signaling of pinned_button state changed
        """
        self.button_transmitter.send('toggled', playlist_id=self.book.get_playlist_id())

    def get_playlist_id(self):
        """get the id of the book that this button is associated with"""
        return self.book.get_playlist_id()

    def set_checked(self, checked):
        """set the state of the pinned_buttin. wether it's checked or not"""
        self.view.pinned_button.set_active(checked)
