#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  book_ease.py
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
"""Entry point for book_ease program"""
import re
import logging
import gi
gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
from gi.repository import Gtk, GdkPixbuf, Gdk
from gi.repository.GdkPixbuf import Pixbuf
import signal_
import book_reader
import book_ease_tables
import player
import file_mgr

logging_stream_handler = logging.StreamHandler()
logging_stream_handler.setFormatter(logging.Formatter('%(levelname)s %(module)s:%(name)s:%(funcName)s %(message)s'))
logging.getLogger().setLevel(logging.WARNING)



class ImageView:
    """Display images inside a playlist folder"""

    # image file types supported by Image_View
    file_types = ('.jpg', '.jpeg', '.png')
    # build compiled regexes for matching list of media suffixes.
    f_type_regexes = []
    for suffix in file_types:
        suffix = '.*.\\' + suffix.strip() + '$'
        f_type_regexes.append(re.compile(suffix))

    def __init__(self, files, builder: Gtk.Builder):
        self.image_view_section = 'image_view'
        self.files = files
        self.builder = builder
        self.image_view: Gtk.Box = builder.get_object("image_view")
        self.image_view_da: Gtk.DrawingArea = builder.get_object("image_view_da")
        self.image_view_da.connect("draw", self.on_draw)
        self.image_view_da.connect('configure-event', self.on_configure)
        self.pixbuf = Pixbuf.new_from_file("python.jpg")
        self.surface = None
        # image_filetypes key has values given in a comma separated list

    def is_image_file(self, file_):
        """Test if file_ is an image file"""
        for i in self.f_type_regexes:
            if i.match(file_):
                return True
        return False

    def on_configure(self, unused_area, unused_event, unused_data=None):
        """redraw the image"""
        self.init_surface()
        self.surface.flush()

    def init_surface(self):
        """create a new image surface"""
        # Destroy previous buffer
        if self.surface is not None:
            self.surface.finish()
            self.surface = None
        # Create a new buffer
        (width, height) = self.get_image_scale()
        disp_pixbuf = self.pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)
        self.surface = Gdk.cairo_surface_create_from_pixbuf(disp_pixbuf, 1, None)

    def on_draw(self, unused_area, context):
        """draw a context on the surface"""
        if self.surface is not None:
            context.set_source_surface(self.surface, 0.25, 0.25)
            context.paint()
        else:
            print('Invalid surface')
        return False

    def get_image_scale(self):
        """get the correct width and height dimensions of an image to scale it so that it correctly fits in the view"""
        minimum_width=200
        max_height = self.image_view_da.get_allocation().height
        dest_width = minimum_width
        # set minimum size of image
        if self.image_view_da.get_allocation().width > minimum_width:
            dest_width = self.image_view_da.get_allocation().width
        # scale the image
        image_h = float(self.pixbuf.get_height())
        image_w = float(self.pixbuf.get_width())
        img_scaling = dest_width / image_w
        dest_height = image_h * img_scaling
        # don't surpass available height
        if dest_height > max_height:
            dest_height = max_height
            img_scaling = dest_height / image_h
            dest_width = image_w * img_scaling
        # don't enlarge the image
        if image_w < dest_width:
            dest_width = image_w
            dest_height = image_h
        return(dest_width, dest_height)


