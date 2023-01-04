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
from dataclasses import dataclass
from typing import Callable


@dataclass(eq=False, frozen=True)
class SignalData:
    """
    Store information about a callback and the parameters to be passed to it.
    """
    callback: Callable
    cb_args: list
    cb_kwargs: dict


class Signal():
    """
    helper class to implement signal system (notifications)
    note: instantiated/inherited by server
    """

    def __init__(self):
        """
        create empty signal handler container, dict
        note: instantiated/inherited by server

        _sig_handlers, _sig_handlers_once:
        For each key/val pair,
        the key will be the signal handle
        and the val will hold a list of SignalData objects that hold
        the data for a signal call. The container is populated in connect().

        _muted_signals:
        This list contains signal handles that are to be ignored when sending a signal.
        """
        self._sig_handlers = {}
        self._sig_handlers_once = {}

    def add_signal(self, handle: str, *more_handles: str):
        """
        create/add signal to the sig handlers list
        note: called by server
        """
        for sig_h in (self._sig_handlers, self._sig_handlers_once):
            sig_h[handle] = []
            for additional_handle in more_handles:
                sig_h[additional_handle] = []

    def remove_signal(self, handle):
        """
        remove signal from the sig handlers list
        note: called by server
        """
        for sig_h in (self._sig_handlers, self._sig_handlers_once):
            del sig_h[handle]

    def connect(self, handle, method, *cb_args, pass_sig_data_to_cb: bool = False, **cb_kwargs) -> SignalData:
        """
        connect callback to signal in the sig handlers list
        note: called by subscriber
        note: server must have added the signal before subscriber can connect

        handle: signal name
        method: subscriber chosen method to call during signal execution
        cb_args: user data to be passed to the callback function during signal execution
        cb_kwargs: user data to be passed to the callback function during signal execution

        Returns the SignalData object that is added to the list.
        """
        sig_data = SignalData(method, cb_args, cb_kwargs)
        if pass_sig_data_to_cb:
            sig_data.cb_kwargs['sig_data'] = sig_data
        self._sig_handlers[handle].append(sig_data)
        return sig_data

    def connect_once(self, handle, method, *cb_args, pass_sig_data_to_cb: bool = False, **cb_kwargs) -> SignalData:
        """
        Connect callback to signal in the sig handlers list
        This connection will be transmitted once and then removed from the list.

        note: called by subscriber
        note: server must have added the signal before subscriber can connect

        handle: signal name
        method: subscriber chosen method to call during signal execution
        cb_args: user data to be passed to the callback function during signal execution
        cb_kwargs: user data to be passed to the callback function during signal execution

        Returns the SignalData object that is added to the list.
        """
        sig_data = SignalData(method, cb_args, cb_kwargs)
        if pass_sig_data_to_cb:
            sig_data.cb_kwargs['sig_data'] = sig_data
        self._sig_handlers_once[handle].append(sig_data)
        return sig_data

    def send(self, handle, *extra_args, **extra_kwargs):
        """
        execute each signal for this handle in the sig handlers list
        note: called by server

        handle: signal name
        extra_args: allow server to add args to the signal call
        extra_kwargs: allow server to add kwargs to the signal call
        """
        for sig_h in (self._sig_handlers, self._sig_handlers_once):
            # reversed so a calback can remove itself wihout disrupting the iteration.
            for signal in reversed(sig_h[handle]):
                signal.callback(*signal.cb_args, *extra_args, **signal.cb_kwargs, **extra_kwargs)
        self._sig_handlers_once[handle] = []

    def disconnect_by_call_back(self, handle: str, call_back: Callable):
        """
        remove a callback from the signal handler's list by matching handle and callback method.
        This will remove the first matching entry matching handle and callback method to a signal.

        Callbacks can not guarantee that they remove themselves from sig handler's list by
        calling disconnect_by_call_back. Callbacks should use disconnect_by_signal_data() instead,
        or preferably use connect_once() whenever possible.
        """
        for sig_h in (self._sig_handlers, self._sig_handlers_once):
            for sig in sig_h[handle]:
                if call_back == sig[0]:
                    sig_h[handle].remove(sig)
                    return
        raise ValueError(f'call_back: {call_back} not found for signal: {handle}.')

    def disconnect_by_signal_data(self, sig_data: SignalData, handle: str = None) -> bool:
        """
        Remove callback by finding the matching signal data-- match by identity.

        It is safe for callbacks to use this method to disconnect themselves from the signal,
        but it is recommended to use connect_once() whenever possible.

        Searches for sig_data in the signal specified by handle. If handle is not specified,
        then disconnect_by_signal_data searches for the sig_data in all rgistered signals.
        """
        handles = list(handle) if handle is not None else list(self._sig_handlers)

        for _handle in handles:
            for sig_h in (self._sig_handlers, self._sig_handlers_once):
                if sig_data in sig_h[_handle]:
                    sig_h[_handle].remove(sig_data)
                    return
        raise ValueError(f'sig_data: {sig_data} not found.')
