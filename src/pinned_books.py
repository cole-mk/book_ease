# -*- coding: utf-8 -*-
#
#  pinned_books.py
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
pinned_books module, along with the gui bits in gui.gtk.pinned_books_view, is the entire subsystem responsible for
managing the list of book that have been marked as "pinned" by the user.
"""
from gui.gtk.pinned_books_view import PinnedBooksVC, PinnedButtonVC
import signal_
import audio_book_tables
import singleton_
import book

class PinnedBooksC(signal_.Signal):
    """
    controller for the pinned books module
    """

    def __init__(self):
        """
        instantiate both the PinnedBooksV and the PinnedBooksM
        """
        signal_.Signal.__init__(self)
        self.add_signal('open_book')
        self.pinned_books_model = PinnedBooksM()
        self.view_c = PinnedBooksVC(self.pinned_books_model)
        # Set up the transmitter to resend the open_book signal.
        self.view_c.transmitter.connect('open_book', self.send, 'open_book')

    def get_view(self):
        """get the pinned_list view"""
        return self.view_c.get_view()

    def get_pinned_button_new(self, book_transmitter, book_view_builder):
        """
        create a new PinnedButtonVC, a controller for a CheckButton
        returns the view object
        """
        btn_vc = PinnedButtonVC(self.pinned_books_model, book_transmitter, book_view_builder)
        return btn_vc


class PinnedCols(singleton_.Singleton):
    """
    PinnedCols contains descriptions of the data in the PinnedData class
    that are common to all instances of the PinnedData class.
    changes made to the descriptions are propogated to all instances.
    """

    def init(self):
        """
        initialize the PinnedData property containers
        each data column in the PinnedData class has an associated
        dict containing key/property values
        """
        self.playlist_id = {'col':0,}
        self.title = {'col':1,}
        self.path = {'col':2,}
        self.cols = [self.playlist_id, self.title, self.path]

    def get_title_prop(self, key):
        """return a property of the title PinnedData column"""
        return self.title[key]

    def set_title_prop(self, key, prop):
        """set a property of the title PinnedData column"""
        self.title[key] = prop

    def get_path_prop(self, key):
        """return a property of the path PinnedData column"""
        return self.path[key]

    def set_path_prop(self, key, prop):
        """set a property of the path PinnedData column"""
        self.path[key] = prop

    def get_playlist_id_prop(self, key):
        """return a property of the playlist_id PinnedData column"""
        return self.playlist_id[key]

    def set_playlist_id_prop(self, key, prop):
        """set a property of the playlist_id PinnedData column"""
        self.playlist_id[key] = prop

    def get_prop_sorted(self, prop, key):
        """
        create a list of property values for all of the data columns
        based on the passed in prop arg.
        That list is sorted based on the value for the passed in key arg
        ex: passing prop=g_type, key=col will return a list of the g_types
            for each of the playlist_id, path, and title columns, sorted
            by column number
        """
        return [col[prop] for col in sorted(self.cols, key=lambda column: column[key])]


class PinnedBooksM(signal_.Signal):
    """
    maintain the list of pinned books
    this includes saving/retrieving the list to/from premenant storage
    via the database interface class
    """

    def __init__(self):
        signal_.Signal.__init__(self)
        # signal that that something in the pinned list might have changed
        self.add_signal('pinned_list_changed')
        # the database interface
        self.dbi = PinnedBooksDBI()
        # setup col_info
        self.col_info = PinnedCols()

    def toggle(self, playlist_data: book.PlaylistData):
        """
        callback indicating that the pinned status of an open book has changed.
        add/remove the passed playlist from the list of pinned_playlists.
        """
        if self.is_pinned(playlist_data):
            self.unpin_book(playlist_data)
        else:
            self.pin_book(playlist_data)

    def is_pinned(self, playlist_data: book.PlaylistData) -> bool:
        """
        check the pinned status of the passed in playlist
        returns bool
        """
        return self.dbi.is_pinned(playlist_data.get_id())

    def unpin_book(self, playlist_data: book.PlaylistData):
        """remove playlist_id from the list of pinned playlists"""
        playlist_id = playlist_data.get_id()
        self.dbi.unpin_playlist(playlist_id)
        # propagate the message that the status has changed
        self.send('pinned_list_changed')

    def pin_book(self, playlist_data: book.PlaylistData):
        """add playlist to the list of pinned playlists"""
        playlist_id = playlist_data.get_id()
        playlist = self.dbi.get_playlist(playlist_id)
        if playlist is not None:
            self.dbi.pin_playlist(playlist_id)
        # propagate the message that the status has changed
        self.send('pinned_list_changed')

    def get_pinned_playlists(self):
        """
        get and return a list of PinnedData objects
        this is the pinned playlist
        """
        playlist_ids = self.dbi.get_pinned_ids()
        playlists = self.dbi.get_playlists(playlist_ids)
        return playlists

    def get_col_info(self):
        """get the PinnedCols object stored in self.col_info"""
        return self.col_info

    def on_playlist_data_changed(self):
        """
        callback indicating that something in an open book has been changed
        Reload the pinned list.
        """
        self.send('pinned_list_changed')


class PinnedBooksDBI:
    """
    Class to interface the database with the rest of the module.
    manage the connections to the database table classes.
    manage converting the data to module specific format for
    consumption by the other classes in this module.
    """

    def __init__(self):
        """init the database table classes"""
        self.pinned_playlists = audio_book_tables.PinnedPlaylists()
        self.playlist = audio_book_tables.Playlist()

    def get_playlist(self, playlist_id):
        """
        get the desired playlist row from the database
        and return a PlaylistData object
        """
        con = audio_book_tables.create_connection()
        with con:
            # get sqlite row object from the table class
            row = self.playlist.get_row(con, playlist_id)
        con.close()
        # return PinnedData object
        return book.PlaylistData(id_=row['id'], title=row['title'], path=row['path'])

    def get_playlists(self, playlist_ids: list[int]) -> list[book.PlaylistData]:
        """
        get all playlist rows matching the playlist_ids from the database
        and return a list of PinnedData objects
        """
        con = audio_book_tables.create_connection()
        with con:
            # get the desired sqlite row objects
            rows = self.playlist.get_rows(con, playlist_ids)
        con.close()
        # return list of PinnedData objects copied from list of sqlite row objects
        playlists = []
        for row in rows:
            playlists.append(book.PlaylistData(id_=row['id'], title=row['title'], path=row['path']))
        return playlists

    def is_pinned(self, playlist_id: int) -> bool:
        """
        search pinned list table for playlist_id
        return bool
        """
        con = audio_book_tables.create_connection()
        with con:
            has_playlist = self.pinned_playlists.has_playlist(con, playlist_id)
        con.close()
        return has_playlist

    def pin_playlist(self, playlist_id):
        """add a playlist to the pinned list in the database"""
        con = audio_book_tables.create_connection()
        with con:
            self.pinned_playlists.insert_playlist(con, playlist_id)
        con.close()

    def unpin_playlist(self, playlist_id):
        """remove a playlist from the pinned list in the database"""
        con = audio_book_tables.create_connection()
        with con:
            self.pinned_playlists.remove_playlist(con, playlist_id)
        con.close()

    def get_pinned_ids(self):
        """get a list of just the playlist ids and not the whole PinnedData object"""
        con = audio_book_tables.create_connection()
        pinned_list = []
        with con:
            rows = self.pinned_playlists.get_pinned_playlists(con)
        con.close()
        # convert list of sqlite row object to list of tuples (str,)
        for row in rows:
            pinned_list.append(row['playlist_id'])
        return pinned_list
