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
import book_columns

# The playlist metadata column setup
md_title        = book_columns.md_title
md_title        = {'name':'Title',          'col':0, 'g_typ':str}

md_author       = book_columns.md_author
md_author       = {'name':'Author',         'col':1, 'g_typ':str}

md_read_by      = book_columns.md_read_by
md_read_by      = {'name':'Read by',        'col':2, 'g_typ':str}

md_length       = book_columns.md_length
md_length       = {'name':'Length',         'col':3, 'g_typ':str}

md_track_number = book_columns.md_track_number
md_track_number = {'name':'Track',          'col':4, 'g_typ':str}

# The track column setup
track_file      = book_columns.track_file
track_file      = {'name':'File',           'col':5, 'g_typ':str}

track_path      = book_columns.track_path
track_path      = {'name':'pl_path',        'col':7, 'g_typ':str}

# The pl_track column setup
pl_track_id     = book_columns.pl_track_id
pl_track_id     = {'name':'pl_track_id',    'col':6, 'g_typ':int}

# The IDs for the metadata data columns
md_title_id        = {'col':8,  'g_typ':int}

md_author_id       = {'col':9,  'g_typ':int}

md_read_by_id      = {'col':10, 'g_typ':int}

md_length_id       = {'col':11, 'g_typ':int}

md_track_number_id = {'col':12, 'g_typ':int}

