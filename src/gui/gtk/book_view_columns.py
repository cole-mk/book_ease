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
from book_columns import *

# The playlist metadata column setup
md_title             |= {'g_col':0, 'g_typ':str, 'name':'Title'}

md_author            |= {'g_col':1, 'g_typ':str, 'name':'Author'}

md_read_by           |= {'g_col':2, 'g_typ':str, 'name':'Read by'}

md_length            |= {'g_col':3, 'g_typ':str, 'name':'Length'}

md_track_number      |= {'g_col':4, 'g_typ':str, 'name':'Track'}


# The track column setup
track_file           |= {'g_col':5, 'g_typ':str, 'name':'File'}

track_path           |= {'g_col':7, 'g_typ':str, 'name':'pl_path'}


# The pl_track column setup
pl_track_id          |= {'g_col':6, 'g_typ':int, 'name':'pl_track_id'}


# The IDs for the metadata data columns
md_title_id           = {'g_col':8,  'g_typ':int}

md_author_id          = {'g_col':9,  'g_typ':int}

md_read_by_id         = {'g_col':10, 'g_typ':int}

md_length_id          = {'g_col':11, 'g_typ':int}

md_track_number_id    = {'g_col':12, 'g_typ':int}

metadata_id_col_list  = (md_title_id, md_author_id, md_read_by_id, md_length_id, md_track_number_id)

playlist_row_id       = {'g_col':13, 'g_typ':int}
