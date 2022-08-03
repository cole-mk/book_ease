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
# import signal_
from __future__ import annotations
from typing import TYPE_CHECKING
import re
import configparser
import pinned_books
import book
import signal_
from gui.gtk import book_reader_view

if TYPE_CHECKING:
    import gi
    gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
    from gi.repository import Gtk
    import book_ease
    import configparser

class BookReader:

    def __init__(self,
                 files: book_ease.Files_,
                 config: configparser.ConfigParser,
                 builder: Gtk.Builder):
        self.book_reader_section = 'book_reader'
        self.cur_path = None
        self.files = files
        self.config = config
        self.playlist_file = self.config['book_reader']['playlist_file']
        self.book_reader_dir = self.config['book_reader']['book_reader_dir']
        # playlists database helper
        self.playlist_dbi = book.PlaylistDBI()

        # pinned playlists that will be displayed bookReader_View
        self.pinned_books = pinned_books.PinnedBooksC()
        self.pinned_books.connect('open_book', self.open_existing_book)

        # register a updated file list callback with files instance
        # self.files.connect('file_list_updated', self.on_file_list_updated, get_cur_path=self.files.get_path_current)
        self.files.connect('file_list_updated', self.on_file_list_updated)
        self.book_conf = configparser.ConfigParser()
        self.found_book_path = None
        self.book_path = None
        self.book_open = False
        # books
        self.books = []
        self.book_cache = []
        self.tmp_book = None
        # playlist_filetypes key has values given in a comma separated list
        file_types = config[self.book_reader_section]['playlist_filetypes'].split(",")
        # build compiled regexes for matching list of media suffixes.
        self.f_type_re = []
        for i in file_types:
            i = '.*.\\' + i.strip() + '$'
            self.f_type_re.append(re.compile(i))

        self.book_reader_view = book_reader_view.BookReader_View(
            builder.get_object("book_reader_view"),
            self,
            self.pinned_books.get_view()
        )

    def has_book(self, pth):
        """determine if there is a playlist associated with the directory, pth"""
        br_path = os.path.join(pth, self.book_reader_dir, self.playlist_file)
        if os.path.exists(br_path):
            return True
        return False

    def get_book(self, index):
        """retrieve a book from the book list"""
        return self.books[index]

    def remove_book(self, book_index):
        """remove a book from the book list"""
        self.books.pop(book_index)
        # propogate changes to book list indices
        while book_index < len(self.books):
            self.get_book(book_index)[0].set_index(book_index)
            book_index += 1

    def on_file_list_updated(self):
        """
        Files is notifying bookreader that it has changed directories and is giving Book reader the list of files in
        the new current working directory.

        Tell BookReader_View if there are any media files that can be used to create a playlist.
        """
        # Tell BookReader_View if there are any saved playlists associated with this directory.
        self.update_current_book_list()

        # tell view we have files available if they are media files. offer to create new playlist
        f_list = self.files.get_file_list()
        has_new_media = False
        for i in f_list:
            if book.TrackFI.is_media_file(i[1]):
                has_new_media = True
                break
        self.book_reader_view.on_has_new_media(has_new_media)

    def append_book(self, book_):
        """append book to list of opened books"""
        index = len(self.books)
        book_.set_index(index)
        self.books.append(book_)
        return index

    def open_existing_book(self, pl_row):
        """
        create a new Book instance and tell it to load a saved playlist.
        append the new Book to the booklist for later usage
        """
        book_ = book.BookC(self.cur_path, None, self)
        br_note_book_tab_vc = BookReaderNoteBookTabVC(book_.transmitter, book_.component_transmitter)
        book_.page = self.book_reader_view.append_book(book_.get_view(), br_note_book_tab_vc)
        index = self.append_book(book_)
        book_.transmitter.connect('close', self.remove_book, index)
        book_.transmitter.connect('update', self.update_current_book_list)
        # load the playlist metadata
        book_.open_existing_playlist(pl_row)
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
        self.files.populate_file_list(f_list, self.cur_path)
        book_ = book.BookC(self.cur_path, f_list, self)
        br_title_vc = BookReaderNoteBookTabVC(book_.transmitter, book_.component_transmitter)
        index = self.append_book(book_)
        book_.transmitter.connect('close', self.remove_book, index)
        book_.page = self.book_reader_view.append_book(book_.get_view(), br_title_vc)
        # clear book_reader_view.has_new_media flag
        self.book_reader_view.on_has_new_media(False)
        # load the playlist metadata
        book_.open_new_playlist()
        # load the playlist metadata in background
        # create_book_data_th = Thread(target=bk.open_new_playlist)
        # create_book_data_th.setDaemon(True)
        # create_book_data_th.start()

    def is_media_file(self, file_):
        """determine is file_ matches any of the media file definitions"""
        for i in self.f_type_re:
            if i.match(file_):
                return True
        return False

    def update_current_book_list(self, *args):
        """Tell BookReader_View if there are any saved playlists associated with the current directory."""
        self.cur_path = self.files.get_path_current()
        playlists_in_path = self.playlist_dbi.get_by_path(book.PlaylistData(path=self.cur_path))
        if len(playlists_in_path) > 0:
            self.book_reader_view.on_has_book(has_book=True, playlists_in_path=playlists_in_path)
        else:
            self.book_reader_view.on_has_book(has_book=False)


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

    def on_close_button_released(self, button, event_button): #pylint: disable=unused-argument
        """The close button was pressed; emit the 'close' signal"""
        self.component_transmitter.send('close')
