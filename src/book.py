# -*- coding: utf-8 -*-
#
#  book.py
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
This module is all of the classes responsible for being a book
this includes the book model, database interfaces for the book, and the main controller class for the book
"""
import re
import os
import mutagen
import playlist
import signal_
import audio_book_tables
from gui.gtk import book_view
import book_columns


class DBConnection: #pylint: disable=too-few-public-methods
    """provide database connection management for multi queries"""

    def __init__(self):
        self.con = None

    def multi_query_begin(self):
        """
        create a semi-persistent connection
        for executing multiple transactions
        """
        if self.con is not None:
            raise RuntimeError('connection already exists')
        self.con = audio_book_tables.create_connection()
        self.con.execute('BEGIN')

    def multi_query_end(self):
        """commit and close connection of a multi_query"""
        if self.con is None:
            raise RuntimeError('connection doesn\'t exist')
        self.con.commit()
        self.con.close()
        self.con = None

    def query_begin(self) -> 'sqlite3.Connection':
        """
        get an sqlite connection object
        returns self.con if a multi_query is in effect.
        Otherwise, create and return a new connection
        """
        if self.con is None:
            return audio_book_tables.create_connection()
        return self.con

    def query_end(self, con):
        """
        commit and close connection if a multi_query
        is not in effect.
        """
        if con is not self.con:
            con.commit()
            con.close()

# the module wide reference to DBConnection
DB_CONNECTION = DBConnection()


class BookData:
    """DTO for Book's"""

    def __init__(self, playlist_data):
        self.playlist_data = playlist_data
        self.track_list = []
        self.saved_playlist = False

    def is_saved(self) -> bool:
        """tell if this playlist has already been saved"""
        return self.saved_playlist

    def set_saved(self, bool_: bool):
        """set this playlist's saved flag"""
        self.saved_playlist = bool_

    def pop_track(self) -> 'Track':
        """pop and return a Track object from the self.track_list"""
        try:
            track = self.track_list.pop()
        except IndexError:
            track = None
        return track

    def sort_track_list_by_number(self) -> None:
        """sort self.track_list in place"""
        self.track_list.sort(key=lambda row: row.number, reverse=True)


class PlaylistData:
    """Class to encapsulate the data that describes a playlist"""

    def __init__(self,
                 title: str = None,
                 path: str = None,
                 id_: int = None):
        self.title = title
        self.path = path
        self.id_ = id_

    def get_title(self) -> str:
        """get title attribute from PlaylistData"""
        return self.title

    def set_title(self, title: str):
        """set title attribute of PlaylistData"""
        self.title = title

    def get_path(self) -> str:
        """get path attribute from PlaylistData"""
        return self.path

    def set_path(self, path: str):
        """set path attribute of PlaylistData"""
        self.path = path

    def get_id(self) -> int:
        """get id attribute from PlaylistData"""
        return self.id_

    def set_id(self, id_: int):
        """set id attribute of PlaylistData"""
        self.id_ = id_

    def __eq__(self, other):
        return(isinstance(other, self.__class__)
               and self.__dict__ == other.__dict__)


