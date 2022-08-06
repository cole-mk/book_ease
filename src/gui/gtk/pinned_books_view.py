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
from __future__ import annotations
import copy
from pathlib import Path
from typing import TYPE_CHECKING
import gi
gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
from gi.repository import Gtk
import signal_
import book
if TYPE_CHECKING:
    import pinned_books


class PinnedBooksV(Gtk.Box):  # pylint: disable=too-few-public-methods
    """
    display the list of pinned books in a Gtk.Treeview encapsulated in a Gtk.Box
    """
    glade_path = Path().cwd() / 'gui' / 'gtk' / 'pinned_playlists.glade'

    def __init__(self, pinned_cols: pinned_books.PinnedCols):
        """
        initialize the Gtk.Treeview and prepare its cell renderer columns
        """
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=0)
        builder = Gtk.Builder()
        builder.add_from_file(str(self.glade_path))
        # the topmost box in the glade file; add it to self
        self.pack_start(builder.get_object('pinned_view'), expand=True, fill=True, padding=0)
        # create the view
        self.pinned_list_tree_view = builder.get_object('pinned_list_tree_view')
        self.init_tree_view_columns(pinned_cols)
        # Create the control buttons and connect to their clicked signals.
        self.open_button = builder.get_object('open_button')
        self.remove_button = builder.get_object('remove_button')

    def init_tree_view_columns(self, pinned_cols: pinned_books.PinnedCols):
        """Initialize the treeview columns to be used by the treeview"""
        # title column
        title_r = Gtk.CellRendererText()
        title_col = Gtk.TreeViewColumn("Title")
        title_col.pack_start(title_r, True)
        title_col.add_attribute(title_r, "text", pinned_cols.get_title_prop('col'))
        self.pinned_list_tree_view.append_column(title_col)
        # path column
        path_r = Gtk.CellRendererText()
        path_col = Gtk.TreeViewColumn("Location")
        path_col.pack_start(path_r, True)
        path_col.add_attribute(path_r, "text", pinned_cols.get_path_prop('col'))
        self.pinned_list_tree_view.append_column(path_col)


class PinnedBooksVC:
    """
    Controller for the pinned book view.
    """

    def __init__(self, pinned_books_model: pinned_books.PinnedBooksM):
        self.pinned_books_model = pinned_books_model
        self.pinned_books_model.connect('pinned_list_changed', self.on_pinned_list_changed)
        # Get up the column information for gtk.liststore
        self.pinned_cols = self.pinned_books_model.get_col_info()
        # Set up the view with a model
        self.pinned_books_view = PinnedBooksV(self.pinned_cols)
        self.pinned_books_vm = PinnedBooksVM(self.pinned_cols)
        self.pinned_books_view.pinned_list_tree_view.set_model(self.pinned_books_vm.pinned_list)
        # connect to the control buttons
        self.pinned_books_view.open_button.connect('clicked', self.on_control_button_clicked)
        self.pinned_books_view.remove_button.connect('clicked', self.on_control_button_clicked)

        self.pinned_books_vm.load_pinned_list(self.pinned_books_model.get_pinned_playlists())
        # callback system
        self.transmitter = signal_.Signal()
        self.transmitter.add_signal('open_book')

    def get_pinned_list_new(self) -> Gtk.ListStore:
        """
        create a Gtk.ListStore for displaying list of pinned playlists
        """
        # init liststore with g_types by expanding the sorted col_info[*][g_types]
        pinned_list = Gtk.ListStore(*self.pinned_cols.get_prop_sorted('g_type', 'col'))
        return pinned_list

    def get_view(self) -> PinnedBooksV:
        """Get the pinned books view."""
        return self.pinned_books_view

    def open_selected_playlist(self):
        """open a playlist that is selected in the pinned playlists view"""
        sel = self.pinned_books_view.pinned_list_tree_view.get_selection()
        model, paths = sel.get_selected_rows()  # pylint: disable=unused-variable
        if paths:
            playlist_data = self.pinned_books_vm.get_playlist_data(paths[0])
            self.transmitter.send('open_book', playlist_data)

    def remove_selected_playlist(self):
        """remove the first playlist selected in the view from the pinned playlists"""
        sel = self.pinned_books_view.pinned_list_tree_view.get_selection()
        model, paths = sel.get_selected_rows()  # pylint: disable=unused-variable
        for path in paths:
            playlist_data = self.pinned_books_vm.get_playlist_data(path)
            self.pinned_books_model.unpin_book(playlist_data)


    def on_control_button_clicked(self, widget: Gtk.Button):
        """Relay signals appropriately"""
        match widget:
            case self.pinned_books_view.open_button:
                self.open_selected_playlist()

            case self.pinned_books_view.remove_button:
                self.remove_selected_playlist()

    def on_pinned_list_changed(self):
        """Load the Gtk model with the updated list of pinned playlists"""
        pinned_playlists = self.pinned_books_model.get_pinned_playlists()
        self.pinned_books_vm.load_pinned_list(pinned_playlists)


