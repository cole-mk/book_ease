# -*- coding: utf-8 -*-
#
#  book_reader_view.py
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
This all the views that constitute the book reader view.
It is a container for displaying books in a gtk notebook, as well as views for the utility components that control the
opening and closing of books.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import pathlib
import gi
gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
from gi.repository import Gtk  # noqa: E402
import signal_  # noqa: E402
import book  # noqa: E402
if TYPE_CHECKING:
    import book_reader


class BookReaderView:
    """
    The outermost view of the bookreader pane containing a notebook to display individual books as well as several
    control buttons to manage the books
    """
    def __init__(self, br_view, gui_builder, book_reader_, pinned_view):
        self.br_view = br_view
        self.book_reader = book_reader_
        self.header_box = gui_builder.get_object('header_box')
        # a view of the pinned books that will be displayed on the start page
        self.pinned_view = pinned_view

        self.book_reader_notebook = gui_builder.get_object('notebook')
        self.start_page = gui_builder.get_object('start_page')
        self.start_page_label = Gtk.Label(label="Start")
        self.book_reader_notebook.append_page(self.start_page, self.start_page_label)
        self.start_page.pack_start(self.pinned_view, expand=False, fill=False, padding=0)

        self.header_box.hide()
        # book_reader_view is the outermost box in the glade file
        self.book_reader_view = gui_builder.get_object('book_reader_view')
        self.br_view.pack_start(self.book_reader_view, expand=True, fill=True, padding=0)

    def on_button_release(self, btn, evt, unused_data=None):
        """
        callback for the various control buttons
        currently takes actions for creating a new book and opening a new book
        """
        if evt.get_button()[0] is True:
            if evt.get_button()[1] == 1:
                if btn is self.create_pl_btn:
                    self.book_reader.open_new_book()

    def on_has_new_media(self, has_new_media):
        """allow book_reader_view to tell the view if there are media files in the directory"""
        if has_new_media:
            self.has_new_media_box.set_no_show_all(False)
            self.has_new_media_box.show_all()
            self.has_new_media_box.set_no_show_all(True)
        else:
            self.has_new_media_box.hide()

    def append_book(self, view: Gtk.Box, br_title_vc: book_reader.BookReaderNoteBookTabVC):
        """set a book view to a new notebook tab"""
        newpage = self.book_reader_notebook.append_page(view, br_title_vc.get_view())
        self.book_reader_notebook.show_all()
        self.book_reader_notebook.set_current_page(newpage)
        # this needs to be changed we're not using the returned tuple
        return newpage, view

    def build_start_page(self):
        """build the content of the first notebook tab for displaying non-specific-book information"""
        start_label = Gtk.Label(label="Welcome to BookEase")
        start_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        start_box.pack_start(start_label, expand=False, fill=False, padding=20)
        start_box.pack_start(self.pinned_view, expand=True, fill=True, padding=20)

        return start_box
        #self.add(start_box)


class BookReaderNoteBookTabV:
    """
    Encapsulate a Gtk.label and a Gtk.Button in a Gtk.Box that is displayed in the tab of the BookReaderV notebook.
    The label holds a (possibly truncated) title of the book displayed in the current notebook page.
    The button is for closing the book.
    """

    def __init__(self):
        self.view = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.title_label = Gtk.Label()
        image = Gtk.Image.new_from_icon_name('window-close', Gtk.IconSize.SMALL_TOOLBAR)
        self.close_button = Gtk.Button(label=None, image=image)
        self.close_button.set_relief(Gtk.ReliefStyle.NONE)
        self.view.pack_start(self.title_label, expand=False, fill=False, padding=0)
        self.view.pack_start(self.close_button, expand=False, fill=False, padding=0)
        self.view.show_all()

    def get_view(self) -> Gtk.Box:
        """Get the Gtk.Box container."""
        return self.view

    def set_label(self, label: str):
        """Set the text in the title label"""
        self.title_label.set_label(label)