class Book(playlist.Playlist, signal_.Signal):
    """Book is the model for a book"""

    def __init__(self, path: str, file_list: list[tuple] | None):
        playlist.Playlist.__init__(self)
        signal_.Signal.__init__(self)
        self.index = None
        self.playlist_data = PlaylistData(title='New Book', path=path)
        #database interfaces
        self.track_dbi = TrackDBI()
        self.playlist_dbi = PlaylistDBI()
        # files to scrape for track metadata
        self.file_list = file_list

        # initialize the callback system
        self.add_signal('book_data_loaded')
        self.add_signal('book_data_created')
        self.add_signal('book_saved')
        # a counter to determine the size of the playlist that will be use to cleanup deleted files
        # this is used during the saving process.
        self.pl_track_counter = 0

    def get_cur_pl_list(self) -> PlaylistData:
        """get list of playlists associated with current path"""
        return self.playlist_dbi.get_by_path(self.playlist_data)

    def get_index(self) -> int:
        """get the index of this book's position in the BookReader's list of books"""
        return self.index

    def set_index(self, index: int):
        """set the index of this book's position in the BookReader's list of books"""
        self.index = index

    def book_data_load(self, playlist_data: PlaylistData):
        """load a saved playlist from the database"""

        self.playlist_data = playlist_data

        # retrieve a list of tracks belonging to this playlist
        # edit those tracks and add them to a new BookData object
        book_data = BookData(playlist_data)
        for track in self.track_dbi.get_track_list_by_pl_id(self.playlist_data.get_id()):
            book_data.track_list.append(track)
            # populate track metadata
            for col in book_columns.metadata_col_list:
                entry_list = self.track_dbi.get_metadata_list(col['key'], track.get_pl_track_id())
                track.set_entry(col['key'], entry_list)

        self.saved_playlist = True
        book_data.set_saved(True)
        # sort playlist by  number
        book_data.sort_track_list_by_number()
        return book_data

    def create_book_data(self):
        """initialize a new BookData object with playlist data scraped from file metadata"""

        book_data = BookData(self.playlist_data)
        for file_ in self.file_list:
            # populate track data
            file_path = os.path.join(self.playlist_data.get_path(), file_[1])
            try:
                # create the track
                track = TrackFI.get_track(file_path)
            except UnsupportedFileType:
                # skip to the next file if this file is a directory or some other non-supported file type
                continue

            # do the appending
            book_data.track_list.append(track)

            # load alt values if this entry is empty
            for col in book_columns.metadata_col_list:
                if not track.get_entries(col['key']):
                    alt_entries = track.get_entry_lists_new(col['alt_keys'])
                    if alt_entries:
                        track.set_entry(col['key'], alt_entries[:1])

        # set book title from the first track title
        title_list = book_data.track_list[0].get_entries('title')
        if title_list:
            self.playlist_data.set_title(title_list[0].get_entry())
        return book_data

    def set_unique_playlist_title(self, playlist_data: PlaylistData) -> str:
        """add a incremented suffix to self.playlist_data.title if there are duplicates"""
        suffix = ''
        count = 1
        while self.playlist_dbi.count_duplicates(playlist_data) > 0:
            title = playlist_data.get_title().rstrip(suffix)
            suffix = '_' + str(count)
            playlist_data.set_title(title + suffix)
            count += 1
        return playlist_data

    def save_playlist_data(self):
        """Save self.playlist_data which consists of title, path, and id"""
        # add suffix to book title to ensure uniqueness
        self.set_unique_playlist_title(self.playlist_data)
        # save playlist_data (title,path,id) storing returned id in self.playlist_data
        self.playlist_data.set_id(self.playlist_dbi.save(self.playlist_data))
        # update the playlist saved flag
        self.set_saved(True)

    def save_track(self, track: playlist.Track):
        """Save all of the Track data."""
        # increment the pl_track_counter that was initialized in save_book_begin
        self.pl_track_counter += 1
        # save the file path that the Track object references
        track_file_id = self.track_dbi.save_track_file(track)
        # save the simple Track instance variables
        pl_track_id = self.track_dbi.save_pl_track(self.playlist_data.get_id(), track_file_id, track)
        # update pl_track_id in the Track instance
        track.set_pl_track_id(pl_track_id)

        # save the Track metadata
        for col in book_columns.metadata_col_list:
            md_entry_l = track.get_entries(col['key'])
            for md_entry in md_entry_l:
                id_ = self.track_dbi.save_track_metadata(md_entry, pl_track_id, col['key'])
                md_entry.set_id(id_)
            # remove deleted entries from database
            self.track_dbi.remove_deleted_metadata(len(md_entry_l) - 1, pl_track_id, col['key'])

    def save_book_finished(self):
        """cleanup after saving the book and close the connection to the database."""
        # remove deleted entries from database using self.pl_track_counter to determine the actual size of the playlist
        self.track_dbi.remove_deleted_pl_tracks(self.playlist_data.get_id(), self.pl_track_counter)
        self.saved_playlist = True
        DB_CONNECTION.multi_query_end()

    def save_book_begin(self):
        """prepare to begin saving book data by opening a connection to the database."""
        # initialize a counter to determine the size of the playlist that will be use to cleanup deleted files
        self.pl_track_counter = 0
        # open the book's module wide connection to the database for saving the book
        DB_CONNECTION.multi_query_begin()

    def save(self, book_data: BookData):
        """Save book_data to database"""
        self.save_book_begin()
        self.playlist_data = book_data.playlist_data
        self.save_playlist_data()
        for track in book_data.track_list:
            self.save_track(track)
        self.save_book_finished()