class PinnedBooksVM:
    """wrapper for Gtk.Liststore used for holding pinned playlist data that's displayed in the view."""

    def __init__(self, pinned_cols: pinned_books.PinnedCols):
        # Set up the column information for gtk.liststore
        self.pinned_cols = pinned_cols
        self.pinned_cols.set_playlist_id_prop('g_type', int)
        self.pinned_cols.set_title_prop('g_type', str)
        self.pinned_cols.set_path_prop('g_type', str)
        self.pinned_list = self.get_pinned_list_new()

    def get_pinned_list_new(self) -> Gtk.ListStore:
        """
        create a Gtk.ListStore for displaying list of pinned playlists
        """
        # init liststore with g_types by expanding the sorted col_info[*][g_types]
        pinned_list = Gtk.ListStore(*self.pinned_cols.get_prop_sorted('g_type', 'col'))
        return pinned_list

    def load_pinned_list(self, pinned_playlists: list[book.PlaylistData]):
        """
        load/reload the data in the Gtk.TreeModel (liststore)
        """
        self.pinned_list.clear()
        for playlist in pinned_playlists:
            self.pinned_list.append([playlist.id_, playlist.title, playlist.path])

    def get_playlist_data(self, path: Gtk.TreePath) -> book.PlaylistData:
        """get a row from self.pinned_list as PlaylistData object"""
        g_iter = self.pinned_list.get_iter(path)
        playlist_data = book.PlaylistData()
        playlist_data.set_id(self.pinned_list.get_value(g_iter, self.pinned_cols.playlist_id['col']))
        playlist_data.set_title(self.pinned_list.get_value(g_iter, self.pinned_cols.title['col']))
        playlist_data.set_path(self.pinned_list.get_value(g_iter, self.pinned_cols.path['col']))
        return playlist_data


class PinnedButtonV:  # pylint: disable=too-few-public-methods
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

    def __init__(self,
                 pinned_books_m: pinned_books.PinnedBooksM,
                 book_transmitter: signal_.Signal,
                 book_view_builder: Gtk.Builder):

        # The pinned_books_model associated with this class
        self.pinned_books_m = pinned_books_m
        self.pinned_books_m.connect('pinned_list_changed', self.on_pinned_list_changed)
        # subscribe to the signals relevant to this class
        book_transmitter.connect('close', self.close)
        book_transmitter.connect('begin_edit_mode', self.begin_edit_mode)
        book_transmitter.connect('begin_display_mode', self.begin_display_mode)
        book_transmitter.connect('update', self.update)
        self.view = PinnedButtonV(book_view_builder)
        self.view.pinned_button.connect('toggled', self.on_button_toggled)
        self.button_transmitter = signal_.Signal()
        self.button_transmitter.add_signal('book_updated')
        # flag to prevent loop when setting the state of the checked button
        self.mute_toggle = False
        # PlaylistData
        self.playlist_data = None

    def get_view(self):
        """return self.view.pinned_button"""
        return self.view.pinned_button

    def update(self, book_data: book.BookData):
        """if book is saved, set button visibility and state"""
        if book_data.is_saved():
            self.view.pinned_button.show()
            self.set_checked(self.pinned_books_m.is_pinned(book_data.playlist_data))
            if self.playlist_data and self.playlist_data != book_data.playlist_data:
                self.pinned_books_m.on_playlist_data_changed()
            self.playlist_data = copy.deepcopy(book_data.playlist_data)
        else:
            self.view.pinned_button.hide()
            self.playlist_data = None

    def begin_edit_mode(self):
        """Make the button un-clickable during book editing mode"""
        self.view.pinned_button.set_sensitive(False)

    def begin_display_mode(self):
        """Make the button clickable during book display mode"""
        self.view.pinned_button.set_sensitive(True)

    def close(self):
        """cleanup by closing the view"""
        self.view.pinned_button.destroy()

    def on_button_toggled(self, btn): # pylint: disable=unused-argument
        """
        callback function registered with with Gtk
        handles signaling of pinned_button state changed
        """
        if self.playlist_data is not None and not self.mute_toggle:
            self.pinned_books_m.toggle(playlist_data=self.playlist_data)

    def get_playlist_id(self):
        """get the id of the book that this button is associated with"""
        return self.playlist_data.get_id()

    def set_checked(self, checked):
        """set the state of the pinned_button. wether it's checked or not"""
        self.mute_toggle = True
        self.view.pinned_button.set_active(checked)
        self.mute_toggle = False

    def on_pinned_list_changed(self):
        """ensure the check button is in the correct state after changes to the pinned list"""
        self.set_checked(self.pinned_books_m.is_pinned(self.playlist_data))
