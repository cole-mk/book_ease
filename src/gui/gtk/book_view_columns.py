# -*- coding: utf-8 -*-
#
#  book_view_columns.py
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
#pylint: disable=unused-wildcard-import
#pylint: disable=wildcard-import
"""
This modules exposes everything from book_columns module.

It appends Gtk and view specific data to the columns defined there.

It creates new columns that are only used in the view classes.
    the metadata id columns
    playlist_row_id

It creates lists of these columns that are only of interest to the view classes
    metadata_id_col_list
    display_cols
"""
from book_columns import *

# TrackMDEntry.id columns; The IDs for the metadata data columns
md_title_id          = {'g_col':8,  'g_typ':int, 'name':'md_title_id'}

md_author_id         = {'g_col':9,  'g_typ':int, 'name':'md_author_id'}

md_read_by_id        = {'g_col':10, 'g_typ':int, 'name':'md_read_by_id'}

md_length_id         = {'g_col':11, 'g_typ':int, 'name':'md_length_id'}

md_track_number_id   = {'g_col':12, 'g_typ':int, 'name':'md_track_number_id'}

metadata_id_col_list = (md_title_id, md_author_id, md_read_by_id, md_length_id, md_track_number_id)


# TrackMDEntry.entry columns; The playlist metadata column setup.
md_title            |= {'g_col':0,  'g_typ':str, 'name':'Title',   'id_column':md_title_id}

md_author           |= {'g_col':1,  'g_typ':str, 'name':'Author',  'id_column':md_author_id}

md_read_by          |= {'g_col':2,  'g_typ':str, 'name':'Read by', 'id_column':md_read_by_id}

md_length           |= {'g_col':3,  'g_typ':str, 'name':'Length',  'id_column':md_length_id}

md_track_number     |= {'g_col':4,  'g_typ':str, 'name':'Track',   'id_column':md_track_number_id}


# The track column setup
track_file          |= {'g_col':5,  'g_typ':str, 'name':'File'}

track_path          |= {'g_col':7,  'g_typ':str, 'name':'Path'}

track_num           |= {'g_col':14,  'g_typ':int, 'name':'track_num'}


# The pl_track column setup
pl_track_id         |= {'g_col':6,  'g_typ':int, 'name':'pl_track_id'}


# The playlist_row_id is a unique row id that is only used by
# The V and VC classes. It never touches Book or Book_C.
playlist_row_id      = {'g_col':13, 'g_typ':int, 'name':'playlist_row_id'}

# The columns that will be displayed in the playlist treeview column
display_cols = [md_track_number, md_title, md_author, md_read_by, md_length, track_file]
