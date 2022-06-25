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
from gui.gtk.pinned_books_view import PinnedBooksV, PinnedButtonVC
import signal_
import sqlite_tables
import singleton_


class PinnedBooksC(signal_.Signal):
    """
    controller for the pinned books module
    """

    def __init__(self):
        """
        instantiate both the PinnedBooksV and the PinnedBooksM
        """
        signal_.Signal.__init__(self)
        self.add_signal('open-book')
        self.model = PinnedBooksM()
        self.view = PinnedBooksV(self.model.get_col_info(), self)
        self.pinned_button_model = PinnedButtonM()
        self.model.connect('pinned_list_changed', self.view.load_pinned_list)

    def on_book_updated(self, playlist_id):
        """
        callback indicating that a book in the pinned list
        might have changed. pass this message to the model
        and wait for a decision to be made there
        """
        self.model.on_book_updated(playlist_id)

    def get_view(self):
        """get the pinned_list view"""
        return self.view

    def toggle(self, playlist_id):
        """
        callback indicating that the pinned button associated
        with a particular opened playlist has had a change of state

        playlist_id: the id of the playlist associated with
        the pinned button
        """
        self.model.toggle(playlist_id)

    def get_pinned_playlists(self):
        """
        get a list of pinned playlists
        encapsulated in PinnedData objects
        """
        return self.model.get_pinned_playlists()

    def is_pinned(self, playlist_id):
        """
        ask the PinnedBooksM if this particular playlist
        is on the pinned list

        playlist_id: the id of the playlist
        """
        return self.model.is_pinned(playlist_id)

    def get_pinned_button_new(self, book, book_transmitter, book_view_builder):
        """
        create a new PinnedButtonVC, a container for a CheckButton
        returns the view object
        """
        btn_vi = PinnedButtonVC(book, book_transmitter, book_view_builder)
        # set checkbutton state
        if self.is_pinned(book.get_playlist_id()):
            btn_vi.set_checked(True)
        btn_vi.button_transmitter.connect('toggled', self.toggle)
        btn_vi.button_transmitter.connect('book_updated', self.on_book_updated)
        self.pinned_button_model.add_button(btn_vi)
        return btn_vi


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


class PinnedData:
    """
    container for passing playlist data to the different classes
    in this module.
    """

    def __init__(self, playlist_id, title, path):
        """initialize the data columns stored in this container"""
        # column descriptions
        self._col_info = PinnedCols()
        # set values of the data columns
        self.playlist_id = playlist_id
        self.title = title
        self.path = path

    def get_title(self):
        """get the value in the title column"""
        return self.title

    def get_title_prop(self, key):
        """see PinnedCols"""
        return self._col_info.title[key]

    def set_title_prop(self, key, prop):
        """see PinnedCols"""
        self._col_info.title[key] = prop

    def get_path(self):
        """get the value in the path column"""
        return self.path

    def get_path_prop(self, key):
        """see PinnedCols"""
        return self._col_info.path[key]

    def set_path_prop(self, key, prop):
        """see PinnedCols"""
        self._col_info.path[key] = prop

    def get_playlist_id(self):
        """get the value in the playlist_id column"""
        return self.playlist_id

    def get_playlist_id_prop(self, key):
        """see PinnedCols"""
        return self._col_info.playlist_id[key]

    def set_playlist_id_prop(self, key, prop):
        """see PinnedCols"""
        self._col_info.playlist_id[key] = prop

    def get_prop_sorted(self, prop, key):
        """see PinnedCols"""
        return self._col_info.get_prop_sorted(prop, key)

    def get_data_sorted_by_prop(self, prop):
        """
        get title, path, and playlist_id sorted by column number property
        returns list
        """
        data = {self.get_playlist_id():self._col_info.get_playlist_id_prop(prop),
                self.get_title():self._col_info.get_title_prop(prop),
                self.get_path():self._col_info.get_path_prop(prop)}
        return list(sorted(data, key=lambda key: data[key]))


