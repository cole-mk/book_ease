#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  test_signal_.py
#
#  Copyright 2020 mark <mark@capstonedistribution.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
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
import unittest
from lib.signal_.signal_ import Signal_


class Track_Get_Entries(unittest.TestCase):

    def setUp(self):
        self.sig = Signal_()

    def tearDown(self):
        del self.sig

    def call_back(self, *cb_args, **cb_kwargs):
        self.cb_args = cb_args
        self.cb_kwargs = cb_kwargs

    def test_add_signal(self):
        # add_signal() successfully adds entry to signal handlers list
        self.sig.add_signal('test_handle')
        self.assertIn('test_handle', self.sig._sig_handlers)

    def test_remove_signal(self):
        # remove_signal() successfully removes entry from signal handlers list
        self.sig.add_signal('test_handle')
        self.sig.remove_signal('test_handle')
        self.assertNotIn('test_handle', self.sig._sig_handlers)

    def test_connect(self):
        # connect correctly appends data tuple to signal handlers list
        self.sig.add_signal('test_handle')
        self.sig.connect('test_handle', self.call_back, 'args1', 'args2', args3='argsthree', args4='argsfour')

        self.assertEqual(self.sig._sig_handlers['test_handle'][0][0], 'test_handle')
        self.assertEqual(self.sig._sig_handlers['test_handle'][0][1], self.call_back)
        self.assertEqual(self.sig._sig_handlers['test_handle'][0][2], ('args1', 'args2'))
        self.assertEqual(self.sig._sig_handlers['test_handle'][0][3]['args3'], 'argsthree')
        self.assertEqual(self.sig._sig_handlers['test_handle'][0][3]['args4'], 'argsfour')

    def test_signal(self):
        self.sig.add_signal('test_handle')
        self.sig.connect('test_handle', self.call_back, 'args1', 'args2', args3='argsthree', args4='argsfour')
        self.sig.signal('test_handle')
        self.assertEqual(self.cb_args, ('args1', 'args2'))
        self.assertEqual(self.cb_kwargs['args3'], 'argsthree')
        self.assertEqual(self.cb_kwargs['args4'], 'argsfour')


if __name__ == '__main__':
	unittest.main()
