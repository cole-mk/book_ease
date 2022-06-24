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
import os
import configparser
from datetime import datetime
import re
from pathlib import Path
#pylint: disable=unused-import
import pdb
#pylint: enable=unused-import
import gi
#pylint: disable=wrong-import-position
gi.require_version("Gtk", "3.0")
#pylint: enable=wrong-import-position
from gi.repository import Gtk, GdkPixbuf, Gdk
from gi.repository.GdkPixbuf import Pixbuf
import signal_
import pinned_books
import book


class RenameTvEntryDialog(Gtk.Dialog):
    """Dialog for renaming a bookmark"""

    def __init__(self, title="My Dialog"):
        self.title=title
        super().__init__(title=self.title, transient_for=None, flags=0)

        self.add_buttons(Gtk.STOCK_CANCEL,
                         Gtk.ResponseType.CANCEL,
                         Gtk.STOCK_OK,
                         Gtk.ResponseType.OK)

        self.set_default_size(300, 150)
        self.label_1 = Gtk.Label()
        self.label_1.set_xalign(0)
        self.entry_1 = Gtk.Entry()
        self.label_2 = Gtk.Label()
        self.label_2.set_xalign(0)
        self.entry_2 = Gtk.Entry()

        box = self.get_content_area()
        box.pack_start(self.label_1, True, True, 0)
        box.pack_start(self.entry_1, True, True, 0)
        box.pack_start(self.label_2, True, True, 0)
        box.pack_start(self.entry_2, True, True, 0)
        self.show_all()

    def add_filechooser_dialog(self, file_chooser_method=None):
        """Allow Bookmark to assign a file choser diaog for this dialog to use"""
        self.entry_2.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, 'folder')
        self.entry_2.connect('icon-press', self.on_file_chooser_icon_pressed, file_chooser_method)

    def on_file_chooser_icon_pressed(self, unused_1, unused_2, unused_3, file_chooser_method=None):
        """callback to start the filechooser dialof that was assigned to this class in add_filechooser_dialog"""
        name, path = file_chooser_method()
        if name and path:
            self.entry_2.set_text(path)


