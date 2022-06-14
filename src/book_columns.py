# -*- coding: utf-8 -*-
#
#  book_columns.py
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


# The playlist metadata column setup
md_title            = {'key':'title',       'alt_keys':['album']}

md_author           = {'key':'author',      'alt_keys':['artist', 'performer', 'composer']}

md_read_by          = {'key':'performer',   'alt_keys':['author', 'artist', 'composer']}

md_length           = {'key':'length',      'alt_keys':[None]}

md_track_number     = {'key':'tracknumber', 'alt_keys':[None]}

metadata_col_list   = (md_title,  md_author, md_read_by, md_length, md_track_number)


# The track column setup
track_file          = {'key':'file',        'alt_keys':[None]}

track_path          = {'key':None,          'alt_keys':[None]}

track_col_list      = (track_file, track_path)


# The pl_track column setup
pl_track_id         = {'key':'pl_track_id', 'alt_keys':[None]}

pl_track_col_list   = (pl_track_id,)
