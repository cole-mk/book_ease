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
import playlist
import signal_
import db
import sqlite3
import re
import os
import sqlite_tables


# module wide db connection for multi queries
__db_connection = None

def multi_query_begin():
    """
    create a semi-persistent connection
    for executing multiple transactions
    """
    print('multi_query_begin')
    global __db_connection
    if __db_connection is not None:
        raise RuntimeError('connection already exists')
    else:
        __db_connection = sqlite_tables.create_connection()

def multi_query_end():
    """commit and close connection of a multi_query"""
    global __db_connection
    if __db_connection is None:
        raise RuntimeError('connection doesn\'t exist')
    else:
        __db_connection.commit()
        __db_connection.close()
        __db_connection = None

def _query_begin() -> 'sqlite3.Connection':
    """
    get an sqlite connection object
    returns __db_connection if a multi_query is in effect.
    Otherwise, create and return a new connection
    """
    global __db_connection
    if __db_connection is None:
        return sqlite_tables.create_connection()
    else:
        return __db_connection

def _query_end(con):
    """
    commit and close connection if a multi_query
    is not in effect.
    """
    global __db_connection
    if con is not __db_connection:
        con.commit()
        con.close()

# The Playlist Data Column Setup
pl_title    = {'name':'Title',         'col':0,
               'g_typ':str,            'editable':True,
               'table':'track_title',  'field':'title',
               'key':'title',  'alt_keys':['album']}

pl_author   = {'name':'Author',            'col':1,
               'g_typ':str,                'editable':True ,
               'table':'track_author',     'field':'author',
               'key':'author',             'alt_keys':['artist', 'performer', 'composer']}

pl_read_by  = {'name':'Read by',           'col':2,
               'g_typ':str,                'editable':True ,
               'table':'track_read_by',    'field':'read_by',
               'key':'performer',          'alt_keys':['author', 'artist', 'composer']}

pl_length   = {'name':'Length',            'col':3,
               'g_typ':str,                'editable':True ,
               'table':'track_length',     'field':'length',
               'key':'length',             'alt_keys':[None]}

pl_track    = {'name':'Track',             'col':4,
               'g_typ':str,                'editable':True ,
               'table':'track_number',     'field':'number',
               'key':'tracknumber',        'alt_keys':[None]}

pl_file     = {'name':'File',      'col':5,
               'g_typ':str,        'editable':False,
               'table':'track',    'field':'filename',
               'key':'file',       'alt_keys':[None]}

pl_row_id   = {'name':'pl_row_id',     'col':6,
               'g_typ':int,            'editable':True ,
               'table':None,           'field':None,
               'key':'pl_row_id',      'alt_keys':[None]}

pl_path      = {'name':'pl_path',  'col':7,
               'g_typ':str,        'editable':False ,
               'table':'track',    'field':'path',
               'key':None,         'alt_keys':[None]}

pl_saved_col_list = [pl_title,  pl_author, pl_read_by,
                     pl_length, pl_track,  pl_file, pl_path]

metadata_col_list =[pl_title,  pl_author, pl_read_by,
                    pl_length, pl_track]