class BookMark:
    """Controller and View for Bookmark functionality inside the file view"""
    def __init__(self, bookmark_view, f_view, files, config):
        self.files = files
        self.config = config
        self.config_section_name = 'bookmarks'
        self.f_view = f_view

        self.icon_pos, self.name_pos, self.target_pos = (0, 1, 2)
        self.bookmark_model = Gtk.ListStore(Pixbuf, str, str)
        self.bookmark_model.connect('row-deleted', self.on_row_deleted)

        self.bookmark_view = bookmark_view
        self.bookmark_view.connect('button-press-event', self.on_button_press)
        self.bookmark_view.connect('button-release-event', self.on_button_release)
        self.bookmark_view.set_model(self.bookmark_model)
        self.bookmark_view.set_show_expanders (False)
        self.bookmark_view.unset_rows_drag_dest()
        self.bookmark_view.unset_rows_drag_source()
        self.renderer_icon = Gtk.CellRendererPixbuf()

        self.renderer_text = Gtk.CellRendererText()
        self.renderer_text.editable = True

        self.column = Gtk.TreeViewColumn("Bookmarks")
        self.column.pack_start(self.renderer_icon, False)
        self.column.pack_start(self.renderer_text, True)
        self.column.add_attribute(self.renderer_icon, "pixbuf", self.icon_pos)
        self.column.add_attribute(self.renderer_text, "text", self.name_pos)

        self.bookmark_view.append_column(self.column)
        self.bookmark_view.set_reorderable(True)

        self.reload_bookmarks()

        # right click context menu
        self.cmenu = Gtk.Menu.new()
        self.cmenu.connect('deactivate', self.cm_on_deactivate)

        self.cm_add_bm = Gtk.MenuItem.new_with_label('add bookmark')
        self.cm_add_bm.connect('button-release-event', self.cm_on_item_button_release, 'add bookmark')
        self.cmenu.append(self.cm_add_bm)

        self.cm_remove_bm = Gtk.MenuItem.new_with_label('remove bookmark')
        self.cm_remove_bm.connect('button-release-event', self.cm_on_item_button_release, 'remove bookmark')
        self.cmenu.append(self.cm_remove_bm)

        self.cm_rename_bm = Gtk.MenuItem.new_with_label('rename bookmark')
        self.cm_rename_bm.connect('button-release-event', self.cm_on_item_button_release, 'rename bookmark')
        self.cmenu.append(self.cm_rename_bm)

        self.cmenu.show_all()

    def remove_selected_bookmark(self):
        """delete the selected bookmark and remove it from the view"""
        sel = self.bookmark_view.get_selection()
        model, paths = sel.get_selected_rows()
        sel.unselect_all()
        # reversed so the itr isn't corrupted on multiselect
        for pth in reversed(paths):
            itr = model.get_iter(pth)
            model.remove(itr)

    def rename_selected_bookmark(self):
        """
        rename the selected bookmark
        by creating a user input dialog to set the name
        """
        sel = self.bookmark_view.get_selection()
        model, paths = sel.get_selected_rows()
        sel.unselect_all()
        # get the selected bookmark model from the row
        for pth in paths:
            itr = model.get_iter(pth)
            name = model.get_value(itr, self.name_pos)
            target = model.get_value(itr, self.target_pos)
            # get rename info from the user
            dialog = RenameTvEntryDialog(title='Rename Bookmark')
            dialog.label_1.set_text("Rename: " + name)
            dialog.entry_1.set_text(name)
            dialog.entry_1.select_region(0 , -1)
            dialog.label_2.set_text('target:')
            dialog.entry_2.set_text(target)
            dialog.entry_2.set_editable(False)
            dialog.add_filechooser_dialog(self.select_dir_dialog)
            response = dialog.run()

            if response == Gtk.ResponseType.OK:
                name = dialog.entry_1.get_text()
                target = dialog.entry_2.get_text()
                model.set_value(itr, self.name_pos, name)
                model.set_value(itr, self.target_pos, target)
                # update config for data persistence
                self.update_bookmark_config()
            dialog.destroy()

    def select_dir_dialog(self):
        """
        File choser dialog used by BookMark class
        needs to be moved to its own class
        """
        name = None
        target = None
        dialog = Gtk.FileChooserDialog(
            title="Please choose a folder",
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, "Select", Gtk.ResponseType.OK
        )
        dialog.set_default_size(800, 400)
        dialog.set_current_folder(self.files.get_path_current())
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            target = dialog.get_filename()
            name = os.path.basename(target)
        dialog.destroy()
        return  name, target

    def add_bookmark(self, name, path):
        """
        add bookmark, defined by name and path, by adding it
        to the bookmark model and saving it to file
        """
        if name is not None and path is not None:
            icon = Gtk.IconTheme.get_default().load_icon('folder', 24, 0)
            self.bookmark_model.append([icon, name, path])
            # update the config for data persistence
            self.config.set(self.config_section_name, name, path)

    def cm_on_deactivate(self):
        """
        callback to cleanup after a context menu is closed
        unselects any entries in the view that were being acted upon by the context menu
        """
        sel = self.bookmark_view.get_selection()
        sel.unselect_all()

    def cm_on_item_button_release(self, unused_button, event, user_data=None):
        """
        do task based on context menu selection by the user
        """
        if event.get_button()[0] is True:
            if event.get_button()[1] == 1:
                #print('left button clicked')
                if 'remove bookmark' == user_data:
                    self.remove_selected_bookmark()
                elif 'add bookmark' == user_data:
                    name, path = self.select_dir_dialog()
                    self.add_bookmark(name, path)
                elif 'rename bookmark' == user_data:
                    self.rename_selected_bookmark()

    def on_button_release(self, unused_button, event):
        """
        change to the directory targeted by the clicked bookmark
        """
        if event.get_button()[0] is True:
            if event.get_button()[1] == 1:
                # cd to the directory targeted in the selected bookmark
                tvs = self.bookmark_view.get_selection()
                (model, pathlist) = tvs.get_selected_rows()
                for path in pathlist :
                    tree_iter = model.get_iter(path)
                    value = model.get_value(tree_iter, self.target_pos)
                    tvs.unselect_all()
                    self.files.cd(value)

    def on_button_press(self, unused_button, event):
        """
        handle callbacks for a button press on a bookmark by any mouse button.
        currently its only action is to call a context menu when the bookmark view is right clicked
        """
        if event.get_button()[0] is True:
            if event.get_button()[1] == 1:
                pass
                #print('left button clicked')
            if event.get_button()[1] == 2:
                pass
                #print('middle button clicked')
            if event.get_button()[1] == 3:
                self.cmenu.popup_at_pointer()
                #print('right button clicked')
            if event.get_button()[1] == 8:
                pass
                #print('back button clicked')
            if event.get_button()[1] == 9:
                pass
                #print('forward button clicked')

    def on_row_deleted(self, unused_path, unused_user_data=None):
        """callback for treestore row deleted, catching the user drag icons to reorder"""
        self.update_bookmark_config()

    def update_bookmark_config(self):
        """clear and resave all of the bookmarks with current values"""
        self.config.remove_section(self.config_section_name)
        self.config.add_section(self.config_section_name)
        for i in self.bookmark_model:
            self.config.set(self.config_section_name, i[1], i[2])

    def reload_bookmarks(self):
        """
        load saved bookmarks into the bookmark treeview
        Note: this does not reload, it only appends
        """
        for key in self.config[self.config_section_name]:
            if os.path.isdir(self.config[self.config_section_name][key]):
                icon = Gtk.IconTheme.get_default().load_icon('folder', 24, 0)
                self.bookmark_model.append([icon, key, self.config[self.config_section_name][key]])


