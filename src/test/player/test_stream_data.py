# -*- coding: utf-8 -*-
#
#  test_stream_data.py
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
Unit test for class player.StreamData
"""

import player

class TestIsFullySet:
    """Unit test for method is_fully_set()"""

    def init_mocks(self):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        stream_data = player.StreamData(path='/some/path',
                                        position=player.StreamTime(0),
                                        track_number=1,
                                        playlist_id=2,
                                        pl_track_id=3)
        return stream_data

    def test_returns_true_if_all_required_attributes_are_set(self):
        """
        Assert that is_fully_set() returns True if all the "required" attributes
        have been set.
        """
        stream_data = self.init_mocks()
        assert stream_data.is_fully_set()

    def test_returns_false_if_not_all_required_attributes_are_set(self):
        """
        assert that is_fully_set() returns False if any one of the required attributes has not been given a value.
        """
        stream_data = self.init_mocks()

        for attribute in player.StreamData._required_attributes:
            tmp = getattr(stream_data, attribute)
            setattr(stream_data, attribute, None)
            assert not stream_data.is_fully_set()
            setattr(stream_data, attribute, tmp)


class TestMarkSavedPosition:
    """Unit test for method mark_saved_position()"""

    def init_mocks(self):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        stream_data = player.StreamData(path='/some/path',
                                        position=player.StreamTime(0),
                                        track_number=1,
                                        playlist_id=2,
                                        pl_track_id=3)
        return stream_data

    def test_sets_last_saved_position_to_current_time(self):
        """
        Assert that mark_saved_position() sets last_saved_position to the value held in self.position.
        """
        stream_data = self.init_mocks()
        assert stream_data.last_saved_position != stream_data.position
        stream_data.mark_saved_position()
        assert stream_data.last_saved_position == stream_data.position

