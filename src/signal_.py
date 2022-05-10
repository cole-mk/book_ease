# -*- coding: utf-8 -*-
#
#  signal_.py
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
helper class for model classes (MVC) to implement signal system (notifications)
"""

class Signal_():

    def __init__(self):
        # each entry will hold a list of tuples as defined in connect()
        self._sig_handlers = {}

    def add_signal(self, handle):
        # add signal to the sig handlers list
        # called by server
        self._sig_handlers[handle] = []

    def remove_signal(self, handle):
        # remove signal from the sig handlers list
        # called by server
       del self._sig_handlers[handle]

    def connect(self, handle, method, *args, **cb_kwargs):
        # connect callback to signal in the sig handlers list
        # called by client
        self._sig_handlers[handle].append((handle, method, args, cb_kwargs))

    def signal(self, handle, *ext_args, **ext_kwargs):
        # execute each signal in the sig handlers list
        # called by server
        [signal[1](*signal[2], *ext_args, **signal[3], **ext_kwargs) for signal in self._sig_handlers[handle]]