class BookReaderV:  # pylint: disable=too-few-public-methods
    """The outermost view of the BookReader"""

    def __init__(self):
        # Load the gui from glade
        self.builder = Gtk.Builder()
        glade_path = pathlib.Path.cwd() / 'gui' / 'gtk' / 'book_reader.glade'
        self.builder.add_from_file(str(glade_path))

    def get_builder(self) -> Gtk.Builder:
        """get the builder object"""
        return self.builder


class ExistingBookOpenerV:
    """
    The Gtk view for the ExistingBookOpener
    """

    def __init__(self, gui_builder: Gtk.Builder):
        self.transmitter = signal_.Signal()
        self.transmitter.add_signal('open_book')
        # has_book_box notification
        self.has_book_box = gui_builder.get_object('has_book_box')
        self.has_book_box.set_no_show_all(True)
        self.open_book_btn = gui_builder.get_object('open_book_btn')
        self.has_book_combo = gui_builder.get_object('has_book_combo')
        renderer_text = Gtk.CellRendererText()
        self.has_book_combo.pack_start(renderer_text, True)
        self.has_book_combo.add_attribute(renderer_text, "text", ExistingBookOpenerM.pl_title['g_col'])
        self.open_book_btn.connect('button-release-event', self.on_button_release)

    def on_button_release(self, *args):  # pylint: disable=unused-argument
        """Relay the message that the user wants to open a book."""
        self.transmitter.send('open_book')

    def get_selection(self) -> Gtk.TreeIter:
        """get an iterator pointing to the book selected by the user in the has_book_combo"""
        return self.has_book_combo.get_active_iter()

    def show(self):
        """Make this view visible"""
        self.has_book_combo.set_active(0)
        self.has_book_box.show()

    def hide(self):
        """Make this view invisible"""
        self.has_book_box.hide()


class ExistingBookOpenerM:
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
    g_types = map(lambda x: x['g_type'], pl_helper_l)

    def __init__(self):
        self.model = Gtk.ListStore(*self.g_types)

    def get_row(self, row: Gtk.TreeIter) -> book.PlaylistData:
        """return a row from the model as a PlaylistData object"""
        playlist_data = book.PlaylistData()
        playlist_data.set_id(self.model.get_value(row, self.pl_id['g_col']))
        playlist_data.set_title(self.model.get_value(row, self.pl_title['g_col']))
        playlist_data.set_path(self.model.get_value(row, self.pl_path['g_col']))
        return playlist_data

    def update(self, pl_data_list: list[book.PlaylistData]):
        """Populate the model with the data in the list of PlaylistData objects."""
        self.model.clear()
        for playlist_data in pl_data_list:
            g_iter = self.model.append()
            self.model.set_value(g_iter, self.pl_id['g_col'], playlist_data.get_id())
            self.model.set_value(g_iter, self.pl_title['g_col'], playlist_data.get_title())
            self.model.set_value(g_iter, self.pl_path['g_col'], playlist_data.get_path())

    def get_model(self) -> Gtk.ListStore:
        """get the Gtk.ListStore that this class encapsulates."""
        return self.model


class NewBookOpenerV:
    """The Gtk view for the ExistingBookOpener"""

    def __init__(self, gui_builder: Gtk.Builder):
        self.transmitter = signal_.Signal()
        self.transmitter.add_signal('open_book')

        self.has_new_media_box = gui_builder.get_object('has_new_media_box')
        self.has_new_media_box.set_no_show_all(True)

        self.create_book_btn = gui_builder.get_object('create_book_btn')
        self.create_book_btn.connect('button-release-event', self.on_button_release)

    def on_button_release(self, *args):  # pylint: disable=unused-argument
        """Relay the message that the user wants to open a book."""
        self.transmitter.send('open_book')

    def show(self):
        """Make this view visible"""
        self.has_new_media_box.show()

    def hide(self):
        """Make this view invisible"""
        self.has_new_media_box.hide()
