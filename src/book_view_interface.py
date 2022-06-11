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
import abc
from gi.repository import Gtk, Gdk, GLib
from pathlib import Path


"""module wide gtk.builder instance"""
__book_builder = None


def get_builder() ->'Gtk.builder':
    """instantiate and return module wide gtk.builder instance"""
    glade_path = Path().cwd() / 'gui' / 'gtk' / 'book.glade'
    global __book_builder
    if __book_builder is None:
        __book_builder = Gtk.Builder()
        __book_builder.add_from_file(str(glade_path))
    return __book_builder

api_ = {'update':lambda x:x.update,
        'get_view':lambda x:x.get_view,
        'close':lambda x:x.close,
        'begin_edit_mode':lambda x:x.begin_edit_mode,
        'begin_display_mode':lambda x:x.begin_display_mode}


class BookView_Interface(metaclass=abc.ABCMeta):

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'update') and
                callable(subclass.update) and
                hasattr(subclass, 'get_view') and
                callable(subclass.get_view) and
                hasattr(subclass, 'begin_edit_mode') and
                callable(subclass.begin_edit_mode) and
                hasattr(subclass, 'close') and
                callable(subclass.close) and
                hasattr(subclass, 'begin_display_mode') and
                callable(subclass.begin_display_mode) or
                NotImplemented)

    @abc.abstractmethod
    def update(self):
        """Update the data set"""
        raise NotImplementedError

    @abc.abstractmethod
    def begin_edit_mode():
        """switch to editing mode"""
        raise NotImplementedError

    @abc.abstractmethod
    def begin_display_mode():
        """switch to display mode"""
        raise NotImplementedError

    @abc.abstractmethod
    def close():
        """cleanup and close the gui"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_view():
        """retrieve the view from the VI classes"""
        raise NotImplementedError
