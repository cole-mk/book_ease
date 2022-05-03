"""Database accessing root class"""
# -*- coding: utf-8 -*-
#
#  db.py
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


class _DB:
    """Database accessing root class"""

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

        # playlists saved in cur dir
        self.cur_pl_list = []
        # helpers for accessing data stored in self.cur_pl_list
        self.cur_pl_id = {'col':0, 'col_name':'id'}
        self.cur_pl_title  = {'col':1, 'col_name':'title'}
        self.cur_pl_path  = {'col':2, 'col_name':'path'}
        self.cur_pl_helper_l = [self.cur_pl_id, self.cur_pl_title, self.cur_pl_path]
        self.cur_pl_helper_l.sort(key=lambda col: col['col'])

        self.init_tables()

    def get_cur_pl_list(self):
        """return self.cur_pl_list"""
        return self.cur_pl_list

    def init_tables(self):
        """
        routine to initialize database tables
        This is an informal interface implemented
        as a pass function in this parent class
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

    def set_cur_pl_list_by_path(self, path, con=None):
        """
        populate self.cur_pl_list with the current playlist data
        associated with the path passed as a parameter
        """
        pl_list = None
        if con is None:
            con = self.create_connection()
        try:
            sql = '''
                SELECT * FROM playlist
                WHERE path = ?
                '''
            cur = con.execute(sql, (path,))
            pl_list = cur.fetchall()

            # fill cur_pl_list with pl_list
            self.cur_pl_list.clear()
            for i, row in enumerate(pl_list):
                self.cur_pl_list.append(row)

        except sqlite3.Error as e:
            print("couldn't set_cur_pl_list_by_path", e)