# TODO: file_list can be removed from the constructor all together. create_book can get it from self.files
class Book(playlist.Playlist, signal_.Signal_):
    def __init__(self, path, file_list, config, files, book_reader):
        playlist.Playlist.__init__(self)
        signal_.Signal_.__init__(self)
        self.index = None
        self.playlist_data = PlaylistData(title='New Book', path=path)
        self.config = config
        self.files = files
        self.book_section = 'books'
        self.book_reader = book_reader
        #database interfaces
        self.track_dbi = TrackDBI()
        self.playlist_dbi = PlaylistDBI()
        # track metadata
        self.file_list = file_list
        # playlist_filetypes key has values given in a comma separated list
        file_types = config[self.book_section]['playlist_filetypes'].split(",")
        # build compiled regexes for matching list of media suffixes.
        self.f_type_re = []
        for i in file_types:
            i = '.*.\\' + i.strip() + '$'
            self.f_type_re.append(re.compile(i))

        # initialize the callback system
        self.add_signal('book_data_loaded')
        self.add_signal('book_data_created')
        self.add_signal('book_saved')


    # get list of playlists associated with current path
    def get_cur_pl_list(self):
        return self.playlist_dbi.get_by_path()

    def get_playlist_data(self) -> 'PlaylistData':
        # get playlist data attached to this Book instance
        return self.playlist_data

    def get_playlist_id(self):
        """get this book instance's unique id"""
        return self.playlist_data.get_id()

    def get_track_list(self):
        return self.track_list

    def get_index(self):
        return self.index

    def set_index(self, index):
        self.index = index

    def assert_playlist_exists(self, playlist_data):
        # assert that playlist actually exists before trying to load
        # raising exception f not found
        found_playlist = None
        for pl in self.get_cur_pl_list():
            if pl.get_id() == playlist_data.get_id():
                found_playlist = pl
                break
        if found_playlist == None:
            raise KeyError(self.playlist_data.get_id(), 'not found in currently saved playlists associated with this path')

    def book_data_load(self, playlist_data):
        # load a saved playlist from the database
        self.db.cur_pl_path['col']

        # check that playlist actually exists before trying to load
        self.assert_playlist_exists(playlist_data)
        self.playlist_data = playlist_data

        track_list = self.db.playlist_get_tracks(self.playlist_data.get_id())
        # move track data from database into internal tracklist
        for i, tr in enumerate(track_list):
            file_path = self.db.track_get_path(tr['track_id'])
            track = playlist.Track(file_path)
            track.set_pl_row_id(tr['id'])
            track.set_saved(True)
            track.set_row_num(tr['track_number'])
            self.track_list.append(track)
            # move the track attributes(metadata) from db to tracklist
            for col in metadata_col_list:
                entries = self.db.track_metadata_get(tr['id'], col['key'])
                tr_entries_list = []
                for entry in entries:
                    tr_entries_list.append(entry['entry'])
                track.set_entry(col['key'], tr_entries_list)
        # playlist is now a saved playlist
        self.saved_playlist = True
        # sort playlist by  row_num
        self.track_list_sort_row_num()
        # notify listeners that book data has been loaded
        self.signal('book_data_loaded')

    # initialize the playlist
    def create_book_data(self, callback=None, **kwargs):
        #dont enumerate filelist, we nee more control over i
        i = 0
        for f in self.file_list:
            # populate playlist data
            file_path = os.path.join(self.playlist_data.get_path(), f[1])
            if not f[self.files.is_dir_pos] and self.book_reader.is_media_file(file_path):
                track = playlist.Track(file_path)
                track.load_metadata_from_file()
                track.set_pl_row_id(i)
                # do the appending
                self.track_list.append(track)
                i+=1
                # check for alt values if this entry is empty
                for col in pl_saved_col_list:
                    if not track.get_entries(col['key']):
                        #has_entry = False
                        for k in col['alt_keys']:
                            val = track.get_entries(k)
                            if val:
                               track.set_entry(col['key'], val)
                               break
        # set book title from the first track title
        title_list = self.track_list[0].get_entries('title')
        if title_list:
            self.playlist_data.set_title(title_list[0].get_entry())
        # emit book_data_created signal
        self.signal('book_data_created')

    def track_list_update(self, track):
        # find existing track
        e_track = None
        for tr in self.track_list:
            if tr.get_pl_row_id() == track.get_pl_row_id():
                e_track = tr
                break
        if e_track == None:
            # add new track
            self.track_list.append(track)
        else:
            # modify existing track
            [e_track.set_entry(key, track.get_entries(key)) for key in track.get_key_list()]
            e_track.set_row_num(track.get_row_num())

    def get_unique_playlist_title(self, playlist_data) -> 'title:str':
        # add a incremented suffix to playlist title if there are duplicates
        title = playlist_data.get_title()
        suffix = ''
        ct = 1
        while self.playlist_dbi.count_duplicates(playlist_data) > 0:
            title = title.rstrip(suffix)
            suffix = '_' + str(ct)
            title = title + suffix
            ct += 1
        return title


    def save(self, title):
        # start a semi-persistent database connection
        multi_query_begin()
        # add suffix to book title to ensure uniqueness
        self.playlist_data.set_title(self.get_unique_playlist_title(self.playlist_data))
        # save playlist title, storing new id in self.playlist_data
        self.playlist_data.set_id(self.playlist_dbi.save(self.playlist_data))

        # save Track objects to database
        for track in self.track_list:
            # save the file path that the Track object references
            track_file_id = self.track_dbi.save_track_file(track)
            # save the simple Track instance variables
            pl_row_id = self.track_dbi.save_pl_track(self.playlist_data.get_id(), track_file_id, track)
            # update pl_row_id in the Track instance
            track.set_pl_row_id(pl_row_id)

            # save the Track metadata
            for col in metadata_col_list:
                md_entry_l = track.get_entries(col['key'])
                for md_entry in md_entry_l:
                    self.track_dbi.save_track_metadata(md_entry, pl_row_id, col['key'])
                # remove deleted entries from database
                self.track_dbi.remove_deleted_metadata(len(md_entry_l) - 1, pl_row_id, col['key'])
        # remove deleted entries from database
        self.track_dbi.remove_deleted_pl_tracks(self.playlist_data.get_id(), len(self.track_list))
        self.saved_playlist = True

        # reload the list of playlist names saved relative to this books directory
        # inform DBI module that multi query is finished
        multi_query_end()
        self.track_list_sort_row_num()
        # notify any listeners that the playlist has been saved
        self.signal('book_saved')


