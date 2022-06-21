# -*- coding: utf-8 -*-
#
#  singleton_.py
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
singleton class copied from the python docs
https://www.python.org/download/releases/2.2/descrintro/#__new__
"""


class Singleton():
    """
    To create a singleton class, you subclass from Singleton;
    each subclass will have a single instance,
    no matter how many times its constructor is called.
    To further initialize the subclass instance,
    subclasses should override 'init' instead of __init__.
    The __init__ method is called each time the constructor is called
    """
    def __new__(cls, *args, **kwds):
        singleton = cls.__dict__.get("__it__")
        if singleton is not None:
            return singleton
        cls.__it__ = singleton = object.__new__(cls)
        singleton.init(*args, **kwds)
        return singleton

    def init(self):
        """pass"""