class Image_View:
    """Display images inside a playlist folder"""

    def __init__(self, files, config, builder):
        self.image_view_section = 'image_view'
        self.files = files
        self.config = config
        self.builder = builder
        self.image_view = builder.get_object("image_view")
        self.image_view_da = builder.get_object("image_view_da")
        self.image_view_da.connect("draw", self.on_draw)
        self.image_view_da.connect('configure-event', self.on_configure)
        self.pixbuf = Pixbuf.new_from_file("python.jpg")
        self.surface = None
        # TODO: setup locating the image files automatically
        # image_filetypes key has values given in a comma separated list
        file_types = config[self.image_view_section]['image_filetypes'].split(",")
        # build compiled regexes for matching list of media suffixes.
        self.f_type_re = []
        for i in file_types:
            i = '.*.\\' + i.strip() + '$'
            self.f_type_re.append(re.compile(i))

    def is_image_file(self, file_):
        """Test if file_ is an image file"""
        for i in self.f_type_re:
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


class BookReader_View:
    """
    The outer most view of the bookreader pane containing a notebook to display individual books as well as several
    control buttons to manage the books
    """

    def __init__(self, br_view, book_reader, pinned_view):
        self.br_view = br_view
        self.book_reader = book_reader

        # add gui keys to helpers for accessing playlist data stored in db
        self.cur_pl_id = {'col':0, 'col_name':'id', 'g_type':int, 'g_col':0}
        self.cur_pl_title  = {'col':1, 'col_name':'title', 'g_type':str, 'g_col':1}
        self.cur_pl_path  = {'col':2, 'col_name':'path', 'g_type':str, 'g_col':2}
        self.cur_pl_helper_l = [self.cur_pl_id, self.cur_pl_title, self.cur_pl_path]
        self.cur_pl_helper_l.sort(key=lambda col: col['col'])

        self.outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        # a view of the pinned books that will be displayed on the start page
        self.pinned_view = pinned_view

        self.book_reader_notebook = Gtk.Notebook()
        self.start_page = self.build_start_page()
        self.start_page_label = Gtk.Label(label="Start")
        self.book_reader_notebook.append_page(self.start_page, self.start_page_label)
        # has_new_media notification
        self.has_new_media_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.has_new_media_box.set_no_show_all(True)
        self.create_pl_btn = Gtk.Button(label='Create')
        self.has_new_media_box.pack_start(self.create_pl_btn, expand=False, fill=False, padding=0)
        self.create_pl_label = Gtk.Label('New Playlist')
        self.create_pl_label.set_margin_right(4)
        self.has_new_media_box.pack_start(self.create_pl_label, expand=False, fill=False, padding=0)
        self.has_new_media_box.set_child_packing(child=self.create_pl_label, expand=False, fill=False,
                                                 padding=0, pack_type=Gtk.PackType.END)

        self.has_new_media_box.set_child_packing(child=self.create_pl_btn, expand=False, fill=False,
                                                 padding=0, pack_type=Gtk.PackType.END)

        self.create_pl_btn.connect('button-release-event', self.on_button_release)

        self.header_box.pack_end(self.has_new_media_box, expand=False, fill=False, padding=10)

        # has_book_box notification
        self.has_book_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.has_book_box.set_no_show_all(True)
        self.has_book_box.show()
        self.open_book_btn = Gtk.Button(label='Open')
        #self.open_book_btn.show()
        self.has_book_box.pack_start(self.open_book_btn, expand=False, fill=False, padding=0)
        self.has_book_box.set_child_packing(child=self.open_book_btn, expand=False, fill=False,
                                            padding=0, pack_type=Gtk.PackType.END)

        # extract list of g_types from self.cur_pl_helper_l that was previously sorted by col number
        # use list to initialize self.cur_pl_list, our model for displayling
        # all playlists associated ith the current path
        g_types = map(lambda x: x['g_type'], self.cur_pl_helper_l)
        self.cur_pl_list = Gtk.ListStore(*g_types)

        self.has_book_combo = Gtk.ComboBox.new_with_model(self.cur_pl_list)
        renderer_text = Gtk.CellRendererText()
        self.has_book_combo.pack_start(renderer_text, True)
        self.has_book_combo.add_attribute(renderer_text, "text", self.cur_pl_title['g_col'])
        self.has_book_combo.set_active(0)
        self.has_book_box.pack_start(self.has_book_combo, expand=False, fill=False, padding=0)
        self.has_book_box.set_child_packing(child=self.has_book_combo, expand=False, fill=False,
                                            padding=0, pack_type=Gtk.PackType.END)

        self.open_book_btn.connect('button-release-event', self.on_button_release)

        self.header_box.pack_end(self.has_book_box, expand=False, fill=False, padding=10)


        self.header_box.hide()

        self.outer_box.pack_start(self.header_box, expand=False, fill=False, padding=0)
        self.outer_box.pack_start(self.book_reader_notebook, expand=True, fill=True, padding=0)

        self.br_view.pack_start(self.outer_box, expand=True, fill=True, padding=0)

    def on_button_release(self, btn, evt, unused_data=None):
        """
        callback for the various control buttons
        currently takes actions for creating a new book and opening a new book
        """
        if evt.get_button()[0] is True:
            if evt.get_button()[1] == 1:
                if btn is self.create_pl_btn:
                    self.book_reader.open_new_book()
                if btn is self.open_book_btn:
                    # open book button was pressed
                    # get the selected title from the has_book_combo
                    # and pass it to book reader for opening the playlist
                    model = self.has_book_combo.get_model()
                    sel = self.has_book_combo.get_active()
                    itr = model.get_iter((sel,))
                    # get entire row from model
                    cols = map(lambda x: x['col'], self.cur_pl_helper_l)
                    pl_row = model.get(itr, *cols)
                    # extract playlist data from row
                    playlist_data = book.PlaylistData()
                    playlist_data.set_id(pl_row[self.cur_pl_id['col']])
                    playlist_data.set_path(pl_row[self.cur_pl_path['col']])
                    playlist_data.set_title(pl_row[self.cur_pl_title['col']])
                    self.book_reader.open_existing_book(playlist_data)

    def on_has_new_media(self, has_new_media):
        """allow book_reader_view to tell the view if there are media files in the directory"""
        if has_new_media:
            self.has_new_media_box.set_no_show_all(False)
            self.has_new_media_box.show_all()
            self.has_new_media_box.set_no_show_all(True)
        else:
            self.has_new_media_box.hide()

    def on_has_book(self, has_book, playlists_in_path=None):
        """
        Allow book_reader_view to tell the view if there are any playlists associated with the current path.

        The has book box is a combo box containing the list of those playlists.

        This method shows or hides the has_book_box based on the value of has_book and updates the combo box model with
        the playlists in playlists_in_path
        """
        # model holds list of existing playlist titles
        model = self.has_book_combo.get_model()
        model.clear()
        if  has_book:
            for playlst_data in playlists_in_path:
                itr = model.append()
                model.set_value(itr, self.cur_pl_id['col'], playlst_data.get_id())
                model.set_value(itr, self.cur_pl_title['col'], playlst_data.get_title())
                model.set_value(itr, self.cur_pl_path['col'], playlst_data.get_path())
            # display option to open existing playlist
            self.has_book_box.set_no_show_all(False)
            self.has_book_box.show_all()
            self.has_book_combo.set_active(0)
            self.has_book_box.set_no_show_all(True)
        else:
            self.has_book_box.hide()

    def append_book(self, view, title):
        """set a book view to a new notebook tab"""
        label = Gtk.Label(label=title[0:8])
        newpage = self.book_reader_notebook.append_page(view, label)
        self.book_reader_notebook.show_all()
        self.book_reader_notebook.set_current_page(newpage)
        # this needs to be changed we're not using the returned tuple
        return newpage, view

    def build_start_page(self):
        """build the content of the first notebook tab for displaying non-specific-book information"""
        start_label = Gtk.Label(label="Welcome to BookEase")
        start_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        start_box.pack_start(start_label, expand=False, fill=False, padding=20)
        start_box.pack_start(self.pinned_view, expand=True, fill=True, padding=20)

        return start_box
        #self.add(start_box)