class MainWindow(Gtk.Window):
    """The main display window"""
    SettingsNumericDBI = book_ease_tables.SettingsNumericDBI

    def __init__(self, book_reader_window, window_pane, file_manager_pane: Gtk.Paned, builder: Gtk.Builder):
        self.book_reader_window = book_reader_window
        self.window_pane = window_pane

        self.file_manager_pane = file_manager_pane
        # visibility switches
        #
        # put the visibility switches in a set, so they can be iterated over when saving and retrieving values
        # from the database.
        self.visibility_switches = set()
        show_files_switch1: Gtk.Switch = builder.get_object("show_files_switch1")
        show_files_switch1.connect('state-set', self.on_visibility_switch_changed)
        self.visibility_switches.add(show_files_switch1)
        #
        show_files_switch2: Gtk.Switch = builder.get_object("show_files_switch2")
        show_files_switch2.connect('state-set', self.on_visibility_switch_changed)
        self.visibility_switches.add(show_files_switch2)
        #
        show_playlist_switch: Gtk.Switch = builder.get_object("show_playlist_switch")
        show_playlist_switch.connect('state-set', self.on_visibility_switch_changed)
        self.visibility_switches.add(show_playlist_switch)
        self.book_reader_view: Gtk.Box = builder.get_object("book_reader_view")
        #
        self.image_view: Gtk.Box = builder.get_object("image_view")
        show_image_switch: Gtk.Switch = builder.get_object("show_image_switch")
        show_image_switch.connect('state-set', self.on_visibility_switch_changed)
        self.visibility_switches.add(show_image_switch)
        # file_manager_pane
        if file_manager_pane_pos := self.SettingsNumericDBI.get('book_reader_window', 'file_manager_pane_pos'):
            self.file_manager_pane.set_position(file_manager_pane_pos)
        # book_reader_pane
        self.book_reader_pane: Gtk.Paned = builder.get_object("book_reader_pane")
        # set saved state
        if book_reader_pane_pos := self.SettingsNumericDBI.get('book_reader_window', 'book_reader_pane_pos'):
            self.book_reader_pane.set_position(book_reader_pane_pos)
        # window callbacks
        self.book_reader_window.connect('destroy', self.on_destroy)
        self.book_reader_window.connect('delete-event', self.on_delete_event, self.book_reader_window )
        # load previous window state
        width = book_ease_tables.SettingsNumericDBI.get('book_reader_window', 'width')
        height = book_ease_tables.SettingsNumericDBI.get('book_reader_window', 'height')
        if width and height:
            self.book_reader_window.set_default_size(width, height)
        # window_1_pane_pos = self.config['book_reader_window'].getint('window_1_pane_pos')
        if window_1_pane_pos := book_ease_tables.SettingsNumericDBI.get('book_reader_window', 'window_1_pane_pos'):
            self.window_pane.set_position(window_1_pane_pos)
        # launch
        self.book_reader_window.show_all()

        # set switch states
        # must be after the call to show all; these trigger interrupts that hide their views
        for switch in self.visibility_switches:
            state = self.SettingsNumericDBI.get_bool('book_reader_window', f'{switch.get_name()}_state')
            if state is not None:
                switch.set_state(state)

    def on_delete_event(self, unused_widget, unused_val, window=None):
        """
        The view has been closed.
        Save the view state to file
        """

        for switch in self.visibility_switches:
            self.SettingsNumericDBI.set_bool('book_reader_window', f'{switch.get_name()}_state', switch.get_state())

        book_ease_tables.SettingsNumericDBI.set('book_reader_window',
                                                'window_1_pane_pos',
                                                self.window_pane.get_position())

        book_ease_tables.SettingsNumericDBI.set('book_reader_window',
                                                'width',
                                                window.get_size()[0])

        book_ease_tables.SettingsNumericDBI.set('book_reader_window',
                                                'height',
                                                window.get_size()[1])

        book_ease_tables.SettingsNumericDBI.set('book_reader_window',
                                                'file_manager_pane_pos',
                                                self.file_manager_pane.get_position())

        book_ease_tables.SettingsNumericDBI.set('book_reader_window',
                                                'book_reader_pane_pos',
                                                self.book_reader_pane.get_position())

    def on_destroy(self, unused_window):
        """exit the gui main loop"""
        Gtk.main_quit()

    def on_visibility_switch_changed(self, switch, state):
        """manage the actions associated with the upper battery of show view switches"""
        file_manager1 = self.file_manager_pane.get_child1()
        file_manager2 = self.file_manager_pane.get_child2()
        # lookup table mapping the switches to the function to call which further depends on the state of the switch
        # This function call either shows or hides the panel associated with the switch.
        switch_functions = {
            'show_image_switch'   :(lambda x:(x and self.image_view.show       or self.image_view.hide)),
            'show_playlist_switch':(lambda x:(x and self.book_reader_view.show or self.book_reader_view.hide)),
            'show_files_switch2'  :(lambda x:(x and file_manager2.show         or file_manager2.hide)),
            'show_files_switch1'  :(lambda x:(x and file_manager1.show         or file_manager1.hide))
            }
        sw_func = switch_functions.get(switch.get_name())(state)
        sw_func()

        # deal with the parent panes needing to be hidden
        if ((not self.image_view.get_visible() and not self.book_reader_view.get_visible())
             and self.book_reader_pane.get_visible()):
            # hide the parent pane
            self.book_reader_pane.hide()
        elif ((self.image_view.get_visible() or self.book_reader_view.get_visible())
               and not self.book_reader_pane.get_visible()):
            # show the parent pane
            self.book_reader_pane.show()
        elif ((not file_manager1.get_visible() and not file_manager2.get_visible())
               and self.file_manager_pane.get_visible()):
            self.file_manager_pane.hide()
        elif ((file_manager1.get_visible() or file_manager2.get_visible())
               and not self.file_manager_pane.get_visible()):
            # show file manager pane
            self.file_manager_pane.show()

def main(unused_args):
    """entry point for book_ease"""
    # pylint: disable=unused-variable
    # unused-variables must be kept to prevent garbage collection.

    signal_.GLOBAL_TRANSMITTER = signal_.Signal()
    # book
    signal_.GLOBAL_TRANSMITTER.add_signal('open_book')
    signal_.GLOBAL_TRANSMITTER.add_signal('open_new_book')
    signal_.GLOBAL_TRANSMITTER.add_signal('book_updated')
    signal_.GLOBAL_TRANSMITTER.add_signal('bookmark_list_changed')
    # file_mgr
    # Senders of 'dir_contents_updated' are expected to send the cwd as the extra_arg
    signal_.GLOBAL_TRANSMITTER.add_signal('dir_contents_updated')

    builder = Gtk.Builder()
    builder.add_from_file("book_ease.glade")

    # file manager system
    file_manager_pane = builder.get_object("file_manager_pane")
    file_mgr_c_0 = file_mgr.FileMgrC(file_manager_pane, file_mgr_view_name="files_1")
    file_mgr_c_1 = file_mgr.FileMgrC(file_manager_pane, file_mgr_view_name="files_2")

    # image pane
    image_view_ref = ImageView(file_mgr_c_0.file_mgr, builder)

    # bookreader backend
    book_reader_ref = book_reader.BookReader(builder)

    player_c_ref = player.PlayerC(book_reader_ref, builder)

    # main window
    main_window_ref = MainWindow(
        builder.get_object("window1"), builder.get_object("window_1_pane"), file_manager_pane, builder
    )

    Gtk.main()
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