class PinnedButtonM:
    """
    maintain the list of pinned buttons
    """

    def __init__(self):
        """the pinned button list"""
        self.pinned_button_list = []

    def add_button(self, pinned_button):
        """add a pinnedButton to the list"""
        self.pinned_button_list.append(pinned_button)

    def remove_button(self, platlist_id):
        """remove a pinnedButton from the list"""
        btn = self.get_button(platlist_id)
        self.pinned_button_list.remove(btn)

    def get_button(self, platlist_id):
        """get a pinnedButton from the list"""
        for btn in self.pinned_button_list:
            if btn.get_playlist_id() == platlist_id:
                return btn
        raise ValueError('button not found in pinned_button_list')


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

    def toggle(self, playlist_id):
        """
        callback indicating that the pinned status of an open book has changed.
        add/remove the passed playlist from the list of pinned_playlists.
        """
        if self.is_pinned(playlist_id):
            self.unpin_book(playlist_id)
        else:
            self.pin_book(playlist_id)
        # propagate the message that the status has changed
        self.send('pinned_list_changed')

    def is_pinned(self, playlist_id):
        """
        check the pinned status of the passed in playlist
        returns bool
        """
        return self.dbi.is_pinned(playlist_id)

    def unpin_book(self, playlist_id):
        """remove playlist_id from the list of pinned playlists"""
        self.dbi.unpin_playlist(playlist_id)

    def pin_book(self, playlist_id):
        """add playlist_id to the list of pinned playlists"""
        playlist = self.dbi.get_playlist(playlist_id)
        if playlist is not None:
            self.dbi.pin_playlist(playlist_id)

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

    def on_book_updated(self, playlist_id):
        """
        callback indicating that something in an open book has been changed
        test if that book is pinned and signal that something in the pinned
        list might have changed.
        """
        if playlist_id in self.dbi.get_pinned_ids():
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
        self.pinned_playlists = sqlite_tables.PinnedPlaylists()
        self.playlist = sqlite_tables.Playlist()

    def get_playlist(self, playlist_id):
        """
        get the desired playlist row from the database
        and return a PinnedData object
        """
        con = sqlite_tables.create_connection()
        with con:
            # get sqlite row object from the table class
            row = self.playlist.get_row(con, playlist_id)
        con.close()
        # return PinnedData object
        return PinnedData(playlist_id=row['id'], title=row['title'], path=row['path'])

    def get_playlists(self, playlist_ids):
        """
        get all playlist rows matching the playlist_ids from the database
        and return a list of PinnedData objects
        """
        con = sqlite_tables.create_connection()
        with con:
            # get the desired sqlite row objects
            rows = self.playlist.get_rows(con, playlist_ids)
        con.close()
        # return list of PinnedData objects copied from list of sqlite row objects
        playlists = []
        for row in rows:
            playlists.append(PinnedData(playlist_id=row['id'], title=row['title'], path=row['path']))
        return playlists

    def is_pinned(self, playlist_id):
        """
        search pinned list table for playlist_id
        return bool
        """
        con = sqlite_tables.create_connection()
        with con:
            has_playlist = self.pinned_playlists.has_playlist(con, playlist_id)
        con.close()
        return has_playlist

    def pin_playlist(self, playlist_id):
        """add a playlist to the pinned list in the database"""
        con = sqlite_tables.create_connection()
        with con:
            self.pinned_playlists.insert_playlist(con, playlist_id)
        con.close()

    def unpin_playlist(self, playlist_id):
        """remove a playlist from the pinned list in the database"""
        con = sqlite_tables.create_connection()
        with con:
            self.pinned_playlists.remove_playlist(con, playlist_id)
        con.close()

    def get_pinned_ids(self):
        """get a list of just the playlist ids and not the whole PinnedData object"""
        con = sqlite_tables.create_connection()
        pinned_list = []
        with con:
            rows = self.pinned_playlists.get_pinned_playlists(con)
        con.close()
        # convert list of sqlite row object to list of tuples (str,)
        for row in rows:
            pinned_list.append(row['playlist_id'])
        return pinned_list
