# -*- coding: utf-8 -*-
#
#  test_player.py
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
Unit test for class player.Player
"""

from unittest import mock
import pytest
# disabled because that patches use the import, by pylint doesn't see it.
import player  # pylint: disable=unused-import
from player import Player


class TestGoToPosition:
    """Unit test for method go_to_position()"""

    def test_calls_gst_player_set_position(self):
        """
        Assert that player.go_to_position() calls method GstPlayer.set_position()
        with the correct args.
        """
        m_player = Player()
        m_player.gst_player = mock.Mock()
        m_player.gst_player.set_position = mock.Mock()
        m_player.go_to_position(t_seconds=30)
        m_player.gst_player.set_position.assert_called_with(t_seconds=30)


class TestPause:
    """Unit test for method pause()"""

    @pytest.fixture()
    @mock.patch('player.GstPlayer')
    @mock.patch('player.PlayerDBI')
    def init_mocks(self, _, m_gst_player):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        player_ = Player()
        m_gst_player.pause = mock.Mock()
        return player_

    def test_calls_gst_player_pause(self, init_mocks):
        """
        Assert that pause() calls method GstPlayer.pause()
        """
        player_ = init_mocks
        player_.pause()
        assert player_.gst_player.pause.called


class TestPlay:
    """Unit test for method play()"""

    @pytest.fixture()
    @mock.patch('player.GstPlayer')
    @mock.patch('player.PlayerDBI')
    def init_mocks(self, _, m_gst_player):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        player_ = Player()
        m_gst_player.play = mock.Mock()
        return player_

    def test_play_calls_gst_player_play(self, init_mocks):
        """
        Assert that pause() calls method GstPlayer.play().
        """
        player_ = init_mocks
        player_.play()
        player_.gst_player.play.assert_called()


class TestSkipForwardLong:
    """Unit test for method skip_forward_long()"""


    @pytest.fixture()
    @mock.patch('player.GstPlayer')
    @mock.patch('player.PlayerDBI')
    def init_mocks(self, _, m_gst_player):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        player_ = Player()
        m_gst_player.set_position_relative = mock.Mock()
        return player_

    def test_skip_forward_long_calls_gst_player_set_position_relative(self, init_mocks):
        """
        Assert that skip_forward_long() calls method GstPlayer.set_position_relative().
        """
        player_ = init_mocks
        player_.skip_forward_long()
        player_.gst_player.set_position_relative.assert_called_with(delta_t_seconds=player_.skip_duration_long)


class TestSkipForwardShort:
    """Unit test for method skip_forward_short()"""


    @pytest.fixture()
    @mock.patch('player.GstPlayer')
    @mock.patch('player.PlayerDBI')
    def init_mocks(self, _, m_gst_player):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        player_ = Player()
        m_gst_player.set_position_relative = mock.Mock()
        return player_

    def test_skip_skip_forward_short_calls_gst_player_set_position_relative(self, init_mocks):
        """
        Assert that skip_forward_short() calls method GstPlayer.set_position_relative().
        """
        player_ = init_mocks
        player_.skip_forward_short()
        player_.gst_player.set_position_relative.assert_called_with(delta_t_seconds=player_.skip_duration_short)


class TestSkipReverseLong:
    """Unit test for method skip_reverse_long()"""


    @pytest.fixture()
    @mock.patch('player.GstPlayer')
    @mock.patch('player.PlayerDBI')
    def init_mocks(self, _, m_gst_player):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        player_ = Player()
        m_gst_player.set_position_relative = mock.Mock()
        return player_

    def test_skip_skip_reverse_long_calls_gst_player_set_position_relative(self, init_mocks):
        """
        Assert that skip_reverse_long() calls method GstPlayer.set_position_relative().
        """
        player_ = init_mocks
        player_.skip_reverse_long()
        delta_t_seconds = player_.skip_duration_long * -1
        player_.gst_player.set_position_relative.assert_called_with(delta_t_seconds=delta_t_seconds)


class TestSkipReverseShort:
    """Unit test for method skip_reverse_short()"""


    @pytest.fixture()
    @mock.patch('player.GstPlayer')
    @mock.patch('player.PlayerDBI')
    def init_mocks(self, _, m_gst_player):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        player_ = Player()
        m_gst_player.set_position_relative = mock.Mock()
        return player_

    def test_skip_skip_reverse_long_calls_gst_player_set_position_relative(self, init_mocks):
        """
        Assert that skip_reverse_short() calls method GstPlayer.set_position_relative().
        """
        player_ = init_mocks
        player_.skip_reverse_short()
        delta_t_seconds = player_.skip_duration_short * -1
        player_.gst_player.set_position_relative.assert_called_with(delta_t_seconds=delta_t_seconds)


class TestStop:
    """Unit test for method stop()"""

    @pytest.fixture()
    @mock.patch('player.GstPlayer')
    @mock.patch('player.PlayerDBI')
    def init_mocks(self, _, m_gst_player):
        """
        Create and return all the mocks that are used for this test class.
        They should be in a state that is conducive to passing the tests.
        """
        player_ = Player()
        m_gst_player.stop = mock.Mock()
        return player_

    def test_stop_calls_gst_player_stop(self, init_mocks):
        """
        Assert that stop() calls method GstPlayer.stop().
        """
        player_ = init_mocks
        player_.stop()
        player_.gst_player.stop.assert_called()
