# -*- coding: utf-8 -*-
#
#  test_stream_time.py
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
#
# pylint: disable=wrong-import-position
# disabled because gi.repository requires an import order that pylint dislikes.
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
# pylint: disable=too-many-lines
# disabled because this needs to be as long as it needs to be.
#
# pylint: disable=unnecessary-dunder-call
# disabled because dunder methods are being tested.
#
# pylint: disable=expression-not-assigned
# disabled because some expressions are used only for testing their side effects.
#

"""
Unit test for class player.StreamTime
"""

from unittest import mock
import pytest

import player
from player import StreamTime


class TestSetTime:
    """Unit test for method set_time()"""

    def test_requirements_exist(self):
        """
        Assert that all methods, classes, attributes,
        or any other resource needed by this method exist.
        """
        assert player.StreamTime
        assert player.StreamTime._time_conversions
        assert player.StreamTime.set_time

        st = StreamTime()
        assert st._time is None or st._time == 0

    def test_stores_time_in_ns_when_unit_not_given(self):
        """
        Assert that set_time() does not convert units when units not given
        """
        stream_time = StreamTime()
        stream_time.set_time(125)
        assert stream_time._time == 125

    def test_truncates_time_to_whole_number_when_unit_not_given(self):
        """
        Assert that set_time() strips any decimals from time_ when the units don't need to be converted.
        """
        stream_time = StreamTime()
        stream_time.set_time(125.69)
        assert stream_time._time == 125

    def test_stores_time_in_ns_when_unit_is_ms(self):
        """
        Assert that set_time() converts time_ from the passed in unit to nanoseconds correctly.
        """
        stream_time = StreamTime()
        stream_time.set_time(125, 'ms')
        assert stream_time._time == 125 * pow(10, 6)

    def test_stores_time_in_ns_when_unit_is_second(self):
        """
        Assert that set_time() converts time_ from the passed in unit to nanoseconds correctly.
        """
        stream_time = StreamTime()
        stream_time.set_time(125, 's')
        assert stream_time._time == 125 * pow(10, 9)

    def test_truncates_time_to_whole_number_ns_when_unit_given(self):
        """
        Assert that set_time() strips any decimals from time_ when the units are converted.
        """
        crazy_number_in_ms = 125.69696969696969
        truncated_crazy_number_in_ns = int(crazy_number_in_ms * pow(10, 6))

        stream_time = StreamTime()
        stream_time.set_time(crazy_number_in_ms, 'ms')
        assert stream_time._time == truncated_crazy_number_in_ns


class TestGetTime:
    """Unit test for method get_time()"""

    def test_requirements_exist(self):
        """
        Assert that all methods, classes, attributes,
        or any other resource needed by this method exist.
        """
        assert player.StreamTime
        assert player.StreamTime._time_conversions
        assert player.StreamTime.get_time

        st = StreamTime()
        assert st._time is None or st._time == 0

    def test_truncates_decimals_to_whole_numbers_when_converting_units(self):
        """
        Assert that when get_time() returns time_ in the requested unit,
        that number has the remainder truncated from the number.
        """
        stream_time = StreamTime(time_=123456789)
        time_ms = stream_time.get_time('ms')
        assert time_ms == 123

    def test_returns_time_in_ns_when_units_not_given(self):
        """
        Assert that  get_time() returns time_ unchanged when units not given.
        """
        stream_time = StreamTime(time_=123)
        time_ms = stream_time.get_time()
        assert time_ms == 123

    def test_returns_time_in_ms_when_unit_is_ms(self):
        """
        Assert that get_time() returns time_ in milliseconds when unit is 'ms'.
        """
        time_ms = 123
        time_ns = 123 * pow(10, 6)
        stream_time = StreamTime(time_=time_ns)
        test_time_ms = stream_time.get_time('ms')
        assert test_time_ms == time_ms

    def test_returns_time_in_seconds_when_unit_is_seconds(self):
        """
        Assert that get_time() returns time_ in milliseconds when unit is 's'.
        """
        time_s = 123
        time_ns = 123 * pow(10, 9)
        stream_time = StreamTime(time_=time_ns)
        test_time_ms = stream_time.get_time('s')
        assert test_time_ms == time_s


