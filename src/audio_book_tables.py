# -*- coding: utf-8 -*-
#
#  audio_book_tables.py
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
This module is responsible for managing the connection to the sqlite tables database.
This database holds the data for book_ease's non-gui settings and all of the playlists.
This module has a create_connection function to aid other classes in connection management.
The classes in this module serve as an interface for a single table in the database.
"""

from pathlib import Path
import sqlite3

# disable=too-many-arguments because the data is unpacked in another class
# pylint: disable=too-many-arguments

# set database file creating config directory
config_dir = Path.home() / '.config' / 'book_ease'
db_dir = config_dir / 'data'
db_dir.mkdir(mode=511, parents=True, exist_ok=True)
db = db_dir / 'audio_books.db'

def create_connection():
    """ create a sqlite3 connection object and return it"""
    con = None
    con = sqlite3.connect(db, isolation_level=None)
    con.row_factory = sqlite3.Row
    return con


class PinnedPlaylists:
    """database accessor for table pinned_playlists"""

    @staticmethod
    def init_table(con):
        """create database table: pinned_playlists"""
        sql = """
                CREATE TABLE IF NOT EXISTS pinned_playlists (
                    id INTEGER PRIMARY KEY ON CONFLICT ROLLBACK AUTOINCREMENT NOT NULL,
                    playlist_id  INTEGER REFERENCES playlist (id)  ON DELETE CASCADE
                                         UNIQUE ON CONFLICT ROLLBACK NOT NULL
                )
                """
        con.execute(sql)

    @staticmethod
    def has_playlist(con, playlist_id):
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

    @staticmethod
    def get_pinned_playlists(con):
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

    @staticmethod
    def insert_playlist(con, playlist_id):
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

    @staticmethod
    def remove_playlist(con, playlist_id):
        """remove playlist from pinned_playlists table"""

        sql = """
            DELETE FROM pinned_playlists
            WHERE playlist_id = (?)
            """
        con.execute(sql, (playlist_id,))


class Playlist:
    """ database accessor for table playlist"""

    def __init__(self):
        self.init_table(create_connection())

    def init_table(self, con):
        """create database table: playlist"""
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
        """search for playlists by list of ids"""
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
        """search for playlist by id"""
        sql = """
            SELECT * FROM playlist
            WHERE id = (?)
            """
        cur = con.execute(sql, (id_,))
        row = cur.fetchone()
        return row

    def get_rows_by_path(self, con, path) -> 'list of sqlite3.row':
        """search for playlists by path"""
        rows = []
        sql = """
            SELECT * FROM playlist
            WHERE path = (?)
            """
        cur = con.execute(sql, (path,))
        for row in cur.fetchall():
            rows.append(row)
        return rows

    def get_title_by_id(self, id_, con) -> 'sqlite3.row':
        """search for playlist title by id"""
        sql = '''
            SELECT title FROM playlists
            WHERE id = (?)
            '''
        cur = con.execute(sql, (id_,))
        row = cur.fetchone()
        return row

    def count_duplicates(self, title, path, playlist_id, con) -> 'sqlite3.row':
        """
        Get a count of the number of playlist titles associated with this path that have the same title, but exclude
        playlist_id from the list.
        """
        if playlist_id is None:
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
        """insert or replace a playlist"""
        cur = con.execute("REPLACE INTO playlist(title, path) VALUES (?,?)", (title, path))
        lastrowid = cur.lastrowid
        return lastrowid

    def insert(self, con, title, path) -> 'lastrowid:int':
        """insert a playlist"""
        sql = """
            INSERT INTO playlist(title, path)
            VALUES (?,?)
            """
        cur = con.execute(sql,(title, path))
        return cur.lastrowid

    def update(self, con, title, path, id_):
        """update the title and path columns of playlist row thats matched to the id number"""
        sql = """
            UPDATE playlist
            SET title = ?,
                path = ?
            WHERE id = ?
            """
        con.execute(sql, (title, path, id_))



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

    def add(self, con, playlist_id, track_number, track_id) -> 'lastrowid:int':
        """insert track"""
        sql = """
            INSERT INTO pl_track(playlist_id, track_number, track_id)
            VALUES (?,?,?)
            """
        cur = con.execute(sql, (playlist_id, track_number, track_id))
        return cur.lastrowid

    def null_duplicate_track_number(self, con, playlist_id, track_number):
        """look for what will be a duplicate track_num and change it to NULL"""
        sql = """
            UPDATE pl_track
            SET track_number = (?)
            WHERE playlist_id = (?)
            AND  track_number = (?)
            """
        con.execute(sql, (None, playlist_id, track_number))

    def update_track_number_by_id(self, con, track_number, id_):
        """update column track_number in pl_track by matching id"""
        sql = """
            UPDATE pl_track
            SET track_number = (?)
            WHERE id = (?)
            """
        con.execute(sql, (track_number, id_))

    def get_ids_by_max_index_or_null(self, con, max_track_number, playlist_id) -> '[sqlite3.row[int], ... ]':
        """get list of ids that are greater than max_index or set to NULL"""
        sql = """
            SELECT id FROM pl_track
            WHERE playlist_id = (?)
            AND (track_number > (?) OR track_number is NULL)
            """
        cur = con.execute(sql, (playlist_id, max_track_number))
        return cur.fetchall()

    def remove_row_by_id(self, con, id_):
        """remove row from table pl_track that matches id"""
        sql = """
            DELETE FROM pl_track
            WHERE id = (?)
            """
        con.execute(sql, (id_,))

    def get_rows_by_playlist_id(self, con, playlist_id):
        """get all rows that match playlist_id"""
        sql = """
            SELECT * FROM pl_track
            where playlist_id = (?)
            """
        cur = con.execute(sql, (playlist_id,))
        return cur.fetchall()

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
                idx      INTEGER,
                _key      TEXT NOT NULL,
                UNIQUE (
                    pl_track_id,
                    idx,
                    _key
                )
                ON CONFLICT ROLLBACK
            )
            """
        con.execute(sql)

    def get_row_by_id(self, con, id_):
        """get the entire row from pl_track_metadata for row matches id"""
        sql = """
            SELECT * FROM pl_track_metadata
            WHERE id = (?)
            """
        cur = con.execute(sql, (id_,))
        return cur.fetchone()

    def get_rows(self, con, key, pl_track_id):
        """get all rows from pl_track_metadata that match key and pl_track_id"""
        sql = """
            SELECT * FROM pl_track_metadata
            WHERE _key = (?)
            AND pl_track_id = (?)
            """
        cur = con.execute(sql, (key, pl_track_id))
        return cur.fetchall()


    def null_duplicate_indices(self, con, pl_track_id, index, key):
        """look for what will be a duplicate index and change it to NULL"""
        sql = """
            UPDATE pl_track_metadata
            SET idx = NULL
            WHERE idx = (?)
            AND pl_track_id = (?)
            AND  _key = (?)
            """
        con.execute(sql, (index, pl_track_id, key))

    def add_row(self, con, pl_track_id,  entry, index, key):
        """insert pl_track_metadata entry"""
        sql = """
            INSERT INTO pl_track_metadata(pl_track_id, entry, idx, _key)
            VALUES (?,?,?,?)
            """
        cur = con.execute(sql, (pl_track_id, entry, index, key))
        return cur.lastrowid

    def update_row(self, con, pl_track_id, id_, entry, index, key):
        """update pl_track_metadata entry"""
        sql = """
            UPDATE pl_track_metadata
            SET pl_track_id  = (?),
            entry = (?),
            idx = (?),
            _key = (?)
            WHERE id = (?)
            """
        con.execute(sql, (pl_track_id, entry, index, key, id_))

    def get_ids_by_max_index_or_null(self, con, max_index, pl_track_id, key) -> '[sqlite3.row[int], ... ]':
        """
        Get the id of any row:key that has and index higher than max_index
        or Null value for index
        """
        sql = """
            SELECT id FROM pl_track_metadata
            WHERE pl_track_id = (?)
            AND _key = (?)
            AND (idx > (?) OR idx is NULL)
            """
        cur = con.execute(sql, (pl_track_id, key, max_index))
        return cur.fetchall()

    def remove_row_by_id(self, con, id_):
        """Delete row with matching id"""
        sql = """
            DELETE FROM pl_track_metadata
            WHERE id = (?)
            """
        con.execute(sql, (id_,))


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
        """Get entire row from track_file that matches id_"""
        sql = """
            SELECT * FROM track_file
            WHERE id = (?)
            """
        cur = con.execute(sql, (id_,))
        return cur.fetchone()