class PlaylistDBI():
    """Interface to help the Book save playlist specific data"""

    def __init__(self):
        self.playlist = audio_book_tables.Playlist()

    def count_duplicates(self, pl_data) -> 'int':
        """
        get a count of the number of playlist titles associated with this path
        that have the same title, but exclude playlist_id from the list
        """
        con = DB_CONNECTION.query_begin()
        count = self.playlist.count_duplicates(pl_data.get_title(),
                                               pl_data.get_path(),
                                               pl_data.get_id(),
                                               con)
        DB_CONNECTION.query_end(con)
        return count[0]

    def exists_in_path(self, pl_data) -> 'bool':
        """tell if any playlists are associated with this path"""
        if self.get_by_path(pl_data) is not None:
            return True
        return False

    def get_by_path(self, pl_data) -> '[PlaylistData, ...]':
        """get playlists associated with path"""
        playlists = []
        con = DB_CONNECTION.query_begin()
        # execute query
        pl_list = self.playlist.get_rows_by_path(con, pl_data.get_path())
        DB_CONNECTION.query_end(con)
        # build playlists list
        for plst in pl_list:
            play_list = PlaylistData(title=plst['title'], path=plst['path'], id_=plst['id'])
            playlists.append(play_list)
        return playlists

    def save(self, pl_data) -> 'playlist_id:int':
        """"insert or update playlist"""
        con = DB_CONNECTION.query_begin()
        id_ = pl_data.get_id()
        if self.playlist.get_row(con, id_) is None:
            id_ = self.playlist.insert(con, pl_data.get_title(), pl_data.get_path())
        else:
            self.playlist.update(con, pl_data.get_title(), pl_data.get_path(), id_)
        DB_CONNECTION.query_end(con)
        return id_


class TrackDBI():
    """
    Class to interface the database with the rest of the module.
    manage the connections to the database table classes.
    manage converting the data to module specific format(Track) for
    consumption by the other classes in this module.
    """

    def __init__(self):
        """create database table objects"""
        self.pl_track = audio_book_tables.PlTrack()
        self.pl_track_metadata = audio_book_tables.PlTrackMetadata()
        self.playlist = audio_book_tables.Playlist()
        self.track_file = audio_book_tables.TrackFile()

    def save_track_file(self, track) -> 'track_file_id:int':
        """
        save to database track_file information held in Track
        returns track_file_id
        """
        con = DB_CONNECTION.query_begin()
        # add entry to track_file table
        self.track_file.add_row(con, path=track.get_file_path())
        track_file_id = self.track_file.get_id_by_path(con, track.get_file_path())['id']
        DB_CONNECTION.query_end(con)
        return track_file_id

    def save_pl_track(self, playlist_id, track_file_id, track) -> 'int':
        """add entry to pl_track table"""
        con = DB_CONNECTION.query_begin()
        track_number = track.get_number()
        # null pl_track_numbers to avoid duplicates in case they were reordered in the view
        self.pl_track.null_duplicate_track_number(con, playlist_id, track_number)
        pl_track_id = track.get_pl_track_id()
        if pl_track_id:
            self.pl_track.update_track_number_by_id(con, track_number, pl_track_id)
        else:
            pl_track_id = self.pl_track.add(con, playlist_id, track_number, track_file_id)
        DB_CONNECTION.query_end(con)
        return pl_track_id

    def save_track_metadata(self, md_entry, pl_track_id, key):
        """save a TrackMDEntry instance to database"""
        con = DB_CONNECTION.query_begin()
        # extract info from TrackMDEntry oject
        id_ = md_entry.get_id()
        index = md_entry.get_index()
        entry = md_entry.get_entry()

        # find an existing entry that matches id
        e_entry = self.pl_track_metadata.get_row_by_id(con, id_)
        if e_entry:
            # only update if there is an actual change
            if e_entry['idx'] != index:
                # rotate indices and update row in table
                self.pl_track_metadata.null_duplicate_indices(con, pl_track_id, index, key)
                self.pl_track_metadata.update_row(con, pl_track_id, id_, entry, index, key)
            elif e_entry['entry'] != entry:
                # indices already match, simply update row
                self.pl_track_metadata.update_row(con, pl_track_id, id_, entry, index, key)
        else:
            # rotate indices and add new row to table
            self.pl_track_metadata.null_duplicate_indices(con, pl_track_id, index, key)
            # update md_entry with id returned from new row
            id_ = self.pl_track_metadata.add_row(con, pl_track_id, entry, index, key)
        DB_CONNECTION.query_end(con)
        return id_

    def remove_deleted_metadata(self, max_index, pl_track_id, key):
        """
        remove deleted entries from table.pl_track_metadata by looking for null indices
        and indices greater than the current max_index
        """
        con = DB_CONNECTION.query_begin()
        id_list = self.pl_track_metadata.get_ids_by_max_index_or_null(con, max_index, pl_track_id, key)
        for row in id_list:
            self.pl_track_metadata.remove_row_by_id(con, row['id'])
        DB_CONNECTION.query_end(con)

    def remove_deleted_pl_tracks(self, playlist_id, max_index):
        """
        remove deleted entries from table.pl_track by looking for null indices
        pl_track.track_number entries are a one based index
        """
        con = DB_CONNECTION.query_begin()
        id_list = self.pl_track.get_ids_by_max_index_or_null(con, max_index, playlist_id)
        for row in id_list:
            self.pl_track.remove_row_by_id(con, row['id'])
        DB_CONNECTION.query_end(con)

    def get_track_list_by_pl_id(self, playlist_id) -> '[playlist.Track, ...]':
        """create list of Track objects by searching the database for pl_tracks matching playlist ids"""
        track_list = []
        con = DB_CONNECTION.query_begin()
        # create Track instances and populate the simple instance variables
        for trak in self.pl_track.get_rows_by_playlist_id(con, playlist_id):
            path = self.track_file.get_row_by_id(con, trak['track_id'])['path']
            track = playlist.Track(file_path=path)
            track.set_number(trak['track_number'])
            track.set_pl_track_id(trak['id'])
            track_list.append(track)
        DB_CONNECTION.query_end(con)
        return track_list

    def get_metadata_list(self, key, pl_track_id):
        """create a list of TrackMDEntry by searching for pl_track_id"""
        md_list = []
        con = DB_CONNECTION.query_begin()

        # find an existing entry that matches pl_track_id
        entry_l = self.pl_track_metadata.get_rows(con, key, pl_track_id)
        for row in entry_l:
            md_entry = playlist.TrackMDEntry()
            md_entry.set_id(row['id'])
            md_entry.set_index(row['idx'])
            md_entry.set_entry(row['entry'])
            md_list.append(md_entry)
        DB_CONNECTION.query_end(con)
        return md_list


