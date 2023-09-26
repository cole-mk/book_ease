# -*- coding: utf-8 -*-
#
#  test_signal.py
#
#  This file is part of book_ease.
#
#  Copyright 2022 mark cole <mark@capstonedistribution.com>
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
#
# pylint: disable=invalid-name
# disabled because in the IDE project structure sidebar, I want the test classes sorted in the same order
# as the methods they are testing.
#
# pylint: disable=protected-access
# disabled because this module is testing protected methods.
#
# pylint: disable=too-few-public-methods
# disabled because some of the tested methods only require one test.
#
# pylint: disable=comparison-with-callable
# disabled because this needs to be done regularly during tests.
#

"""
Unit test for class signal_.Signal
"""

from unittest import mock
import pytest
import weakref
import gc
from signal_ import Signal


class TestSignal:
    """
    Unit test for class signal_.Signal
    """
    call_count = 0
    sig_data_passed_to_cb_list = []
    args_list = []

    def callback(self, *args, **kwargs):
        """test callback"""
        self.call_count += 1
        for arg in args:
            self.args_list.append(arg)
        if 'sig_data' in kwargs:
            self.sig_data_passed_to_cb_list.append(kwargs['sig_data'])

        # for test_connect_once_callbacks_can_reconnect_themselves
        if {'reconnect_once', 'tx_object'}.issubset(kwargs):
            kwargs['tx_object'].connect_once('handle', self.callback)
            kwargs['tx_object'].send('handle')

    def test_connect_once_callbacks_can_reconnect_themselves(self):
        """
        Ensure that a callback that was registered with connect_once can re-add itself
        to the connect_once signal list. There previously was a bug where the callback would
        call connect_once to reconnect to the signal, but Signal.send() would delete the entire
        connect_once list when Signal.send() finished processing the rest of the event queue.
        """
        self.call_count = 0
        tx = Signal()
        tx.add_signal('handle')
        tx.connect_once('handle', self.callback, reconnect_once=True, tx_object=tx)
        tx.send('handle')
        assert self.call_count == 2

    def test_sends_connected_signals_multiple_times(self):
        """
        Assert that send() can transmit a signal repeatedly if it has been connected via connect().
        """
        self.call_count = 0
        tx = Signal()
        tx.add_signal('handle')
        tx.connect('handle', self.callback)

        for _ in range(3):
            tx.send('handle')

        assert self.call_count == 3

    def test_connect_raises_key_error_if_signal_not_added(self):
        """
        Assert that connect() and connect_once() raises a KeyError if the 'handle' parameter has not previously
        been added to the list of registered signals.
        """
        tx = Signal()
        #callback = mock.Mock()

        with pytest.raises(KeyError):
            tx.connect('handle', self.callback)

        with pytest.raises(KeyError):
            tx.connect_once('handle', self.callback)

    def test_remove_causes_connect_to_raise_key_error(self):
        """
        Show that remove_signal() actually removes the signal by:
        Assert that calling connect() after removing the signal raises a KeyError.
        """
        tx = Signal()

        tx.add_signal('handle')
        tx.connect('handle', self.callback)
        tx.remove_signal('handle')

        with pytest.raises(KeyError):
            tx.connect('handle', self.callback)

    def test_sends_connect_once_transmitts_a_single_time_only(self):
        """
        Show that when a signal is connected using connect_once(),
        the signal is sent only on the next call to send().
        """
        tx = Signal()
        self.call_count = 0
        tx.add_signal('handle')
        tx.connect_once('handle', self.callback)
        tx.send('handle')
        tx.send('handle')

        assert self.call_count == 1

    def test_disconnect_by_signal_data_removes_signal_from_call_list(self):
        """
        Show that disconnect_by_signal_data() removes the correct signal from the
        call lists. It cannot be fooled by identical signals connected multiple times.
        """

        tx = Signal()
        self.sig_data_passed_to_cb_list = []

        tx.add_signal('handle')
        sig_data = [tx.connect('handle', self.callback, pass_sig_data_to_cb=True) for _ in range(3)]
        tx.disconnect_by_signal_data(sig_data[1])
        tx.send('handle')

        assert sig_data[0] in self.sig_data_passed_to_cb_list
        assert sig_data[1] not in self.sig_data_passed_to_cb_list
        assert sig_data[2] in self.sig_data_passed_to_cb_list

    def test_disconnect_by_callback_removes_signal_from_call_list(self):
        """
        Show that disconnect_by_signal_data() removes the correct signal from the
        call lists. It cannot be fooled by identical signals connected multiple times.
        """

        tx = Signal()

        tx.add_signal('handle')
        for _ in range(3):
            tx.connect('handle', self.callback, pass_sig_data_to_cb=True)

        self.sig_data_passed_to_cb_list = []
        tx.disconnect_by_call_back('handle', self.callback)
        tx.send('handle')
        assert len(self.sig_data_passed_to_cb_list) == 2

        self.sig_data_passed_to_cb_list = []
        tx.disconnect_by_call_back('handle', self.callback)
        tx.send('handle')
        assert len(self.sig_data_passed_to_cb_list) == 1

        self.sig_data_passed_to_cb_list = []
        tx.disconnect_by_call_back('handle', self.callback)
        tx.send('handle')
        assert len(self.sig_data_passed_to_cb_list) == 0

    def test_passes_sig_data_as_kwargs_when_pass_sig_data_to_cb_is_true(self):
        """
        Show that send passes SignalData object to the callback as cb_kwarg[sig_data] after
        calling connect() or connect_once() with parameter pass_sig_data_to_cb=True.
        """
        self.sig_data_passed_to_cb_list = []
        tx = Signal()

        tx.add_signal('handle')
        sig_data = tx.connect('handle', self.callback, pass_sig_data_to_cb=True)
        tx.send('handle')
        assert sig_data in self.sig_data_passed_to_cb_list

    def test_extra_args_called_after_subscriber_args(self):
        """
        Assert that send's output parameters are in the following order:
            subscriber args, transmitter's args.

        This is important because allows connected signals to be daisy chained across multiple
        signal instances without mangling the args.
        """
        self.args_list = []
        tx = Signal()

        tx.add_signal('handle')
        tx.connect('handle', self.callback, 'subscriber_arg')
        tx.send('handle', 'tx_arg')

        assert self.args_list[0] == 'subscriber_arg', self.args_list
        assert self.args_list[1] == 'tx_arg'

    def test_signal_does_not_prevent_deleted_subscriber_from_garbage_collection(self):
        """
        Show that a Signal subscription does not prevent a subscriber from being
        freed by the garbage collector if the subscriber goes out of scope or gets del'd.
        """
        class internal_class:
            """class only used by this function"""
            def cb(self) -> None:
                """Sample callback"""

        ic = internal_class()
        ic_wr = weakref.ref(ic)

        tx = Signal()
        tx.add_signal('handle')
        tx.connect('handle', ic.cb)

        del ic
        gc.collect()

        assert ic_wr() is None

    def test_signal_does_not_notify_deleted_subscribers(self):
        """
        Show that a Signal subscription does not try to notify a subscriber that has gone
        out of scope or has been del'd.
        """

        class internal_class:
            """class only used by this function"""
            cb_called_n_times = 0

            def cb(self, *args, **kwargs) -> None:
                """Sample callback"""
                internal_class.cb_called_n_times += 1

        ic = internal_class()

        tx = Signal()
        tx.add_signal('handle')
        tx.connect('handle', ic.cb)

        del ic
        gc.collect()
        tx.send('handle')
        assert internal_class.cb_called_n_times == 0