class Book_DB(db._DB):
    """Database accessing implementation class that serves Book class"""

    def __init__(self):
        """create database tables used by this class by calling an init function for each of the tables"""
        db._DB.__init__(self)

    def init_tables(self):
        """create database tables used by this class by calling an init function for each of the tables"""
        con = self.create_connection()
        self.init_table_playlist(con)
        self.init_table_track(con)
        self.init_table_pl_track(con)
        self.init_table_pl_track_metadata(con)

    def init_table_playlist(self, con):
        """create database table: playlist"""
        sql = '''
                CREATE TABLE playlist (
                    id INTEGER PRIMARY KEY ON CONFLICT ROLLBACK AUTOINCREMENT NOT NULL,
                    title       TEXT NOT NULL,
                    path        TEXT NOT NULL,
                    UNIQUE (
                        title,
                        path
                    )
                    ON CONFLICT ROLLBACK
                )
                '''
        try:
            with con:
                con.execute(sql)
        except sqlite3.OperationalError as e:
            # table already exists
            pass

    def init_table_track(self, con):
        """create database table: track"""
        sql = """
                CREATE TABLE track (
                    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    path     TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    UNIQUE (
                        path,
                        filename
                    )
                )
                """
        try:
            with con:
                con.execute(sql)
        except sqlite3.OperationalError:
            # table already exists
            pass

    def init_table_pl_track(self, con):
        """create database table: pl_track"""
        sql = """
                CREATE TABLE pl_track (
                    id INTEGER PRIMARY KEY ON CONFLICT ROLLBACK AUTOINCREMENT NOT NULL,
                    playlist_id  INTEGER REFERENCES playlist (id)
                                        NOT NULL,
                    track_number INTEGER,
                    track_id     INTEGER NOT NULL REFERENCES track(id),
                    UNIQUE (
                        playlist_id,
                        track_number
                    )
                )
                """
        try:
            with con:
                con.execute(sql)
        except sqlite3.OperationalError:
            # table already exists
            pass

    def init_table_pl_track_metadata(self, con):
        """create database table: pl_track"""
        sql = """
                CREATE TABLE  pl_track_metadata (
                    id          INTEGER PRIMARY KEY ON CONFLICT ROLLBACK AUTOINCREMENT
                                    UNIQUE
                                    NOT NULL,
                    pl_track_id    INTEGER REFERENCES pl_track (id)
                                    NOT NULL,
                    entry      TEXT NOT NULL,
                    ent_index      INTEGER NOT NULL,
                    _key      TEXT NOT NULL,
                    UNIQUE (
                       pl_track_id,
                       ent_index,
                       _key
                   )
                  ON CONFLICT ROLLBACK
                )
                """
        try:
            with con:
                con.execute(sql)
        except sqlite3.OperationalError as e:
            # table already exists
            pass

    def playlist_exists(self, path):
        if self.playlist_get_by_path(path) is not None:
            return True
        return False

    def track_get_path(self, track_id):
        con = self.create_connection()
        if con is None:
            return None
        sql = """
            SELECT path FROM track
            WHERE id = (?)
            """
        try:
            cur = con.execute(sql, (track_id,))
            path = cur.fetchone()[0]
        except sqlite3.IntegrityError as e:
            path = None
            print('SELECT id FROM', md_table_name, e)
        con.close()
        return path


    def track_metadata_set_primary(self, primary_index, track, key, pl_track_id, cur):
        # a track metadata table
        if primary_index is not None:
            # get the id of the primary entry
            sql = """
                SELECT id FROM pl_track_metadata
                WHERE   pl_track_id = (?)
                AND     ent_index = (?)
                AND     _key = (?)
                """
            track_primary_id = None
            try:
                cur.execute(sql, (pl_track_id, primary_index, key))
                row = cur.fetchone()
                track_primary_id = None
                if row is not None:
                    track_primary_id = row['id']
            except sqlite3.IntegrityError as e:
                print('SELECT id FROM', md_table_name, e)

            # save primary entry, insert or update
            if track_primary_id is not None:
                primary_id = None
                sql = """
                    INSERT INTO primary_metadata(pl_track_id, pl_track_metadata_id, pl_track_metadata_key)
                    VALUES (?,?,?)
                    """
                try:
                    cur.execute(sql, (pl_track_id, track_primary_id, key))
                    primary_id = cur.lastrowid
                except sqlite3.IntegrityError as e:
                    print('track_metadata_add()primary_metadata error', e)

                if primary_id is None:
                    sql = """
                        UPDATE  primary_metadata
                        SET     pl_track_metadata_id = (?)
                        WHERE   pl_track_id = (?)
                        AND     pl_track_metadata_key = (?)
                        """
                    try:
                        cur.execute(sql, (track_primary_id, pl_track_id, key))
                    except sqlite3.Error as e:
                        print("track_metadata_add() update error", e)

    def track_metadata_get(self, pl_track_id, key):
        con = self.create_connection()
        if con is None:
            return None
        #cur = con.cursor()
        sql = """
            SELECT * FROM pl_track_metadata
            WHERE pl_track_id = (?)
            AND _key = (?)
            ORDER BY
            ent_index ASC
            """

        try:
            #cur.execute("""BEGIN""")
            cur = con.execute(sql, (pl_track_id,key))
            playlist = cur.fetchall()
        except sqlite3.Error as e:
            print("playlist_get_tracks() error", e)
            playlist = []
        return playlist



    def track_metadata_add(self, track_id, entries, key, pl_track_id, cur): #field = key
        if cur is None:
            return None
        #TODO: remove previous occurances of pl_track_id, _key
        #TODO: inseert new list of  pl_track_id, entry, ent_index, _key
        sql = """
            DELETE FROM pl_track_metadata
            WHERE pl_track_id = (?)
            AND   _key = (?)
            """
        # add each track metadata entry into its respective table
        try:
            cur.execute(sql, (pl_track_id, key))
        except sqlite3.Error as e:
            print('track_metadata_add DELETE error', e)
        try:
            if len(entries) > 0:
                for ent_index, entry in enumerate(entries):
                    if entry is None:
                        continue
                    # pl_track metadata table
                    sql = """
                        INSERT INTO pl_track_metadata(pl_track_id, entry, ent_index, _key)
                        VALUES (?,?,?,?)
                        """
                    cur.execute(sql, (pl_track_id, entry, ent_index, key))
        except sqlite3.Error as e:
            print('track_metadata_add', e)

    def track_add(self, path, filename, cur):
        if cur is None:
            return None
        track_id = None

        # insert track and retrieve new track_id
        sql = """
              INSERT INTO track(path, filename)
              VALUES (?,?)
              """
        try:
            cur.execute(sql, (path, filename))
            track_id = cur.lastrowid
        except sqlite3.IntegrityError as e:
            pass

        # get track id if the track was pre-existing
        if track_id is None:
            sql = """
                    SELECT id FROM track
                    WHERE path = (?)
                    AND filename = (?)
                    """
            try:
                cur.execute(sql, (path, filename))
                track_id = cur.fetchone()['id']
            except sqlite3.Error as e:
                print(e)
        return track_id

    def playlist_get_tracks(self, playlist_id):
        con = self.create_connection()
        cur = con.cursor()
        sql = """
            SELECT * FROM pl_track
            WHERE playlist_id = (?)
            ORDER BY track_number ASC
            """
        try:
            cur.execute(sql, (playlist_id,))
            playlist = cur.fetchall()
        except sqlite3.Error as e:
            print("playlist_get_tracks() error", e)
            playlist = []
        return playlist


    def playlist_get_by_path(self, path):
        con = self.create_connection()
        cur = con.cursor()
        sql = """
            SELECT * FROM playlist
            WHERE path = (?)
            """
        try:
            cur.execute(sql, (path,))
            playlist = cur.fetchall()
        except sqlite3.Error as e:
            print("playlist_get_by_path() error", e)
            playlist = []
        return playlist

    def playlist_update(self, title, path, playlist_id, cur):
        #con = sqlite3.connect(self.db)
        pl_id = None
        try:
            sql = """
                    UPDATE playlist
                    SET title = ?
                    WHERE id = ?
                    """
            cur.execute(sql, (title, playlist_id))
            pl_id = playlist_id
        except sqlite3.IntegrityError:
            print("playlist", title, "already exists at", path)
        return pl_id

    def playlist_track_update(self, playlist_id, track_number, track_id, _id, cur):
        if cur is None:
            return None

        lastrowid = None

        # look for what will be a duplicate track_num and change it to NULL
        sql = """
            UPDATE pl_track
            SET track_number = (?)
            WHERE playlist_id = (?)
            AND  track_number = (?)
            """
        try:
            cur.execute(sql, (None, playlist_id, track_number))
        except sqlite3.Error as e:
            print("playlist_track_add() duplicate error", e)

        success = False
        # update track
        sql = """
            UPDATE pl_track
            SET track_id = (?), track_number = (?)
            WHERE id = (?)
            """
        try:
            cur.execute(sql, (track_id, track_number, _id))
            success = True
        except sqlite3.Error as e:
            print("playlist_track_add() update error", e)

        if success:
            sql = """
                SELECT id
                FROM pl_track
                WHERE playlist_id = (?)
                AND track_number = (?)
                """
            try:
                cur.execute(sql, (playlist_id, track_number))
                row = cur.fetchone()
                if row != None:
                    lastrowid = row['id']
            except sqlite3.Error as e:
                print("playlist_track_add()update error", e)

        return lastrowid

    def playlist_track_remove_deleted(self, playlist_id, playlist_len, cur):
        if cur is None:
            return None
        sql = """
            DELETE FROM pl_track
            WHERE playlist_id = (?)
            AND (track_number >= (?) OR track_number IS NULL)
            """
        cur.execute(sql, (playlist_id, playlist_len))

    def playlist_track_add(self, playlist_id, track_number, track_id, _id, cur):
        #con = self.create_connection()
        if cur is None:
            return None
        # insert track
        sql = """
              INSERT INTO pl_track(playlist_id, track_number, track_id)
              VALUES (?,?,?)
              """
        lastrowid = None
        try:
            cur.execute(sql, (playlist_id, track_number, track_id))
            lastrowid = cur.lastrowid
        except sqlite3.IntegrityError as e:
            pass

        return lastrowid

    def playlist_insert(self, playlist_data, cur):
        lastrowid = None
        try:
            cur.execute("INSERT INTO playlist(title, path) VALUES (?,?)", (title, path))
            lastrowid = cur.lastrowid
        except sqlite3.IntegrityError:
            print("couldn't add", playlist_data.get_title(), playlist_data.get_path(),"twice")
        return lastrowid

    def playlist_count_duplicates(self, title, path, playlist_id, cur):
        if playlist_id == None:
            playlist_id = 'NULL'

        sql = """
            SELECT COUNT(*) FROM playlist
            WHERE title = (?)
            AND path = (?)
            AND id != (?)
            """
        cur.execute(sql, (title, path, playlist_id))
        ct = cur.fetchone()
        return ct[0]