class UnsupportedFileType(Exception):
    """
    custom exception raised when TrackFi tries to scrape data from an unsupported file type
    """


class TrackFI:
    """
    Track File Interface
    factory class to populate Track objects with data pulled from audio files
    """
    # audio_file_types is the list of file extensions supported by book_ease
    audio_file_types = ('.flac', '.opus', '.loss', '.aiff', '.ogg', '.m4b', '.mp3', '.wav')
    # build compiled regexes for matching list of media suffixes.
    f_type_re = []
    for i in audio_file_types:
        i = '.*.\\' + i.strip() + '$'
        f_type_re.append(re.compile(i))
    # get a TrackMDEntryFormatter for fixing known formatting issues in file metadata
    entry_formatter = playlist.TrackMDEntryFormatter()

    @classmethod
    def get_track(cls, path) -> 'Track':
        """
        create and return a track populated with file data and metadata
        Raises exception if path does not represent a media file
        """
        if not cls.is_media_file(path):
            raise UnsupportedFileType(path, 'is not a supported file type')
        track = playlist.Track(file_path=path)
        # populate Track.metadata
        TrackFI.load_metadata(track)

        return track

    @classmethod
    def load_metadata(cls, track):
        """
        load passed in Track instance with media file metadata.
        mutagen returns a dict where each property value is a list of entries.
        Track obojects implement this with as dict:list:TrackMDEntry(index, entry, id)

        Note: id will be populated when saving to the db
        """
        metadata = mutagen.File(track.get_file_path(), easy=True)
        for key in metadata:
            md_entry_list = []
            for i, entry in enumerate(metadata[key]):
                # get function for fixing common formatting issues found in file metadata
                format_entry = cls.entry_formatter.get_md_entry_formatter(key)
                # create a new TrackMDEnty with the mutagen data
                md_entry = playlist.TrackMDEntry(index=i, entry=format_entry(entry))
                md_entry_list.append(md_entry)
            # assign the copied list of metadata entries to the track
            track.set_entry(key, md_entry_list)

    @classmethod
    def is_media_file(cls, file_):
        """determine is file_ matches any of the media file definitions"""
        for i in cls.f_type_re:
            if i.match(file_):
                return True
        return False


