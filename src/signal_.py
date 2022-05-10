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
helper class to implement signal system (notifications)
note: instantiated/inherited by server
"""

class Signal_():

    def __init__(self):
        """
        create empty signal handler container, dict
        note: instantiated/inherited by server

        for each key/val pair,
        the key will be the signal handle
        and the val will hold a list of containers that hold
        the data for a signal call. the container is defined in connect()
        """
        self._sig_handlers = {}

    def add_signal(self, handle):
        """
        create/add signal to the sig handlers list
        note: called by server
        """
        self._sig_handlers[handle] = []

    def remove_signal(self, handle):
        """
        remove signal from the sig handlers list
        note: called by server
        """
        del self._sig_handlers[handle]

    def connect(self, handle, method, *cb_args, **cb_kwargs):
        """
        connect callback to signal in the sig handlers list
        note: called by subscriber
        note: server must have added the signal before subscriber can connect

        handle: signal name
        method: subscriber chosen method to call during signal execution
        cb_args: user data to be passed to the callback function during signal execution
        cb_kwargs: user data to be passed to the callback function during signal execution
        """
        self._sig_handlers[handle].append((method, cb_args, cb_kwargs))

    def signal(self, handle, *extra_args, **extra_kwargs):
        """
        execute each signal for this handle in the sig handlers list
        note: called by server

        handle: signal name
        extra_args: allow server to add args to the signal call
        extra_kwargs: allow server to add kwargs to the signal call
        signal[0]: callback method
        signal[1]: cb_args
        signal[2]: cb_kwargs
        """
        [signal[0](*signal[1], *extra_args, **signal[2], **extra_kwargs) for signal in self._sig_handlers[handle]]
