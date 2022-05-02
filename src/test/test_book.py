# -*- coding: utf-8 -*-
#
#  test_book.py
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
import unittest
import sys
import os
import book_ease
#sys.path.insert(0, os.path.abspath("/home/mark/projects/book_ease/src"))
#from book_ease import Book
#try:
#    from book_ease import Book
#except ( ImportError):
#    pass
#    #from .book_ease import Book

#def setUpModule():
#    createConnection()
#
#def tearDownModule():
#    closeConnection()

class TestBookSignal(unittest.TestCase):
    
    
    #from book_ease import Book
    #from . import book_ease
    # method that runs before each test to set any pre-requisites 
    def setUp(self):
        self.signal_args = None 
        #pass

    # method that runs after each test to set any pre-requisites 
    def tearDown(self):
        self.signal_args = None 

    # method that runs once for this class
    @classmethod
    def setUpClass(cls):
        pass

    # method that runs once for this class
    @classmethod
    def tearDownClass(cls):
        pass

    def signal_callback(self, **kwargs):
        self.signal_args = kwargs

    def test_signal(self):
        # pass a properly formatted signal list to book.signal method
        book_ease.Book.signal(None, [('text', self.signal_callback, {'item':'it'})])
        self.assertIn('item', self.signal_args)

    def test_signal_empty_list(self):
        lst = []
        book_ease.Book.signal(self, lst)
        #self.assertEqual(self.signal_args, None)

    def test_connect_no_matching_handle(self):
        # pass an invalid sig handle to book.connect and check ensure it throws the correct exception
        try:
            book_ease.Book.connect(None, 'invalid-handle', self.signal_callback, item='it')
        except NameError as e:
            expected_exception = "('invalid-handle', \"doesn't match any signals in Book.connect()\")"
            self.assertEqual(str(e), expected_exception)

    def test_connect_matching_handle(self):
        # ensure connect is properly placing the callback data into its assigned signal list
        self.sig_l_book_data_loaded = []
        book_ease.Book.connect(self, 'book_data_loaded', self.signal_callback, item='it')
        self.assertEqual(self.sig_l_book_data_loaded[0], ('book_data_loaded', self.signal_callback, {'item':'it'}))


if __name__ == '__main__':
    unittest.main(verbosity=3)

