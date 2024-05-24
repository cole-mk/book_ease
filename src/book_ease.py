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
import re
import logging
import gi
gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
from gi.repository import Gtk, GdkPixbuf, Gdk
from gi.repository.GdkPixbuf import Pixbuf
import book_reader
import book_ease_tables
import player
import file_mgr
from gui.gtk import file_mgr_view

logging_stream_handler = logging.StreamHandler()
logging_stream_handler.setFormatter(logging.Formatter('%(levelname)s - %(name)s - %(message)s'))
logging.getLogger('signal_').addHandler(logging_stream_handler)

logging.getLogger().setLevel(logging.WARNING)

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


class BookMarkData:
    """DTO for bookmark data"""
    __slots__ = ['id_', 'name', 'target', 'index']

    def __init__(self, id_, name, target, index):
        self.id_ = id_
        self.name = name
        self.target = target
        self.index = index


class BookMarkDBI:
    """Adapter to help BookMark interface with the book_ease.db database"""

    def __init__(self, column_map):
        self.column_map = column_map
        self.settings_string = book_ease_tables.SettingsString()
        self.book_marks_table = book_ease_tables.BookMarks()

    def get_bookmarks(self) -> tuple[BookMarkData]:
        """Get the list of saved bookmarks from the database."""
        with book_ease_tables.DB_CONNECTION_MANAGER.query() as con:
            book_mark_db_rows = self.book_marks_table.get_all_rows_sorted_by_index_asc(con)
        return tuple(BookMarkData(
            id_=row[self.column_map['id']['title']],
            name=row[self.column_map['name']['title']],
            target=row[self.column_map['target']['title']],
            index=row[self.column_map['index']['title']]
        )for row in book_mark_db_rows)

    def set_book_marks(self, book_marks: tuple[BookMarkData]):
        """Save the bookmarks to the database"""
        with book_ease_tables.DB_CONNECTION_MANAGER.query() as con:
            id_set = set()
            for bm_data in book_marks:
                self.book_marks_table.update_row_by_id(con,
                                                       id_=bm_data.id_,
                                                       name=bm_data.name,
                                                       target=bm_data.target,
                                                       index=bm_data.index)
                id_set.add(bm_data.id_)
            self.book_marks_table.delete_rows_not_in_ids(con, tuple(id_set))

    def append_book_mark(self, name: str, target: str, index: int) -> int:
        """
        Append a bookmark entry to the 'book_mark' category in the settings_string database.
        Returns the rowid of the newly inserted row.
        """
        with book_ease_tables.DB_CONNECTION_MANAGER.query() as con:
            rowid = self.book_marks_table.set(con, name=name, target=target, index=index)
        return rowid


class BookMark:
    """Controller and View for Bookmark functionality inside the file view"""

    # map database columns to the bookmark g_model (ListStore) columns
    column_map = {
        'icon': {'g_col': 0},
        'id': {'g_col': 1, 'title': 'id_'},
        'name': {'g_col': 2, 'title': 'name'},
        'target': {'g_col': 3, 'title': 'target'},
        'index': {'title': 'index_'}
    }

    def __init__(self, bookmark_view, f_view, files):
        self.files = files
        self.book_mark_dbi = BookMarkDBI(self.column_map)
        self.f_view = f_view

        self.bookmark_model = Gtk.ListStore(Pixbuf, int, str, str)
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
        self.column.add_attribute(self.renderer_icon, "pixbuf", self.column_map['icon']['g_col'])
        self.column.add_attribute(self.renderer_text, "text", self.column_map['name']['g_col'])

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
            name = model.get_value(itr, self.column_map['name']['g_col'])
            target = model.get_value(itr, self.column_map['target']['g_col'])
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
                model.set_value(itr, self.column_map['name']['g_col'], name)
                model.set_value(itr, self.column_map['target']['g_col'], target)
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
        # This needs to be done so that the id is pushed into the bookmarks model
        if name is not None and path is not None:
            index = len(self.bookmark_model)
            new_id = self.book_mark_dbi.append_book_mark(name=name, target=path, index=index)
            icon = Gtk.IconTheme.get_default().load_icon('folder', 24, 0)
            self.bookmark_model.append([icon, new_id, name, path])


    def cm_on_deactivate(self, __):
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
                    value = model.get_value(tree_iter, self.column_map['target']['g_col'])
                    tvs.unselect_all()
                    self.files.cd(value)

    def on_button_press(self, unused_button, event):
        """
        handle callbacks for a button press on a bookmark by any mouse button.
        currently its only action is to call a context menu when the bookmark view is right clicked
        """
        print('on_button_press')
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
        """clear and re-save all the bookmarks with current values"""
        cmap = BookMark.column_map
        data = tuple(BookMarkData(id_=row[cmap['id']['g_col']],
                                  name=row[cmap['name']['g_col']],
                                  target=row[cmap['target']['g_col']],
                                  index=i)
                     for i, row in enumerate(self.bookmark_model))

        self.book_mark_dbi.set_book_marks(data)

    def reload_bookmarks(self):
        """
        load saved bookmarks into the bookmark treeview
        Note: this does not reload, it only appends
        """
        for row in self.book_mark_dbi.get_bookmarks():
            # if os.path.isdir(row[1]):

            if os.path.isdir(row.target):
                icon = Gtk.IconTheme.get_default().load_icon('folder', 24, Gtk.IconLookupFlags.GENERIC_FALLBACK)
                self.bookmark_model.append([icon, row.id_, row.name, row.target])


class Image_View:
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
        # TODO: setup locating the image files automatically
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

    def __init__(self, book_reader_window, window_pane, builder: Gtk.Builder):
        self.book_reader_window = book_reader_window
        self.window_pane = window_pane

        # visibility switches
        #
        # put the visibility switches in a set, so they can be iterated over when saving and retrieving values
        # from the database.
        self.visibility_switches = set()
        show_files_switch1: Gtk.Switch = builder.get_object("show_files_switch1")
        show_files_switch1.connect('state-set', self.on_visibility_switch_changed)
        self.visibility_switches.add(show_files_switch1)
        self.file_manager1: Gtk.Paned = builder.get_object("file_manager1")
        #
        show_files_switch2: Gtk.Switch = builder.get_object("show_files_switch2")
        show_files_switch2.connect('state-set', self.on_visibility_switch_changed)
        self.visibility_switches.add(show_files_switch2)
        self.file_manager2: Gtk.Paned = builder.get_object("file_manager2")
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
        self.file_manager_pane: Gtk.Paned = builder.get_object("file_manager_pane")
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


def main(unused_args):  # pylint: disable=unused-variable
    """entry point for book_ease"""
    builder = Gtk.Builder()
    builder.add_from_file("book_ease.glade")
    # files backend
    files = file_mgr.Files_()
    # left side file viewer
    files_view_1 = file_mgr_view.Files_View(builder.get_object("files_1"), files)
    # left side bookmarks
    book_mark_1 = BookMark(builder.get_object("bookmarks_1"), files_view_1, files)
    # image pane
    image_view_ref = Image_View(files, builder)

    # bookreader backend
    book_reader_ref = book_reader.BookReader(files, builder)

    player_c_ref = player.PlayerC(book_reader_ref, builder)

    # main window
    main_window_ref = MainWindow(builder.get_object("window1"), builder.get_object("window_1_pane"), builder)

    Gtk.main()
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
