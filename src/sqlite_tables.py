# -*- coding: utf-8 -*-
#
#  sqlite_tables.py
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
from pathlib import Path
import sqlite3

class _SqliteDB:
    """
    Database accessor base class:
    stores the common database path information

    Note: all exceptions are to be propogated to an upper layer
        except for init_tables, usually called from __init__
        in the child class
    
    init_tables()
    create_connection()
    """

    def __init__(self):
        """
        initialize the DB class by setting the db file
        create list to store playlists stored in the "pwd"
        """
        # set database file creating config directory
        config_dir = Path.home() / '.config' / 'book_ease'
        db_dir = config_dir / 'data'
        db_dir.mkdir(mode=511, parents=True, exist_ok=True)
        self.db = db_dir / 'book_ease.db'
        # create the database table used by child class
        con = self.create_connection()
        try:
            with con:
                self.init_table(con)
        except sqlite3.OperationalError:
            # table already exists
            pass
        con.close()


    def init_table(self):
        """
        routine to initialize database tables
        This is an informal interface implemented
        as a pass function in this base class
        """
        pass

    def create_connection(self):
        """ create a sqlite3 connection object and return it"""
        con = None
        try:
            con = sqlite3.connect(self.db, isolation_level=None)
            con.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            print('create_connection() error', e)
        return con


class PinnedPlaylists(_SqliteDB):
    """
    database accessor for table pinned_playlists

    init_table(self, con)
        create database table: pinned_playlists

    get_pinned_playlists(self, con=None):
        retreive entire list of pinned playlists returning sqlite3 row object
    """
    def __init__(self):
        _SqliteDB.__init__(self)

    def init_table(self, con):
        """create database table: pinned_playlists"""
        sql = """
                CREATE TABLE pinned_playlists (
                    id INTEGER PRIMARY KEY ON CONFLICT ROLLBACK AUTOINCREMENT NOT NULL,
                    playlist_id  INTEGER REFERENCES playlist (id)  ON DELETE CASCADE
                                         UNIQUE ON CONFLICT ROLLBACK NOT NULL
                )
                """
        con.execute(sql)

    def has_playlist(self, con, playlist_id):
        """
        determine if playlist_id is stored in pinned_playlists table
        returns bool
        """

        sql = """
            SELECT * FROM pinned_playlists
            WHERE playlist_id = (?)
            """
        cur = con.execute(sql, (playlist_id,))
        row = cur.fetchone()
        if row is None:
            return False
        return True
        
    def get_pinned_playlists(self, con):
        """
        retreive entire list of pinned playlists
        returns sqlite3 row object
        """
        sql = """
            SELECT * FROM pinned_playlists
            """
        # retrieve the list
        cur = con.execute(sql)
        rows = cur.fetchall()
        return rows        

    def insert_playlist(self, con, playlist_id):
        """
        insert a new playlist into the pinned_playlists table
        returns row id of the newly pinned playlist
        """
        sql = """
            INSERT INTO pinned_playlists(playlist_id)
            VALUES (?)
            """
        cur = con.execute(sql, (playlist_id,))
        return cur.lastrowid

    def remove_playlist(self, con, playlist_id):
        """remove playlist from pinned_playlists table"""

        sql = """
            DELETE FROM pinned_playlists
            WHERE playlist_id = (?)
            """
        cur = con.execute(sql, (playlist_id,))


class Playlist(_SqliteDB):
    """
    database accessor for table playlist

    init_table(self, con)
        create database table: playlist

    get_title_by_id(self, id_, con)
        search for playlist title by id
    """

    def __init__(self):
        _SqliteDB.__init__(self)
        
    def init_table(self, con):
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
        con.execute(sql)

    def get_rows(self, con, playlist_ids):
        """
        search for playlists by list of ids
        return all rows encapsulated in sqlite row objects
        """
        rows = []
        sql = """
            SELECT * FROM playlist
            WHERE id = (?)            
            """
        for id_ in playlist_ids:
            cur = con.execute(sql, (id_,))
            row = cur.fetchone()
            rows.append(row)
        return rows

    def get_row(self, con, id_):
        """
        search for playlist by id
        return entire row encapsulated in sqlite row object
        """
        sql = """
            SELECT * FROM playlist
            WHERE id = (?)
            """
        cur = con.execute(sql, (id_,))
        row = cur.fetchone()
        return row

    def get_title_by_id(self, id_, con):
        """
        search for playlist title by id
        return title encapsulated in sqlite row
        """
        sql = '''
            SELECT title FROM playlists
            WHERE id = (?) 
            '''
        cur = con.execute(sql, (id_,))
        row = cur.fetchone()
        return row


class PlTrack(_SqliteDB):
    """database accessor for table pl_track"""

    def __init__(self):
        _SqliteDB.__init__(self)

    def init_table(self, con):
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
        con.execute(sql)

class PlTrackMetadata(_SqliteDB):
    """create database table: pl_track_mmetadata"""

    def __init__(self):
        _SqliteDB.__init__(self)

    def init_table(self, con):
        """create database table: pl_track_metadata"""
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
        con.execute(sql)


class Track(_SqliteDB):
    """create database table: pltrack"""

    def __init__(self):
        _SqliteDB.__init__(self)

    def init_table(self, con):
        """create database table: track"""
        sql = """
                CREATE TABLE track (
                    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    path TEXT UNIQUE NOT NULL,
                )
                """
        con.execute(sql)

    def add_row(self, con, path):
        """
        insert row into table track
        returns new track_id
        """
        sql = """
              INSERT INTO track(path)
              VALUES (?)
              """
        cur = con.execute(sql, (path,))
        return cur.lastrowid

    def get_row_by_path(self, con, path):
        """get row from table track that matches path"""
        sql = """
            SELECT id FROM track
            WHERE path = (?)
            """
        cur = con.execute(sql, (path,))
        return cur.fetchone()

    def get_row_by_id(self, con, id_):
        sql = """
            SELECT path FROM track
            WHERE id = (?)
            """
        cur = con.execute(sql, (id_,))
        return cur.fetchone()
