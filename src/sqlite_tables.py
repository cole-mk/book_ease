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


# set database file creating config directory
config_dir = Path.home() / '.config' / 'book_ease'
db_dir = config_dir / 'data'
db_dir.mkdir(mode=511, parents=True, exist_ok=True)
db = db_dir / 'book_ease.db'
# module wide db connection for multi queries
module_wide_db_connection = None

def create_connection():
    """ create a sqlite3 connection object and return it"""
    con = None
    con = sqlite3.connect(db, isolation_level=None)
    con.row_factory = sqlite3.Row
    return con


class DBI_:
    """
    Base class for the various DBIs throughout book_ease
    Handles the conection control for single and multi queries
    """
    def __init__(self):
        pass

    def multi_query_begin(self):
        """
        create a semi-persistent connection
        for executing multiple transactions
        """
        if self.con is not None:
            raise RuntimeError('connection already exists')
        else:
            sqlite_tables.module_wide_db_connection = create_connection()

    def multi_query_end(self):
        """commit and close connection of a multi_query"""
        if sqlite_tables.module_wide_db_connection is None:
            raise RuntimeError('connection doesn\'t exist')
        else:
            sqlite_tables.module_wide_db_connection.commit()
            sqlite_tables.module_wide_db_connection.close()
            sqlite_tables.module_wide_db_connection = None

    def _query_begin(self) -> 'sqlite3.Connection':
        """
        get an sqlite connection object
        returns module_wide_db_connection if a multi_query is in effect.
        Otherwise, create and return a new connection
        """
        if sqlite_tables.module_wide_db_connection is None:
            return create_connection()
        else:
            return sqlite_tables.module_wide_db_connection

    def _query_end(self, con):
        """
        commit and close connection if a multi_query
        is not in effect.
        """
        if con is not sqlite_tables.module_wide_db_connection:
            con.commit()
            con.close()