class BookReader_:
    """class to manage the state of many books"""

    def __init__(self, files, config, builder):
        self.book_reader_section = 'book_reader'
        self.cur_path = None
        self.files = files
        self.config = config
        self.playlist_file = self.config['book_reader']['playlist_file']
        self.book_reader_dir = self.config['book_reader']['book_reader_dir']
        # playlists database helper
        self.playlist_dbi = book.PlaylistDBI()

        # pinned playlists that will be displayed bookReader_View
        self.pinned_books =  pinned_books.PinnedBooksC()

        # register a updated file list callback with files instance
        self.files.connect('file_list_updated', self.on_file_list_updated, get_cur_path=self.files.get_path_current)
        self.book_conf = configparser.ConfigParser()
        self.found_book_path = None
        self.book_path = None
        self.book_open = False
        # books
        self.books = []
        self.book_cache = []
        self.tmp_book = None
        # playlist_filetypes key has values given in a comma separated list
        file_types = config[self.book_reader_section]['playlist_filetypes'].split(",")
        # build compiled regexes for matching list of media suffixes.
        self.f_type_re = []
        for i in file_types:
            i = '.*.\\' + i.strip() + '$'
            self.f_type_re.append(re.compile(i))

        self.book_reader_view = BookReader_View(
            builder.get_object("book_reader_view"),
            self,
            self.pinned_books.get_view()
        )

    def has_book(self, pth):
        """determine if there is a playlist associated with the directory, pth"""
        br_path = os.path.join(pth, self.book_reader_dir, self.playlist_file)
        if os.path.exists(br_path):
            return True
        return False

    def get_book(self, index):
        """retrieve a book from the book list"""
        return self.books[index]

    def remove_book(self, book_index):
        """remove a book from the book list"""
        self.books.pop(book_index)
        # propogate changes to book list indices
        while book_index < len(self.books):
            self.get_book(book_index)[0].set_index(book_index)
            book_index+=1

    def on_file_list_updated(self, get_cur_path):
        """
        Files is notifying bookreader that it has changed directories and is giving Book reader the list of files in
        the new current working directory.

        Tell BookReader_View if there are any saved playlists associated with this directory.

        Tell BookReader_View if there are any media files that can be used to create a playlist.
        """
        # conditions that need to be considered:
        # are there any media files in the directory
        # Is there a pre-existing playlist in the dir already
        # Do in View: Is there a playlist for the directory open in the bookreader view(is there an open book)
        # deal with the cache complication I created on day 1
        self.cur_path = get_cur_path()
        playlists_in_path = self.playlist_dbi.get_by_path(book.PlaylistData(path=self.cur_path))
        if len(playlists_in_path) > 0:
            self.book_reader_view.on_has_book(has_book=True, playlists_in_path=playlists_in_path)
        else:
            self.book_reader_view.on_has_book(has_book=False)

        # tell view we have files available if they are media files. offer to create new playlist
        f_list = self.files.get_file_list()
        has_new_media=False
        for i in f_list:
            if book.TrackFI.is_media_file(i[1]):
                has_new_media=True
                break
        self.book_reader_view.on_has_new_media(has_new_media)

    def append_book(self, book_):
        """append book to list of opened books"""
        index = len(self.books)
        book_.set_index(index)
        self.books.append(book_)
        return index

    def open_existing_book(self, pl_row):
        """
        create a new Book instance and tell it to load a saved playlist.
        append the new Book to the booklist for later usage
        """
        book_ = book.Book_C(self.cur_path, None, self.config, self.files, self)
        book_.page = self.book_reader_view.append_book(book_.get_view, book_.get_title())
        self.append_book(book_)
        # load the playlist metadata
        book_.open_existing_playlist(pl_row)
        # load the playlist metadata in background
        #load_book_data_th = Thread(target=bk.book_data_load, args={row})
        #load_book_data_th.setDaemon(True)
        #load_book_data_th.start()

    def open_new_book(self):
        """
        create a new Book instance and tell it to create a new playlist.
        append the new Book to the booklist for later usage
        """
        f_list = self.files.get_file_list_new()
        self.files.populate_file_list(f_list, self.cur_path)
        book_ = book.Book_C(self.cur_path, f_list, self.config, self.files, self)
        self.append_book(book_)
        book_.page = self.book_reader_view.append_book(book_.get_view(), book_.get_title())
        # clear book_reader_view.has_new_media flag
        self.book_reader_view.on_has_new_media(False)
        # load the playlist metadata
        book_.open_new_playlist()
        # load the playlist metadata in background
        #create_book_data_th = Thread(target=bk.open_new_playlist)
        #create_book_data_th.setDaemon(True)
        #create_book_data_th.start()

    def is_media_file(self, file_):
        """determine is file_ matches any of the media file definitions"""
        for i in self.f_type_re:
            if i.match(file_):
                return True
        return False

    def close_book(self, books_index):
        """remove a book from the books list and tel its view to close"""
        self.remove_book(books_index)
        # close the bookview
        book_v = self.get_book(books_index)[1]
        book_v.close()

    def book_editing_cancelled(self, books_index):
        """
        callback for when a book view's cancel editing button has been pressed
        close the book if it wasn't already saved and reload if it was
        This is bookreader playing repeater for the Book system again.
        It needs to be moved to Book_C.
        """
        book_ = self.get_book(books_index)[0]
        if book_.is_saved():
            # clear the tracklist and reload from DB
            pl_row = book_.get_cur_pl_row()
            book_.clear_track_list()
            book_.book_data_load(pl_row)
        else:
            # close the playlist
            self.close_book(books_index)