class TestInit:
    """Unit test for method __init__()"""

    def test_requirements_exist(self):
        """
        Assert that all methods, classes, attributes,
        or any other resource needed by this method exist.
        """
        assert player.StreamTime
        assert player.StreamTime._time_conversions
        assert player.StreamTime.set_time

        st = StreamTime()
        assert st._time is None or st._time == 0

    @mock.patch('player.StreamTime.set_time')
    def test_sets_time_to_none_when_no_args_given(self, m_set_time):
        """
        Assert that __init__() sets self._time to None when no args are given.
        It should not call self.set_time().
        """
        test_time = StreamTime()
        m_set_time.assert_not_called()
        assert test_time._time is None

    @mock.patch('player.StreamTime.set_time')
    def test_calls_set_time_with_time_and_ns_when_only_time_given(self, m_set_time):
        """
        Assert that __init__() calls self.set_time() with the following parameters,
        when __init__() is called with only the time given as arg:
        time_=time, unit='ns'
        """
        StreamTime(time_=123)
        m_set_time.assert_called_with(time_=123, unit='ns')

    @mock.patch('player.StreamTime.set_time')
    def test_calls_set_time_with_time_and_unit_when_time_and_unit_given(self, m_set_time):
        """
        Assert that __init__() calls self.set_time() with the following parameters,
        when __init__() is called with only time and units given as arg:
        time_=time, unit=unit
        """
        StreamTime(time_=123, unit='s')
        m_set_time.assert_called_with(time_=123, unit='s')

        StreamTime(time_=123, unit='ms')
        m_set_time.assert_called_with(time_=123, unit='ms')

        StreamTime(time_=123, unit='ns')
        m_set_time.assert_called_with(time_=123, unit='ns')


class TestEQ:
    """Unit test for the method __eq__()"""

    def test_returns_true_when_same_time(self):
        """
        Assert that __eq__() returns True when the time values of two StreamTime objects are equal.
        """
        st1 = StreamTime(30)
        st2 = StreamTime(30)
        assert st1.__eq__(st2) is True

    def test_returns_false_when_different_time(self):
        """
        Assert that __eq__() returns False when the time values of two StreamTime objects are different.
        """
        st1 = StreamTime(30)
        st2 = StreamTime(20)
        assert st1.__eq__(st2) is False

    def test_raises_type_error_when_comparing_different_classes(self):
        """
        Assert that __eq__() returns False when the other object is not a StreamTime object.
        """
        st1 = StreamTime(30)
        st2 = 30
        with pytest.raises(TypeError):
            st1.__eq__(st2) is False


class TestAdd:
    """Unit test for the method __add__()"""

    def test_raises_type_error_if_other_is_not_stream_time(self):
        """
        Assert that __add__() raises TypeError of other is not a StreamTime object.
        """
        with pytest.raises(TypeError):
            StreamTime(30) + 1

    def test_sums_two_stream_times(self):
        """
        Assert that __add__() sums the times stored by two Streamtime objects.
        """
        assert StreamTime(30) + StreamTime(69) == StreamTime(99)
        assert StreamTime(30) + StreamTime(-69) == StreamTime(-39)
        assert StreamTime(-30) + StreamTime(-69) == StreamTime(-99)
        assert StreamTime(-30) + StreamTime(69) == StreamTime(39)


class TestSub:
    """Unit test for the method __sub__()"""

    def test_raises_type_error_if_other_is_not_stream_time(self):
        """
        Assert that __sub__() raises TypeError of other is not a StreamTime object.
        """
        with pytest.raises(TypeError):
            StreamTime(30) - 1

    def test_subtracts_two_stream_times(self):
        """
        Assert that __sub__() finds the difference between the times stored by two Streamtime objects.
        """
        assert StreamTime(30) - StreamTime(-69) == StreamTime(99)
        assert StreamTime(30) - StreamTime(69) == StreamTime(-39)
        assert StreamTime(-30) - StreamTime(69) == StreamTime(-99)
        assert StreamTime(-30) - StreamTime(-69) == StreamTime(39)