class PinnedPlaylists:
    """database accessor for table pinned_playlists"""
    def __init__(self):
        self.init_table(create_connection())

    def init_table(self, con):
        """create database table: pinned_playlists"""
        sql = """
                CREATE TABLE IF NOT EXISTS pinned_playlists (
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


class Playlist:
    # database accessor for table playlist

    def __init__(self):
        self.init_table(create_connection())

    def init_table(self, con):
        #create database table: playlist
        sql = '''
                CREATE TABLE IF NOT EXISTS playlist (
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

    def get_rows(self, con, playlist_ids) -> 'list of sqlite3.row':
        # search for playlists by list of ids
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

    def get_row(self, con, id_) -> 'sqlite3.row':
        # search for playlist by id
        sql = """
            SELECT * FROM playlist
            WHERE id = (?)
            """
        cur = con.execute(sql, (id_,))
        row = cur.fetchone()
        return row

    def get_rows_by_path(self, con, path) -> 'list of sqlite3.row':
        # search for playlists by path
        rows = []
        sql = """
            SELECT * FROM playlist
            WHERE path = (?)
            """
        cur = con.execute(sql, (path,))
        [rows.append(row) for row in cur.fetchall()]
        return rows

    def get_title_by_id(self, id_, con) -> 'sqlite3.row':
        # search for playlist title by id
        sql = '''
            SELECT title FROM playlists
            WHERE id = (?)
            '''
        cur = con.execute(sql, (id_,))
        row = cur.fetchone()
        return row

    def count_duplicates(self, title, path, playlist_id, con) -> 'sqlite3.row':
        #get a count of the number of playlist titles associated with this path
        #that have the same title, but exclude playlist_id from the list
        if playlist_id == None:
            playlist_id = 'NULL'

        sql = """
            SELECT COUNT(*) FROM playlist
            WHERE title = (?)
            AND path = (?)
            AND id != (?)
            """
        cur = con.execute(sql, (title, path, playlist_id))
        return cur.fetchone()

    def replace(self, con, title, path) -> 'id:int':
        # insert or replace a playlist
        cur.execute("REPLACE INTO playlist(title, path) VALUES (?,?)", (title, path))
        lastrowid = cur.lastrowid
        return lastrowid


class PlTrack:
    """database accessor for table pl_track"""

    def __init__(self):
        self.init_table(create_connection())

    def init_table(self, con):
        """create database table: pl_track"""
        sql = """
            CREATE TABLE IF NOT EXISTS pl_track (
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

    def add(self,con, playlist_id, track_number, track_id) -> 'lastrowid:int':
        # insert track
        sql = """
            INSERT OR IGNORE INTO pl_track(playlist_id, track_number, track_id)
            VALUES (?,?,?)
            """
        cur = con.execute(sql, (playlist_id, track_number, track_id))
        return cur.lastrowid

    def null_duplicate_track_number(con, playlist_id, track_number):
    # look for what will be a duplicate track_num and change it to NULL
        sql = """
            UPDATE pl_track
            SET track_number = (?)
            WHERE playlist_id = (?)
            AND  track_number = (?)
            """
        con.execute(sql, (None, playlist_id, track_number))

    def update_track_number_by_id(con, track_number, id_):
        # update track
        sql = """
            UPDATE pl_track
            SET track_number = (?)
            WHERE id = (?)
            """
        con.execute(sql, (track_number, id_))


class PlTrackMetadata:
    """create database table: pl_track_mmetadata"""

    def __init__(self):
        self.init_table(create_connection())

    def init_table(self, con):
        """create database table: pl_track_metadata"""
        sql = """
            CREATE TABLE IF NOT EXISTS pl_track_metadata (
                id          INTEGER PRIMARY KEY ON CONFLICT ROLLBACK AUTOINCREMENT
                                UNIQUE
                                NOT NULL,
                pl_track_id    INTEGER REFERENCES pl_track (id)
                                NOT NULL,
                entry      TEXT NOT NULL,
                index      INTEGER,
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

    def get_row_by_id(self, con, id_):
        sql = """
            SELECT * FROM pl_track_metadata
            WHERE id = (?)
            """
        cur = con.execute(sql, (id_,))
        return cur.fetchone()

    def null_duplicate_indices(self, con, pl_track_id, index, key):
        # look for what will be a duplicate index and change it to NULL
        sql = """
            UPDATE pl_track_metadata
            SET index = (?)
            WHERE index = (?)
            AND pl_track_id = (?)
            AND  _key = (?)
            """
        con.execute(sql, (None, index, pl_track_id, _key))

    def add_row(self, con, pl_track_id,  entry, index, key):
        # insert pl_track_metadata entry
        sql = """
            INSERT INTO pl_track_metadata(pl_track_id, entry, index, key)
            VALUES (?,?,?,?)
            """
        cur = con.execute(sql, (pl_track_id, entry, index, key))
        return cur.lastrowid

    def update_row(self, con, id_, entry, index, key):
        # update pl_track_metadata entry
        sql = """
            UPDATE pl_track_metadata
            SET pl_track_id  = (?)
            AND entry = (?)
            AND index = (?)
            AND key = (?)
            WHERE id = (?)
            """
        con.execute(sql, (pl_track_id, entry, index, key, id_))

    def get_ids_by_max_index_or_null(self, con, max_index, pl_track_id, key) -> '[sqlite3.row, ... ]':
        # Get the id of any row:key that has and index higher than max_index
        # or Null value for index
        sql = """
            SELECT id FROM pl_track_metadata
            WHERE pl_track_id
            AND key = (?)
            AND index > (?)
            """
        cur = con.execute(sql, (pl_track_id, key, index, key))
        return cur.fetchall()

    def remove_row_by_id(self, con, id_):
        # Delete row with matching id
        sql = """
            DELETE FROM pl_track_metadata
            WHERE id = (?)
            """
        con.execute(sql(id_))



class TrackFile:
    """create database table: pltrack"""

    def __init__(self):
        self.init_table(create_connection())

    def init_table(self, con):
        """create database table: track_file"""
        sql = """
            CREATE TABLE IF NOT EXISTS track_file (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                path TEXT UNIQUE NOT NULL
            )
            """
        con.execute(sql)

    def add_row(self, con, path):
        """
        insert row into table track_file
        returns new track_id or 0 if already exists
        """
        sql = """
              INSERT or IGNORE INTO track_file(path)
              VALUES (?)
              """
        cur = con.execute(sql, (path,))
        return cur.lastrowid

    def get_id_by_path(self, con, path):
        """get row from table track_file that matches path"""
        sql = """
            SELECT id FROM track_file
            WHERE path = (?)
            """
        cur = con.execute(sql, (path,))
        return cur.fetchone()

    def get_row_by_id(self, con, id_):
        sql = """
            SELECT path FROM track_file
            WHERE id = (?)
            """
        cur = con.execute(sql, (id_,))
        return cur.fetchone()
