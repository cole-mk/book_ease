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
        self.title = 'New Book'                 #####
        self.playlist_id = None                 #####
        self.config = config
        self.files = files
        self.book_section = 'books'
        self.path = path                        #####
        self.book_reader = book_reader
        self.db = Book_DB()
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
        return self.db.get_cur_pl_list()

    def get_cur_pl_row(self):
        cur_pl_list = self.get_cur_pl_list()
        cur_pl_row = None
        for row in cur_pl_list:
            if row[self.db.cur_pl_id['col']] == self.playlist_id:
                cur_pl_row = row
                break
        if cur_pl_row == None:
            raise KeyError(self.playlist_id, 'not found in currently saved playlists associated with this path')
        return cur_pl_row

    def get_playlist_id(self):
        """get this book instance's unique id"""
        return self.playlist_id

    def get_track_list(self):
        return self.track_list

    def get_index(self):
        return self.index

    def set_index(self, index):
        self.index = index

    def get_title_l(self, row):
        track = self.track_list[row]
        return track.get_entries(self.title_keys)
    # initialize the playlist

    def book_data_load(self, pl_row):
        # pl_row is row (tuple) from playlist database table (displayed in BookView)
        #TODO: get rid of the g_cols
        self.db.cur_pl_path['col']
        self.title = pl_row[self.db.cur_pl_title['col']]
        self.playlist_id = pl_row[self.db.cur_pl_id['col']]
        self.path = pl_row[self.db.cur_pl_path['col']]
        track_list = self.db.playlist_get_tracks(self.playlist_id)
        # move track data from database into internal tracklist
        for i, tr in enumerate(track_list):
            file_path = self.db.track_get_path(tr['track_id'])
            track = playlist.Track(file_path)
            track.set_entry(pl_row_id['key'], [tr['id']])
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
            file_path = os.path.join(self.path, f[1])
            if not f[self.files.is_dir_pos] and self.book_reader.is_media_file(file_path):
                track = playlist.Track(file_path)
                track.load_metadata_from_file()
                track.set_entry(pl_row_id['key'], [i])
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
            self.title = title_list[0]
        # emit book_data_created signal
        self.signal('book_data_created')

    def track_list_update(self, track):
        # find existing track
        e_track = None
        for tr in self.track_list:
            if tr.get_entries(pl_row_id['key'])[0] == track.get_entries('pl_row_id')[0]:
                e_track = tr
                break
        if e_track == None:
            # add new track
            self.track_list.append(track)
        else:
            # modify existing track
            [e_track.set_entry(key, track.get_entries(key)) for key in track.get_key_list()]
            e_track.set_row_num(track.get_row_num())

    def save(self, title):
        # playlist
        pl_id = None
        con = self.db.create_connection()
        if con is None:
            return None
        try:
            cur = con.cursor()
            cur.execute("""BEGIN""")
            # add a incremented suffix to playlist title if there are duplicates
            suffix = ''
            ct = 1
            while self.db.playlist_count_duplicates(title, self.path, self.playlist_id, cur) > 0:
                title = title.rstrip(suffix)
                suffix = '_' + str(ct)
                title = title + suffix
                ct += 1
            # set book title to incremented value
            self.title = title
            # set playlist title
            if self.playlist_id is None:
                # insert the newly created playlist
                self.playlist_id = self.db.playlist_insert(title, self.path, cur)
            else:
                self.db.playlist_update(title, self.path, self.playlist_id, cur)
            if self.playlist_id is not None:
                self.title = title
                # save playlist tracks,tracks and their metadata
                for track in self.track_list:
                    track_id = self.db.track_add(path=track.get_file_path(), filename=track.get_file_name(), cur=cur)
                    pl_track_num = track.get_row_num()
                    pl_track_id = track.get_entries(pl_row_id['key'])[0]
                    if track_id is not None:
                        if not track.is_saved():
                            pl_track_id = self.db.playlist_track_add(self.playlist_id,
                                                                     pl_track_num,
                                                                     track_id,
                                                                     pl_track_id,
                                                                     cur)
                            track.set_saved(True)
                        else:
                            pl_track_id = self.db.playlist_track_update(self.playlist_id,
                                                                        pl_track_num,
                                                                        track_id,
                                                                        pl_track_id,
                                                                        cur)

                        track.set_entry(self.pl_row_id['key'], [pl_track_id])
                        if pl_track_id is not None:
                            for col in self.metadata_col_list:

                                self.db.track_metadata_add(track_id,
                                                           track.get_entries(col['key']),
                                                           col['key'],
                                                           pl_track_id, cur)

            self.db.playlist_track_remove_deleted(self.playlist_id, len(self.track_list), cur)
            self.saved_playlist = True

        except sqlite3.Error as e:
            print('on_playlist_save', e)
        # reload the list of playlist names saved relative to this books directory
        self.db.set_cur_pl_list_by_path(self.book_reader.cur_path, con)
        con.commit()
        con.close()
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

    def playlist_insert(self, title, path, cur):
        lastrowid = None
        try:
            cur.execute("INSERT INTO playlist(title, path) VALUES (?,?)", (title, path))
            lastrowid = cur.lastrowid
        except sqlite3.IntegrityError:
            print("couldn't add", (title, path),"twice")
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



class PlaylistDBI(sqlite_tables.DBI_):

    __init__(self):
        sqlite_tables.DBI_.__init__(self)
        self.playlist = sqlite_tables.Playlist()

    def count_duplicates(self, pl_data) -> 'int':
        # get a count of the number of playlist titles associated with this path
        # that have the same title, but exclude playlist_id from the list
        con = self._query_begin()
        count = self.playlist.count_duplicates(pl_data.get_title(),
                                               pl_data.get_path(),
                                               pl_data.get_id())
        self._query_end(con)
        return count[0]

    def exists_in_path(self, pl_data) -> 'bool':
        # tell if any playlists are associated with this path
        if self.get_by_path(pl_data) is not None:
            return True
        return False

    def get_by_path(self, pl_data) -> 'PlaylistData':
        # get playlists associated with path
        playlists = []
        con = self._query_begin()
        # execute query
        pl_list = self.playlist.get_rows_by_path(con, pl_data.get_path())
        self._query_end(con)
        # build playlists list
        for pl in pl_list:
            playlist = PlaylistData(title=pl['title'], path=pl['path'], id_=pl['id'])
            playlists.append(playlist)
        return playlists

    def replace(self, pl_data) -> 'playlist_id:int':
        # insert or update playlist
        con = self._query_begin()
        id_ = self.playlist.replace(con, pl_data.get_title(), pl_data.get_path())
        self._query_end(con)
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