class BookC:
    """
    This class handles comms between Book module and Book_reader
    This class coordinates actions among the component view controllers
    Tis class instantiates the Book model and handles the signals sent from the model
    """

    #the list of signals that BookC is allowed to send to the component views
    book_tx_api = ['update', 'get_view', 'close', 'begin_edit_mode', 'begin_display_mode', 'save_title', 'save']
    # the list of signals that the component views is allowed to send to BookC
    component_tx_api = ['save_button', 'cancel_button', 'edit_button', 'close']

    def __init__(self, path, file_list, book_reader):
        # the model
        self.book = Book(path, file_list)
        # allow BookReader to track BookC's position in its books list
        self.index = None

        # set up the callback system in the observer interface of the component view controllers
        # This makes it so that the component views only have to call the signal name and not do any other setup.
        self.component_transmitter = signal_.Signal()
        for handle in self.component_tx_api:
            self.component_transmitter.add_signal(handle)
            self.component_transmitter.connect(handle, self.receive, handle)

        # instantiate the component_views observable.
        self.transmitter = signal_.Signal()
        # register the outgoing signals that go to the component views.
        # Each of the component views now just need to connect to the signals they want to subscribe to.
        for handle in self.book_tx_api:
            self.transmitter.add_signal(handle)

        # create the main view.
        # the main view does not use the component_transmitter because it has nothing to say.
        # It does have a get_gui_builder method that will be used to allow the component views control of their
        # particular views.
        self.book_vc = book_view.BookVC(self.transmitter)
        book_view_builder = self.book_vc.get_gui_builder()

        # create the component view controllers.
        # title view
        book_view.TitleVC(self.book, self.transmitter, self.component_transmitter, book_view_builder)
        # control button view
        book_view.ControlBtnVC(self.book, self.transmitter, self.component_transmitter, book_view_builder)
        # playlist view
        book_view.PlaylistVC(self.book, self.transmitter, self.component_transmitter, book_view_builder)
        # pinned button view does not use the component_transmitter because it is responsible for signalling its own
        # controller.
        book_reader.pinned_books.get_pinned_button_new(self.transmitter, book_view_builder)

    def get_view(self):
        """get the main outer most view"""
        return self.book_vc.get_view()

    def get_playlist_id(self):
        """get this book instance's unique id"""
        return self.book.playlist_data.get_id()

    def set_index(self, index):
        """save position in BookReader.books"""
        self.index = index

    def get_index(self):
        """return position in BookReader.books"""
        return self.index

    def open_new_playlist(self):
        """Create a new playlist from media files"""
        book_data = self.book.create_book_data()
        self.transmitter.send('update', book_data)
        self.transmitter.send('begin_edit_mode')

    def get_title(self):
        """get this books title from the model"""
        return self.book.playlist_data.get_title()

    def open_existing_playlist(self, playlist_data):
        """open a previously saved book"""
        book_data = self.book.book_data_load(playlist_data)
        self.transmitter.send('update', book_data)
        self.transmitter.send('begin_display_mode')

    def save(self):
        """Coordinate the saving of the book with Book and the the VC classes"""
        book_data = BookData(self.book.playlist_data)
        # notify the VC classes that they need to save
        self.transmitter.send('save', book_data)
        self.book.save(book_data)
        # Tell the book that it is finished saving and can cleanup
        reloaded_book_data = self.book.book_data_load(self.book.playlist_data)
        # tell the VC classes to update their views and switch to display mode
        self.transmitter.send('update', reloaded_book_data)
        self.transmitter.send('begin_display_mode')

    def edit(self):
        """Inform the component views that they need to enter edit_mode"""
        self.transmitter.send('begin_edit_mode')

    def cancel_edit(self):
        """close book if it is not saved or tell component views to enter display mode"""
        if self.book.is_saved():
            self.book.book_data_load(self.book.playlist_data)
            self.transmitter.send('begin_display_mode')
        else:
            self.transmitter.send('close')

    def close_book(self):
        """Tell the component controllers to close"""
        self.transmitter.send('close')

    def receive(self, control_signal):
        """convert signals from the component views into actions by calling the appropriate methods"""
        match control_signal:
            case 'save_button':
                self.save()
            case 'cancel_button':
                self.cancel_edit()
            case 'edit_button':
                self.edit()
            case 'close':
                self.close_book()