class Files_(signal_.Signal):
    """class to manage the file management features of book_ease"""

    def __init__(self, config):
        signal_.Signal.__init__(self)
        self.config = config
        self.library_path = self.config['app']['library path']
        self.current_path = self.library_path
        self.path_back_max_len = 10
        self.path_ahead_max_len = 10
        self.path_back = []
        self.path_ahead = []
        self.show_hidden_files = False
        self.sort_ignore_case = True
        self.sort_dir_first = True

        self.file_list = self.get_file_list_new()
        self.icon_pos, self.f_name_pos, self.is_dir_pos, self.f_size_pos, self.f_units_pos, self.ctime_pos \
            = (0, 1, 2, 3, 4, 5)

        # Signals
        # Notify of file changes
        self.add_signal('file_list_updated')
        # populate the file_list
        self.__update_file_list()

    def __update_file_list(self):
        """repopulate the files list gtk model with the files in cwd"""
        self.file_list.clear()
        self.populate_file_list(self.file_list, self.current_path)
        # notify subscribers that the file list has been updated
        self.send('file_list_updated')

    def get_file_list_new(self):
        """create a new file list model for the files view"""
        f_list = Gtk.ListStore(Pixbuf, str, bool, str, str, str)
        return f_list

    def populate_file_list(self, file_list, path):
        """Determine if files in path, directory, are suitable to be displayed and add them to the file_list"""
        files = os.scandir(path)
        # populate liststore
        for i in files:
            # ignore things like broken symlinks
            if not i.is_file() and not i.is_dir():
                continue
            # user option
            if not self.show_hidden_files and self.is_hidden_file(i.name):
                continue
            # format timestamp
            timestamp_formatted = datetime.fromtimestamp(i.stat().st_ctime).strftime("%y/%m/%d  %H:%M")
            # format file size and select correct units
            size_f, units = self.format_f_size(i.stat().st_size)
            # set correct icon
            icon = Gtk.IconTheme.get_default().load_icon('multimedia-player', 24, 0)
            if i.is_dir():
                icon = Gtk.IconTheme.get_default().load_icon('folder', 24, 0)
            # append to file list
            file_list.append([icon, i.name, i.is_dir(), size_f, units, str(timestamp_formatted)])


    def get_file_list(self):
        """retrieve self.file_list"""
        return self.file_list

    # callback signaled by Files_View
    def cmp_f_list_dir_fst(self, model, row1, row2):
        """
        compare method for sorting sort columns in the file view
        returns gt:1 lt:-1 or eq:0
        """
        sort_column, sort_order = model.get_sort_column_id()
        name1 = model.get_value(row1, sort_column)
        name2 = model.get_value(row2, sort_column)

        if self.sort_ignore_case:
            name1 = name1.lower()
            name2 = name2.lower()

        if self.sort_dir_first:
            is_dir_1 = model.get_value(row1, 2)
            is_dir_2 = model.get_value(row2, 2)
            # account for the sort order when returning directories first
            direction = 1
            if sort_order is Gtk.SortType.DESCENDING:
                direction = -1
            #return immediately if comparing a dir and a file
            if is_dir_1 and not is_dir_2:
                return -1 * direction
            if not is_dir_1 and is_dir_2:
                return 1 * direction

        if name1 < name2:
            return -1
        if name1 == name2:
            return 0
        return 1

    def format_f_size(self, size):
        """
        convert filesize to string with appropriate units
        This includes generating a units suffix thats returned with the formatted size as a tuple.
        """
        units = 'b'
        length = len(f"{size:.0f}")
        if length <= 3:
            val = str(size)
        elif length <= 6:
            val = f"{size / 10e+2:.1f}"
            units = 'kb'
        elif length <= 9:
            val = f"{size / 10e+5:.1f}"
            units = 'mb'
        elif length <= 12:
            val = f"{size / 10e+8:.1f}"
            units = 'gb'
        else:
            val = f"{size / 10e+11:.1f}"
            units = 'tb'
        return (val, units)

    def append_to_path_back(self):
        """track file change history"""
        if len(self.path_back) >= self.path_back_max_len:
            self.path_back.pop(0)
        self.path_back.append(self.current_path)

    def append_to_path_ahead(self):
        """track file change history"""
        if len(self.path_ahead) >= self.path_ahead_max_len:
            self.path_ahead.pop(0)
        self.path_ahead.append(self.current_path)


    def get_path_current(self):
        """get the current path"""
        return self.current_path

    def cd(self, path):
        """move to a new working directory determined by path"""
        if os.path.isdir(path):
            self.append_to_path_back()
            self.path_ahead.clear()
            self.current_path = path
            self.__update_file_list()

    def cd_ahead(self):
        """move forward to directory in the file change history"""
        if len(self.path_ahead) > 0:
            path = self.path_ahead.pop()
            if os.path.isdir(path):
                self.append_to_path_back()
                self.current_path = path
                self.__update_file_list()
            else:
                self.path_ahead.append(path)

    def cd_up(self, path):
        """move up one level in the directory tree"""
        if os.path.isdir(path):
            self.append_to_path_back()
            self.cd(os.path.split(self.get_path_current())[0])
            self.__update_file_list()

    def cd_previous(self):
        """move back to directory in the file change history"""
        if len(self.path_back) > 0:
            path = self.path_back.pop()
            if os.path.isdir(path):
                self.append_to_path_ahead()
                self.current_path = path
                self.__update_file_list()
            else:
                self.path_back.append(path)

    def is_hidden_file(self, file_name):
        """determine if a file is a hidden file"""
        valid = re.compile(r"^[\.]")
        if valid.match(file_name):
            return True
        return False