class PlaylistDBI():

    def __init__(self):
        self.playlist = sqlite_tables.Playlist()

    def count_duplicates(self, pl_data) -> 'int':
        # get a count of the number of playlist titles associated with this path
        # that have the same title, but exclude playlist_id from the list
        con = _query_begin()
        count = self.playlist.count_duplicates(pl_data.get_title(),
                                               pl_data.get_path(),
                                               pl_data.get_id(),
                                               con)
        _query_end(con)
        return count[0]

    def exists_in_path(self, pl_data) -> 'bool':
        # tell if any playlists are associated with this path
        if self.get_by_path(pl_data) is not None:
            return True
        return False

    def get_by_path(self, pl_data) -> 'PlaylistData':
        # get playlists associated with path
        playlists = []
        con = _query_begin()
        # execute query
        pl_list = self.playlist.get_rows_by_path(con, pl_data.get_path())
        _query_end(con)
        # build playlists list
        for pl in pl_list:
            playlist = PlaylistData(title=pl['title'], path=pl['path'], id_=pl['id'])
            playlists.append(playlist)
        return playlists

    def save(self, pl_data) -> 'playlist_id:int':
        # insert or update playlist
        con = _query_begin()
        id_ = self.playlist.replace(con, pl_data.get_title(), pl_data.get_path())
        _query_end(con)
        return id_


