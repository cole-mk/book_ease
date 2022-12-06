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
from signal_ import Signal


class TestSignal:
    """
    Unit test for class signal_.Signal
    """

    def test_sends_connected_signals_multiple_times(self):
        """
        Assert that send() can transmit a signal repeatedly if it has been connected via connect().
        """
        tx = Signal()
        tx.add_signal('handle')
        callback = mock.Mock()
        tx.connect('handle', callback)

        for _ in range(3):
            tx.send('handle')

        assert callback.call_count == 3

    def test_connect_raises_key_error_if_signal_not_added(self):
        """
        Assert that connect() and connect_once() raises a KeyError if the 'handle' parameter has not previously
        been added to the list of registered signals.
        """
        tx = Signal()
        callback = mock.Mock()

        with pytest.raises(KeyError):
            tx.connect('handle', callback)

        with pytest.raises(KeyError):
            tx.connect_once('handle', callback)

    def test_remove_causes_connect_to_raise_key_error(self):
        """
        Show that remove_signal() actually removes the signal by:
        Assert that calling connect() after removing the signal raises a KeyError.
        """
        tx = Signal()
        callback = mock.Mock()

        tx.add_signal('handle')
        tx.connect('handle', callback)
        tx.remove_signal('handle')

        with pytest.raises(KeyError):
            tx.connect('handle', callback)

    def test_sends_connect_once_transmitts_a_single_time_only(self):
        """
        Show that when a signal is connected using connect_once(),
        the signal is sent only on the next call to send().
        """
        tx = Signal()
        callback = mock.Mock()

        tx.add_signal('handle')
        tx.connect_once('handle', callback)
        tx.send('handle')
        tx.send('handle')

        callback.assert_called_once()

    def test_disconnect_by_signal_data_removes_signal_from_call_list(self):
        """
        Show that disconnect_by_signal_data() removes the correct signal from the
        call lists. It cannot be fooled by identical signals connected multiple times.
        """

        tx = Signal()
        callback = mock.Mock()

        tx.add_signal('handle')
        sig_data = [tx.connect('handle', callback, pass_sig_data_to_cb=True) for _ in range(3)]
        tx.disconnect_by_signal_data(sig_data[1])
        tx.send('handle')

        signals_passed_to_cb = {call[1]['sig_data'] for call in callback.call_args_list}
        assert sig_data[0] in signals_passed_to_cb
        assert sig_data[1] not in signals_passed_to_cb
        assert sig_data[2] in signals_passed_to_cb

    def test_passes_sig_data_as_kwargs_when_pass_sig_data_to_cb_is_true(self):
        """
        Show that send passes SignalData object to the callback as cb_kwarg[sig_data] after
        calling connect() or connect_once() with parameter pass_sig_data_to_cb=True.
        """
        tx = Signal()
        callback = mock.Mock()

        tx.add_signal('handle')
        sig_data = tx.connect('handle', callback, pass_sig_data_to_cb=True)
        tx.send('handle')
        callback.assert_called_with(sig_data=sig_data)

    def test_extra_args_called_after_subscriber_args(self):
        """
        Assert that send's output parameters are in the following order:
            subscriber args, transmitter's args.

        This is important because allows connected signals to be daisy chained across multiple
        signal instances without mangling the args.
        """
        tx = Signal()
        callback = mock.Mock()

        tx.add_signal('handle')
        tx.connect('handle', callback, 'subscriber_arg')
        tx.send('handle', 'tx_arg')
        args, _ = callback.call_args
        assert args[0] == 'subscriber_arg'
        assert args[1] == 'tx_arg'
