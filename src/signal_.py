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
helper module to implement signal system (notifications)
note: instantiated/inherited by server
"""
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable


class Signal():
    """
    helper class to implement signal system (notifications)
    note: instantiated/inherited by server
    """

    def __init__(self):
        """
        create empty signal handler container, dict
        note: instantiated/inherited by server

        _sig_handlers:
        for each key/val pair,
        the key will be the signal handle
        and the val will hold a list of containers that hold
        the data for a signal call. the container is defined in connect()

        _muted_signals:
        This list contains signal handles that are to be ignored when sending a signal.
        """
        self._sig_handlers = {}
        self._muted_signals = []

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

    def send(self, handle, *extra_args, **extra_kwargs):
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
        if not handle in self._muted_signals:
            for signal in self._sig_handlers[handle]:
                signal[0](*signal[1], *extra_args, **signal[2], **extra_kwargs)

    def mute_signal(self, handle):
        """add a signal handle to the list of signals to be ignored while sending"""
        if not handle in self._muted_signals:
            self._muted_signals.append(handle)

    def unmute_signal(self, handle):
        """remove a signal handle from the list of signals to be ignored while sending"""
        self._muted_signals.remove(handle)

    def disconnect_by_call_back(self, handle: str, call_back: Callable):
        """
        remove a callback from the signal handler's list by matching handle and callback method.
        This will remove all matching entries where the same callback method was connected more than once by the same
        object instance.
        """
        index = len(self._sig_handlers[handle]) -1
        for sig in reversed(self._sig_handlers[handle]):
            if call_back == sig[0]:
                self._sig_handlers[handle].pop(index)
            index -= 1