class Files_View:
    """Display file infrmation for files in the cwd"""

    def __init__(self, files_view, files, config):
        self.files_view = files_view
        self.files = files

        self.config = config

        self.config_section_name = 'FilesView'

        # set up the data model and containers
        self.files_ls = self.files.get_file_list()
        self.files_ls.set_sort_func(1, self.files.cmp_f_list_dir_fst, None)
        self.files_view.set_model(self.files_ls)

        # name column
        name_r_icon = Gtk.CellRendererPixbuf()
        name_r_text = Gtk.CellRendererText()
        self.name_col = Gtk.TreeViewColumn("Name")
        self.name_col.pack_start(name_r_icon, False)
        self.name_col.pack_start(name_r_text, True)
        self.name_col.add_attribute(name_r_icon, "pixbuf", 0)
        self.name_col.add_attribute(name_r_text, "text", 1)
        self.name_col.set_sort_column_id(1)
        self.name_col.set_resizable(True)
        # reset column width to previous size
        name_width = int(self.config[self.config_section_name]['column_width_name'])
        self.name_col.set_fixed_width(name_width)
        self.files_view.append_column(self.name_col)

        # size column
        size_r_val = Gtk.CellRendererText()
        size_r_units = Gtk.CellRendererText()
        size_col = Gtk.TreeViewColumn("Size")
        size_col.pack_start(size_r_val, False)
        size_col.pack_start(size_r_units, False)
        size_col.add_attribute(size_r_val, "text", 3)
        size_col.add_attribute(size_r_units, "text", 4)
        self.files_view.append_column(size_col)

        # file creation time column
        c_time_r = Gtk.CellRendererText()
        c_time_col = Gtk.TreeViewColumn("Modified")
        c_time_col.pack_start(c_time_r, True)
        c_time_col.add_attribute(c_time_r, "text", 5)
        self.files_view.append_column(c_time_col)

        #signals
        self.files_view.connect('row-activated', self.row_activated)
        self.files_view.connect('button-release-event', self.on_button_release )

    def on_button_release(self, unused_button, event):
        """
        handle mouse button release events.
        Currently:
        column resising
        forward and back buttons to move ahead or back in the file change history.
        """
        if event.get_button()[0] is True:
            if event.get_button()[1] == 1:
                self.on_col_width_change()
                #print('left button clicked')
            elif event.get_button()[1] == 2:
                pass
                #print('middle button clicked')
            elif event.get_button()[1] == 3:
                pass
                #print('right button clicked')
            elif event.get_button()[1] == 8:
                self.files.cd_previous()
                #print('back button clicked')
            elif event.get_button()[1] == 9:
                self.files.cd_ahead()
                #print('forward button clicked')

    def on_col_width_change(self):
        """save new column width to config parser, creating a new section name if it doesn't exist'"""
        name_width_config = int(self.config[self.config_section_name]['column_width_name'])
        name_width = self.name_col.get_width()
        if name_width_config != name_width:
            self.config.set(self.config_section_name, 'column_width_name', str(name_width))

    def row_activated(self, treeview, path, unused_column):
        """
        a file was cicked in the view.
        if file is a directory then change to that directory
        """
        model = treeview.get_model()
        tree_iter = model.get_iter(path)
        value = model.get_value(tree_iter,1)
        is_dir = model.get_value(tree_iter,2)
        if is_dir:
            # cd into selected dir
            new_path = os.path.join(self.files.get_path_current(), value)
            self.files.cd(new_path)

