# -*- coding: utf-8 -*-
#
#  book_reader_view.py
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
This all the views that constitute the book reader view.
It is a container for displaying books in a gtk notebook, as well as views for the utility components that control the
opening and closing of books.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import pathlib
import gi
gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
from gi.repository import Gtk  # noqa: E402
if TYPE_CHECKING:
    import book_reader


class BookReaderNoteBookTabV:
    """
    Encapsulate a Gtk.label and a Gtk.Button in a Gtk.Box that is displayed in the tab of the BookReaderV notebook.
    The label holds a (possibly truncated) title of the book displayed in the current notebook page.
    The button is for closing the book.
    """

    def __init__(self):
        self.view = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.title_label = Gtk.Label()
        image = Gtk.Image.new_from_icon_name('window-close', Gtk.IconSize.SMALL_TOOLBAR)
        self.close_button = Gtk.Button(label=None, image=image)
        self.close_button.set_relief(Gtk.ReliefStyle.NONE)
        self.view.pack_start(self.title_label, expand=False, fill=False, padding=0)
        self.view.pack_start(self.close_button, expand=False, fill=False, padding=0)
        self.view.show_all()

    def get_view(self) -> Gtk.Box:
        """Get the Gtk.Box container."""
        return self.view

    def set_label(self, label: str):
        """Set the text in the title label"""
        self.title_label.set_label(label)


class BookReaderV:  # pylint: disable=too-few-public-methods
    """The outermost view of the BookReader"""

    def __init__(self, book_view_builder: Gtk.Builder):
        # Load the gui from glade
        self.builder = Gtk.Builder()
        glade_path = pathlib.Path.cwd() / 'gui' / 'gtk' / 'book_reader.glade'
        self.builder.add_from_file(str(glade_path))
        book_reader_view: Gtk.Box = self.builder.get_object('book_reader_view')
        # Load the container from the book_view_builder into which the BookReader view will be displayed.
        book_view_container: Gtk.Box = book_view_builder.get_object('book_reader_view')
        book_view_container.pack_start(book_reader_view, expand=True, fill=True, padding=0)


    def get_builder(self) -> Gtk.Builder:
        """get the builder object"""
        return self.builder


class StartPageV:
    """Gtk view of the start page"""

    def __init__(self, gui_builder: Gtk.Builder):
        self.view: Gtk.Box = gui_builder.get_object('start_page')
        self.tab_label = Gtk.Label()

    def add_view(self, view: Gtk.Widget):
        """append a view to the start page view"""
        self.view.pack_start(view, expand=True, fill=True, padding=0)

    def get_view(self):
        """get the Gtk container that is the start page view"""
        return self.view

    def get_tab_label(self) -> Gtk.Label:
        """Get the tab label."""
        return self.tab_label

    def set_tab_label(self, text: str):
        """Set text of the tab label."""
        self.tab_label.set_label(text)


class NoteBookV:  # pylint: disable=too-few-public-methods
    """Gtk view of the book_reader.NoteBook"""

    def __init__(self, gui_builder: Gtk.Builder):
        self.note_book: Gtk.Notebook = gui_builder.get_object('note_book')

    def append_page(self,
                    view: Gtk.Widget,
                    note_book_tab_view: Gtk.Widget):
        """set a book view to a new notebook tab"""
        new_page = self.note_book.append_page(view, note_book_tab_view)
        self.note_book.show_all()
        self.note_book.set_current_page(new_page)


class NoteBookPageV(Gtk.Box):
    """
    Adapter view for placing gtk widgets in a notebook, allowing them to be searched by id.
    """

    def __init__(self,
                 page_view: Gtk.Widget,
                 id_: int = None):

        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_page_view(page_view)
        self.id_ = id_
        self.show_all()

    def close(self):
        """Destroy self so that the Notebook page can actually close"""
        self.destroy()

    def set_id(self, id_: int):
        """Set the id of this page view"""
        self.id_ = id_

    def get_id(self) -> int:
        """Get the id of this page view"""
        return self.id_

    def set_page_view(self, page_view: Gtk.Widget):
        """Add page_view to self for display after clearing any old views from self."""
        for view in self:
            self.remove(view)
        self.pack_start(page_view, expand=True, fill=True, padding=0)
