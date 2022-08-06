# -*- coding: utf-8 -*-
#
#  book_reader.py
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
This module is responsible for managing open Books and feeding them to the view for display
"""
from __future__ import annotations
from typing import TYPE_CHECKING
import pinned_books
import book
import signal_
from gui.gtk import book_reader_view

if TYPE_CHECKING:
    import gi
    gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
    from gi.repository import Gtk
    import book_ease


class BookReader:
    """This class is responsible for opening books for display"""

    def __init__(self,
                 files: book_ease.Files_,
                 book_view_builder: Gtk.Builder):
        self.files = files

        # playlists database helper
        self.playlist_dbi = book.PlaylistDBI()

        # pinned playlists that will be displayed BookReaderView
        self.pinned_books = pinned_books.PinnedBooksC()
        self.pinned_books.connect('open_book', self.open_existing_book)

        # open books
        self.books = []

        # The BookReader components
        book_reader_v = book_reader_view.BookReaderV(book_view_builder)
        gui_builder = book_reader_v.get_builder()

        self.existing_book_opener = ExistingBookOpener(gui_builder, self.files)
        self.existing_book_opener.transmitter.connect('open_book', self.open_existing_book)

        self.new_book_opener = NewBookOpener(gui_builder, self.files)
        self.new_book_opener.transmitter.connect('open_book', self.open_new_book)

        self.start_page = StartPage(gui_builder)
        self.start_page.add_component(self.pinned_books.get_view())

        self.note_book = NoteBook(gui_builder)
        self.note_book.append_page(self.start_page.get_view(), self.start_page.get_tab_label())

    def get_book(self, index):
        """retrieve a book from the book list"""
        return self.books[index]

    def remove_book(self, book_index):
        """remove a book from the book list"""
        self.books.pop(book_index)
        # propagate changes to book list indices
        while book_index < len(self.books):
            self.get_book(book_index)[0].set_index(book_index)
            book_index += 1

    def append_book(self, book_):
        """append book to list of opened books"""
        index = len(self.books)
        book_.set_index(index)
        self.books.append(book_)
        return index

    def open_existing_book(self, pl_data: book.PlaylistData):
        """
        create a new Book instance and tell it to load a saved playlist.
        append the new Book to the booklist for later usage
        """
        book_ = book.BookC(self.files.get_path_current(), None, self)
        br_note_book_tab_vc = BookReaderNoteBookTabVC(book_.transmitter, book_.component_transmitter)
        self.note_book.append_page(book_.get_view(), br_note_book_tab_vc.get_view())
        index = self.append_book(book_)
        book_.transmitter.connect('close', self.remove_book, index)
        book_.transmitter.connect('update', self.existing_book_opener.update_book_list)
        # load the playlist metadata
        book_.open_existing_playlist(pl_data)
        # load the playlist metadata in background
        # load_book_data_th = Thread(target=bk.book_data_load, args={row})
        # load_book_data_th.setDaemon(True)
        # load_book_data_th.start()

    def open_new_book(self):
        """
        create a new Book instance and tell it to create a new playlist.
        append the new Book to the booklist for later usage
        """
        f_list = self.files.get_file_list_new()
        self.files.populate_file_list(f_list, self.files.get_path_current())
        book_ = book.BookC(self.files.get_path_current(), f_list, self)
        br_title_vc = BookReaderNoteBookTabVC(book_.transmitter, book_.component_transmitter)
        index = self.append_book(book_)
        book_.transmitter.connect('close', self.remove_book, index)
        book_.transmitter.connect('update', self.existing_book_opener.update_book_list)
        self.note_book.append_page(book_.get_view(), br_title_vc.get_view())
        # load the playlist metadata
        book_.open_new_playlist()
        # load the playlist metadata in background
        # create_book_data_th = Thread(target=bk.open_new_playlist)
        # create_book_data_th.setDaemon(True)
        # create_book_data_th.start()


class BookReaderNoteBookTabVC:
    """
    Controller for the tab view of the notebook page of the BookReaderView.
    The view contains a close button and a label for displaying the book title
    This class monitors the update signal from a Book so that the title label can be kept current.
    This class also emits the 'close' signal to its associated Book
    """

    def __init__(self, book_transmitter: signal_.Signal, component_transmitter: signal_.Signal):
        self.tab_view = book_reader_view.BookReaderNoteBookTabV()
        self.tab_view.close_button.connect('button-release-event', self.on_close_button_released)
        self.label_max_len = 8
        book_transmitter.connect('update', self.update)
        self.component_transmitter = component_transmitter

    def update(self, book_data: book.BookData):
        """
        sync the title_label with changes made in the Book
        Note that this label has a max length and truncates the title.
        """
        self.tab_view.set_label(book_data.playlist_data.get_title()[0:self.label_max_len])

    def get_view(self) -> Gtk.Box:
        """get the book title label that this class services"""
        return self.tab_view.get_view()

    def on_close_button_released(self, button, event_button):  # pylint: disable=unused-argument
        """The close button was pressed; emit the 'close' signal"""
        self.component_transmitter.send('close')


class ExistingBookOpener:
    """
    This class monitors Files object for changes in CWD, making its view visible if there is a saved book associated
    with this path.

    This class also allows the user top open an existing book by selecting the desired book from the has_book combo box
    and pressing the open_book_button.
    """

    def __init__(self,
                 gui_builder: Gtk.Builder,
                 files: book_ease.Files_):
        self.transmitter = signal_.Signal()
        self.transmitter.add_signal('open_book')

        self.files = files
        self.files.connect('cwd_changed', self.update_book_list)

        self.playlist_dbi = book.PlaylistDBI()

        self.existing_book_opener_v = book_reader_view.ExistingBookOpenerV(gui_builder)
        self.existing_book_opener_v.transmitter.connect('open_book', self.open_book)

        self.existing_book_opener_m = book_reader_view.ExistingBookOpenerM()
        self.existing_book_opener_v.has_book_combo.set_model(self.existing_book_opener_m.get_model())

    def update_book_list(self, *args):  # pylint: disable=unused-argument
        """
        Check if there are any saved Books associated with the new cwd.

        """
        # def update_book_list(self, *args):  # pylint: disable=unused-argument
        cur_path = self.files.get_path_current()
        playlists_in_path = self.playlist_dbi.get_by_path(book.PlaylistData(path=cur_path))
        self.existing_book_opener_m.update(playlists_in_path)
        if len(playlists_in_path) > 0:
            self.existing_book_opener_v.show()
        else:
            self.existing_book_opener_v.hide()

    def open_book(self):
        """
        Use transmitter to broadcast the command to open a book.
        Include a PlaylistData object describing the book as an arg.
        """
        selection = self.existing_book_opener_v.get_selection()
        book_ = self.existing_book_opener_m.get_row(selection)
        self.transmitter.send('open_book', book_)


class NewBookOpener:
    """
    This class monitors Files object for changes in CWD, making its view visible if there is are media files in this
    path.

    This class also allows the user top open a new book by pressing the create_book_button.
    """

    def __init__(self,
                 gui_builder: Gtk.Builder,
                 files: book_ease.Files_):

        self.transmitter = signal_.Signal()
        self.transmitter.add_signal('open_book')

        self.files = files
        self.files.connect('cwd_changed', self.on_cwd_changed)

        self.view = book_reader_view.NewBookOpenerV(gui_builder)
        self.view.transmitter.connect('open_book', self.open_book)

    def open_book(self):
        self.transmitter.send('open_book')

    def on_cwd_changed(self):
        # tell view we have files available if they are media files. offer to create new playlist
        if self.has_new_media():
            self.view.show()
        else:
            self.view.hide()

    def has_new_media(self) -> bool:
        f_list = self.files.get_file_list()
        has_new_media = False
        for i in f_list:
            if book.TrackFI.is_media_file(i[1]):
                has_new_media = True
                break
        return has_new_media


class StartPage:
    """A welcome page to be displayed in the BookReader Notebook View"""

    def __init__(self, gui_builder: Gtk.Builder):
        self.transmitter = signal_.Signal()
        self.transmitter.add_signal('open_book')
        self.view = book_reader_view.StartPageV(gui_builder)
        self.view.set_tab_label('Start')

    def add_component(self, component_view: Gtk.Widget):
        """Add a component View to the start page"""
        self.view.add_view(component_view)

    def get_view(self):
        """get the Gtk container that is the start page view"""
        return self.view.get_view()

    def get_tab_label(self):
        """get a label object from the view"""
        return self.view.get_tab_label()


class NoteBook:
    """
    This class and its view wrap a tabbed notebook view for display by the BookReader module.
    """

    def __init__(self, gui_builder: Gtk.Builder):
        self.note_book_view = book_reader_view.NoteBookV(gui_builder)

    def append_page(self,
                    note_book_page: Gtk.Widget,
                    note_book_tab_view: Gtk.Widget):
        """
        Append a page to the NoteBook Display

        The note_book_page must have a get_view method that is used to fill the main body of the NoteBook view.

        The note_book_tab_view is used to fill the NoteBook's tab with a view that may be able to display a page title
        and/or a close page button.
        """
        self.note_book_view.append_page(note_book_page, note_book_tab_view)
