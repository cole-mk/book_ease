# -*- coding: utf-8 -*-
#
#  vi_interface.py
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
"""module wide gtk.builder instance"""

from pathlib import Path
from gi.repository import Gtk

__book_builder = None # pylint: disable=invalid-name


def get_builder() ->'Gtk.builder':
    """instantiate and return module wide gtk.builder instance"""

    glade_path = Path().cwd() / 'gui' / 'gtk' / 'book.glade'
    global __book_builder# pylint: disable=global-statement disable=invalid-name

    if __book_builder is None:
        __book_builder = Gtk.Builder()
        __book_builder.add_from_file(str(glade_path))
    return __book_builder