class PlaylistData:

    def __init__(self, title=None, path=None, id_=None):
        self.title = title
        self.path = path
        self.id_ = id_

    def get_title(self):
        return self.title

    def set_title(self, title):
        self.title = title

    def get_path(self):
        return self.path

    def set_path(self, path):
        self.path = path

    def get_id(self):
        return self.id_

    def set_id(self, id_):
        self.id_ = id_


class TrackDBI():
    # Class to interface the database with the rest of the module.
    # manage the connections to the database table classes.
    # manage converting the data to module specific format(Track) for
    # consumption by the other classes in this module.

    def __init__(self):
        # create database table objects
        self.pl_track = sqlite_tables.PlTrack()
        self.pl_track_metadata = sqlite_tables.PlTrackMetadata()
        self.playlist = sqlite_tables.Playlist()
        self.track_file = sqlite_tables.TrackFile()

    def save_track_file(self, track) -> 'int':
        # save to database track_file information held in Track
        # returns track_file_id
        con = _query_begin()
        # add entry to track_file table
        track_file_id = self.track_file.add_row(con, path=track.get_file_path())
        if track_file_id == 0:
            # track_file already exists, get id
            # id for file currently does not need to be saved to Track() object
            # as the lookup is simple and its only used here in this class
            track_file_id = self.track_file.get_id_by_path(con, track.get_file_path())
        _query_end(con)
        return track_file_id

    def save_pl_track(self, playlist_id, track_file_id, track) -> 'int':
        # add entry to pl_track table
        con = _query_begin()
        track_num = track.get_row_num()
        # null pl_track_numbers to avoid duplicates in case they were reordered in the view
        self.pl_track.null_duplicate_track_number(con, playlist_id, track_num)
        pl_row_id = self.pl_track.add(con, playlist_id, track_num, track_file_id)
        if pl_row_id == 0:
            # track already exists, update playlist track numbers
            pl_row_id = track.get_id()
            self.pl_track.update_track_number_by_id(con, track_number, pl_row_id)
        _query_end(con)
        return pl_row_id

    def save_track_metadata(self, md_entry, pl_track_id, key):
        # save a TrackMDEntry instance to database
        con = _query_begin()
        # extract info from TrackMDEntry oject
        id_ = md_entry.get_id()
        index = md_entry.get_index()
        entry = md_entry.get_entry()

        # find an existing entry that matches id
        e_entry = self.pl_track_metadata.get_row_by_id(con, id_)
        if not e_entry:
            # rotate indices and add new row to table
            self.pl_track_metadata.null_duplicate_indices(con, pl_track_id, index, key)
            # update md_entry with id returned from new row
            id_ = self.pl_track_metadata.add_row(con, pl_track_id, entry, index, key)
        else:
            # only update if there is an actual change
            if e_entry['index'] != index:
                # rotate indices and update row in table
                self.pl_track_metadata.null_duplicate_indices(con, pl_track_id, index, key)
                self.pl_track_metadata.update_row(con, id_, entry, index, key)
            elif e_entry['entry'] != entry:
                # indices already match, simply update row
                self.pl_track_metadata.update_row(con, id_, entry, index, key)
        _query_end(con)

    def remove_deleted_metadata(self, max_index, pl_track_id, key):
        # remove deleted entries from table.pl_track_metadata by looking for null indices
        # and indices greater than the current max_index
        con = _query_begin()
        id_list = self.pl_track_metadata.get_ids_by_max_index_or_null(con, max_index, pl_track_id, key)
        [self.pl_track_metadata.remove_row_by_id(con, row['id']) for row in id_list]
        _query_end(con)

    def remove_deleted_pl_tracks(self, playlist_id, max_index):
        # remove deleted entries from table.pl_track by looking for null indices
        # pl_track.track_number entries are a one based index
        con = _query_begin()
        id_list = self.pl_track.get_ids_by_max_index_or_null(con, max_index, playlist_id)
        print('remove_deleted_pl_tracks', id_list)
        [self.pl_track.remove_row_by_id(con, row['id']) for row in id_list]
        _query_end(con)