class MainWindow(Gtk.Window):
    """The main display window"""

    def __init__(self, book_reader_window, window_pane, config, builder):
        self.config = config
        self.book_reader_window = book_reader_window
        self.window_pane = window_pane

        # visibility buttons
        self.show_files_switch1 = builder.get_object("show_files_switch1")
        self.show_files_switch1.connect('state-set', self.on_visibility_switch_changed)
        self.show_files_switch1_state = self.config['book_reader_window'].getboolean('show_files_switch1_state')
        self.file_manager1 = builder.get_object("file_manager1")
        #
        self.show_files_switch2 = builder.get_object("show_files_switch2")
        self.show_files_switch2.connect('state-set', self.on_visibility_switch_changed)
        self.show_files_switch2_state = self.config['book_reader_window'].getboolean('show_files_switch2_state')
        self.file_manager2 = builder.get_object("file_manager2")
        #
        self.show_playlist_switch = builder.get_object("show_playlist_switch")
        self.show_playlist_switch.connect('state-set', self.on_visibility_switch_changed)
        self.show_playlist_switch_state = self.config['book_reader_window'].getboolean('show_playlist_switch_state')
        self.book_reader_view = builder.get_object("book_reader_view")
        #
        self.image_view = builder.get_object("image_view")
        self.show_image_switch = builder.get_object("show_image_switch")
        self.show_image_switch.connect('state-set', self.on_visibility_switch_changed)
        self.show_image_switch_state = self.config['book_reader_window'].getboolean('show_image_switch_state')
        # file_manager_pane
        self.file_manager_pane = builder.get_object("file_manager_pane")
        self.file_manager_pane_pos = self.config['book_reader_window'].getint('file_manager_pane_pos')
        self.file_manager_pane.set_position(int(self.file_manager_pane_pos))
        # book_reader_pane
        self.book_reader_pane = builder.get_object("book_reader_pane")
        self.book_reader_pane_pos = self.config['book_reader_window'].getint('book_reader_pane_pos')
        self.book_reader_pane.set_position(int(self.book_reader_pane_pos))
        # window callbacks
        self.book_reader_window.connect('destroy', self.on_destroy)
        self.book_reader_window.connect('delete-event', self.on_delete_event, self.book_reader_window )
        # load previous window state
        width = self.config['book_reader_window'].getint('width')
        height = self.config['book_reader_window'].getint('height')
        self.book_reader_window.set_default_size(width, height)
        window_1_pane_pos = self.config['book_reader_window'].getint('window_1_pane_pos')
        self.window_pane.set_position(window_1_pane_pos)
        # launch
        self.book_reader_window.show_all()

        # set switch states
        # must be after the call to show all; these trigger interrupts that hide their views
        if self.show_files_switch1_state is not None:
            self.show_files_switch1.set_state(bool(self.show_files_switch1_state))
        if self.show_files_switch2_state is not None:
            self.show_files_switch2.set_state(bool(self.show_files_switch2_state))
        if self.show_playlist_switch_state is not None:
            self.show_playlist_switch.set_state(bool(self.show_playlist_switch_state))
        if self.show_image_switch_state is not None:
            self.show_image_switch.set_state(self.show_image_switch_state)


    def on_delete_event(self, unused_widget, unused_val, window=None):
        """
        The view has been closed.
        Save the view state to file
        """
        # save settings to config
        # window size
        window_1_pane_pos = self.window_pane.get_position()
        width, height = window.get_size()
        self.config.set('book_reader_window', 'window_1_pane_pos', str(window_1_pane_pos))
        self.config.set('book_reader_window', 'width', str(width))
        self.config.set('book_reader_window', 'height', str(height))
        # pane positions
        book_reader_pane_pos = self.book_reader_pane.get_position()
        file_manager_pane_pos = self.file_manager_pane.get_position()
        self.config.set('book_reader_window', 'book_reader_pane_pos', str(book_reader_pane_pos))
        self.config.set('book_reader_window', 'file_manager_pane_pos', str(file_manager_pane_pos))
        # button states
        show_image_switch_state = self.show_image_switch.get_state()
        self.config.set('book_reader_window', 'show_image_switch_state', str(show_image_switch_state))
        #
        show_files_switch2_state = self.show_files_switch2.get_state()
        self.config.set('book_reader_window', 'show_files_switch2_state', str(show_files_switch2_state))
        #
        show_files_switch1_state = self.show_files_switch1.get_state()
        self.config.set('book_reader_window', 'show_files_switch1_state', str(show_files_switch1_state))
        #
        show_playlist_switch_state = self.show_playlist_switch.get_state()
        self.config.set('book_reader_window', 'show_playlist_switch_state', str(show_playlist_switch_state))


    def on_destroy(self, unused_window):
        """exit the gui main loop"""
        Gtk.main_quit()

    def on_visibility_switch_changed(self, switch, state):
        """manage the actions associated with the upper battery of show view switches"""

        # lookup table mapping the switches to the function to call which further depends on the state of the switch
        # This function call either shows or hides the panel associated with the switch.
        switch_functions = {
            'show_image_switch'   :(lambda x:(x and self.image_view.show       or self.image_view.hide)),
            'show_playlist_switch':(lambda x:(x and self.book_reader_view.show or self.book_reader_view.hide)),
            'show_files_switch2'  :(lambda x:(x and self.file_manager2.show    or self.file_manager2.hide)),
            'show_files_switch1'  :(lambda x:(x and self.file_manager1.show    or self.file_manager1.hide))
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
        elif ((not self.file_manager1.get_visible() and not self.file_manager2.get_visible())
               and self.file_manager_pane.get_visible()):
            self.file_manager_pane.hide()
        elif ((self.file_manager1.get_visible() or self.file_manager2.get_visible())
               and not self.file_manager_pane.get_visible()):
            # show file manager pane
            self.file_manager_pane.show()


def main(unused_args):
    """entry point for book_ease"""
    #configuration file
    config_dir = Path.home() / '.config' / 'book_ease'
    config_dir.mkdir(mode=511, parents=True, exist_ok=True)
    config_file = config_dir / 'book_ease.ini'
    config = configparser.ConfigParser()
    config.read(config_file)
    # Load the gui from glade
    builder = Gtk.Builder()
    builder.add_from_file("book_ease.glade")
    # files backend
    files = Files_(config)
    # left side file viewer
    files_view_1 = Files_View(builder.get_object("files_1"), files, config)
    # left side bookmarks
    BookMark(builder.get_object("bookmarks_1"), files_view_1, files, config)
    # image pane
    Image_View(files, config, builder)

    # bookreader backend
    BookReader_(files, config, builder)

    # main window
    MainWindow(builder.get_object("window1"), builder.get_object("window_1_pane"), config, builder)

    Gtk.main()
    # write any changes to the config
    with open(config_file, 'w', encoding="utf-8") as configfile:
        config.write(configfile)

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
