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

This module provides logging output. It is set to output to the NullHandler.
To access the output, place the following in the main application file:
import logging
logging.getLogger('signal_').addHandler(logging.StreamHandler())
"""
import weakref
import logging
from typing import Callable


class SignalData:
    """
    Store information about a callback and the parameters to be passed to it.
    """
    logger = logging.getLogger(f'{__name__}.SignalData')
    logger.addHandler(logging.NullHandler())

    def __init__(self,
                 callback: Callable,
                 subscriber_died_cb: Callable,
                 *cb_args: tuple,
                 **cb_kwargs: dict) -> None:

        self._subscriber_died_cb = subscriber_died_cb
        self.callback = weakref.WeakMethod(callback, self._cleanup)
        self.cb_args = cb_args
        self.cb_kwargs = cb_kwargs

    def _cleanup(self, _) -> None:
        """
        Wrapper for the weakref callback. Replace the passed in reference to self.callback
        with a reference to self.
        """
        self._subscriber_died_cb(self)


class Signal():
    """
    helper class to implement signal system (notifications)
    note: instantiated/inherited by server
    """

    def __init__(self) -> None:
        """
        create empty signal handler container, dict
        note: instantiated/inherited by server

        _sig_handlers, _sig_handlers_once:
        For each key/val pair,
        the key will be the signal handle
        and the val will hold a list of SignalData objects that hold
        the data for a signal call. The containers are populated in connect().
        """
        self._sig_handlers = {}
        self._sig_handlers_once = {}

    def add_signal(self, handle: str, *more_handles: tuple[str]) -> None:
        """
        create/add signal to the sig handlers list
        note: called by server
        """
        for sig_h in (self._sig_handlers, self._sig_handlers_once):
            sig_h[handle] = []
            for additional_handle in more_handles:
                sig_h[additional_handle] = []

    def remove_signal(self, handle: str) -> None:
        """
        remove signal from the sig handlers list
        note: called by server
        """
        for sig_h in (self._sig_handlers, self._sig_handlers_once):
            del sig_h[handle]

    def _connect(self,
                 handle: str,
                 sig_handler_dict: dict,
                 cb_method: Callable,
                 *cb_args: tuple,
                 pass_sig_data_to_cb: bool = False,
                 **cb_kwargs: dict) -> SignalData:
        """
        connect callback to signal in the sig handlers list
        note: called by self.connect or self.connect_once
        note: server must have added the signal before subscriber can connect

        handle: signal name
        sig_handler_dict: i.e. self._sig_handlers or self._sig_handlers_once
        method: subscriber chosen method to call during signal execution
        cb_args: user data to be passed to the callback function during signal execution
        cb_kwargs: user data to be passed to the callback function during signal execution

        Returns a weakref.proxy->SignalData object that is added to the list.
        """
        sig_data = SignalData(cb_method, self.disconnect_by_signal_data, *cb_args, **cb_kwargs)

        sig_handler_dict[handle].append(sig_data)
        sig_data_proxy = weakref.proxy(sig_data)

        if pass_sig_data_to_cb:
            sig_data.cb_kwargs['sig_data'] = sig_data_proxy

        return sig_data_proxy

    def connect(self,
                handle: str,
                method: Callable,
                *cb_args: tuple,
                pass_sig_data_to_cb: bool = False,
                **cb_kwargs: dict) -> SignalData:
        """
        connect callback to signal in the sig handlers list
        note: called by subscriber
        note: server must have added the signal before subscriber can connect

        handle: signal name
        method: subscriber chosen method to call during signal execution
        cb_args: user data to be passed to the callback function during signal execution
        cb_kwargs: user data to be passed to the callback function during signal execution

        Returns a weakref.proxy->SignalData object that is added to the list.
        """
        return self._connect(handle,
                             self._sig_handlers,
                             method,
                             *cb_args,
                             pass_sig_data_to_cb=pass_sig_data_to_cb,
                             **cb_kwargs)

    def connect_once(self,
                     handle: str,
                     method: Callable,
                     *cb_args: tuple,
                     pass_sig_data_to_cb: bool = False,
                     **cb_kwargs: dict) -> SignalData:
        """
        Connect callback to signal in the sig handlers list
        This connection will be transmitted once and then removed from the list.

        note: called by subscriber
        note: server must have added the signal before subscriber can connect

        handle: signal name
        method: subscriber chosen method to call during signal execution
        cb_args: user data to be passed to the callback function during signal execution
        cb_kwargs: user data to be passed to the callback function during signal execution

        Returns a weakref.proxy->SignalData object that is added to the list.
        """
        return self._connect(handle,
                             self._sig_handlers_once,
                             method,
                             *cb_args,
                             pass_sig_data_to_cb=pass_sig_data_to_cb,
                             **cb_kwargs)

    def send(self, handle: str, *extra_args: tuple, **extra_kwargs: dict) -> None:
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
                signal.callback()(*signal.cb_args, *extra_args, **signal.cb_kwargs, **extra_kwargs)
        self._sig_handlers_once[handle] = []

    def disconnect_by_call_back(self, handle: str, call_back: Callable) -> None:
        """
        remove a callback from the signal handler's list by matching handle and callback method.
        This will remove the first matching entry matching handle and callback method to a signal.

        Callbacks can not guarantee that they remove themselves from sig handler's list by
        calling disconnect_by_call_back. Callbacks should use disconnect_by_signal_data() instead,
        or preferably use connect_once() whenever possible.
        """
        for sig_h in (self._sig_handlers, self._sig_handlers_once):
            for sig in sig_h[handle]:
                if call_back == sig.callback():
                    sig_h[handle].remove(sig)
                    return
        raise ValueError(f'call_back: {call_back} not found for signal: {handle}.')

    def disconnect_by_signal_data(self, sig_data: SignalData, handle: str=None) -> None:
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
                try:
                    sig_h[_handle].remove(sig_data)
                    return
                except ValueError:
                    # Only raise the exception once it is proven that sig_data isn't to be found.
                    pass
        raise ValueError(f'sig_data: {sig_data} not found.')
