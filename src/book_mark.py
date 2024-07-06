#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  book_mark.py
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
"""Book mark functionality for the file_mgr system"""

from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path
import os
import gi
gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
from gi.repository import Gtk, Gdk
from gi.repository.GdkPixbuf import Pixbuf
import book_ease_tables
import signal_
import glib_utils
if TYPE_CHECKING:
    import file_mgr


class RenameTvEntryDialog(Gtk.Dialog):
    """Dialog for renaming a bookmark"""

    def __init__(self, title: str="My Dialog") -> None:
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

    def add_filechooser_dialog(self, file_chooser_method=None) -> None:
        """Allow Bookmark to assign a file choser diaog for this dialog to use"""
        self.entry_2.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, 'folder')
        self.entry_2.connect('icon-press', self.on_file_chooser_icon_pressed, file_chooser_method)

    def on_file_chooser_icon_pressed(self, unused_1, unused_2, unused_3, file_chooser_method=None) -> None:
        """callback to start the filechooser dialof that was assigned to this class in add_filechooser_dialog"""
        name, path = file_chooser_method()
        if name and path:
            self.entry_2.set_text(path)


class BookMarkData:
    """DTO for bookmark data"""
    __slots__ = ['id_', 'name', 'target', 'index']

    def __init__(self, id_: int, name: str, target: str, index: int) -> None:
        self.id_ = id_
        self.name = name
        self.target = target
        self.index = index


class BookMarkDBI:
    """Adapter to help BookMark interface with the book_ease.db database"""

    def __init__(self, column_map: dict) -> None:
        self.column_map = column_map
        self.settings_string = book_ease_tables.SettingsString()
        self.book_marks_table = book_ease_tables.BookMarks()

    def get_bookmarks(self) -> tuple[BookMarkData]:
        """Get the list of saved bookmarks from the database."""
        with book_ease_tables.DB_CONNECTION_MANAGER.query() as con:
            book_mark_db_rows = self.book_marks_table.get_all_rows_sorted_by_index_asc(con)
        return tuple(BookMarkData(
            id_ = row[self.column_map['id']['title']],
            name = row[self.column_map['name']['title']],
            target = row[self.column_map['target']['title']],
            index = row[self.column_map['index']['title']]
        )for row in book_mark_db_rows)

    def set_book_marks(self, book_marks: tuple[BookMarkData]) -> None:
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

    def __init__(self,
                 bookmark_view: Gtk.TreeView,
                 file_mgr_: file_mgr.FileMgr) -> None:

        self.file_mgr = file_mgr_
        self.book_mark_dbi = BookMarkDBI(self.column_map)

        self.bookmark_model = Gtk.ListStore(Pixbuf, int, str, str)
        # To get the updated values after using drag and drop to reorder
        # the treeview, the 'row-deleted' signal must be used. It is necessary
        # to set a _drag_drop flag in self.bookmark_view's 'drag-drop' callback to distinguish
        # the drag-drop from other types of delete events.
        self.bookmark_model.connect('row-deleted', self.on_row_deleted)
        self._drag_drop: bool=False

        signal_.GLOBAL_TRANSMITTER.connect('bookmark_list_changed', self.reload_bookmarks)

        self.bookmark_view = bookmark_view
        self.bookmark_view.connect('button-press-event', self.on_button_press)
        self.bookmark_view.connect('button-release-event', self.on_button_release)
        self.bookmark_view.connect('drag-drop', self.on_drag_drop)
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
        self.cmenu: Gtk.Menu  = Gtk.Menu.new()
        self.cmenu.connect('deactivate', self.cm_on_deactivate)

        self.cm_add_bm: Gtk.MenuItem = Gtk.MenuItem.new_with_label('add bookmark')
        self.cm_add_bm.connect('button-release-event', self.cm_on_item_button_release, 'add bookmark')
        self.cmenu.append(self.cm_add_bm)

        self.cm_remove_bm: Gtk.MenuItem = Gtk.MenuItem.new_with_label('remove bookmark')
        self.cm_remove_bm.connect('button-release-event', self.cm_on_item_button_release, 'remove bookmark')
        self.cmenu.append(self.cm_remove_bm)

        self.cm_rename_bm: Gtk.MenuItem = Gtk.MenuItem.new_with_label('rename bookmark')
        self.cm_rename_bm.connect('button-release-event', self.cm_on_item_button_release, 'rename bookmark')
        self.cmenu.append(self.cm_rename_bm)

        self.cmenu.show_all()

    def remove_selected_bookmark(self) -> None:
        """delete the selected bookmark and remove it from the view"""
        sel = self.bookmark_view.get_selection()
        model, paths = sel.get_selected_rows()
        sel.unselect_all()
        # reversed so the itr isn't corrupted on multiselect
        for pth in reversed(paths):
            itr = model.get_iter(pth)
            model.remove(itr)
        self.update_bookmark_config()
        signal_.GLOBAL_TRANSMITTER.send('bookmark_list_changed', sender=self)

    def rename_selected_bookmark(self) -> None:
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
                signal_.GLOBAL_TRANSMITTER.send('bookmark_list_changed', sender=self)
            dialog.destroy()

    def select_dir_dialog(self) -> tuple[str, str] | tuple[None, None]:
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
        dialog.set_current_folder(str(self.file_mgr.get_cwd()))
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            target = dialog.get_filename()
            name = os.path.basename(target)
        dialog.destroy()
        return  name, target

    def add_bookmark(self, name: str, path: str) -> None:
        """
        add bookmark, defined by name and path, by adding it
        to the bookmark model and saving it to file
        """
        # Save to database immediately so that the id is pushed into the bookmarks model
        if name is not None and path is not None:
            index = len(self.bookmark_model)
            new_id = self.book_mark_dbi.append_book_mark(name=name, target=path, index=index)
            icon = Gtk.IconTheme.get_default().load_icon('folder', 24, 0)
            self.bookmark_model.append([icon, new_id, name, path])
            signal_.GLOBAL_TRANSMITTER.send('bookmark_list_changed', sender=self)

    def cm_on_deactivate(self, __) -> None:
        """
        callback to cleanup after a context menu is closed
        unselects any entries in the view that were being acted upon by the context menu
        """
        sel = self.bookmark_view.get_selection()
        sel.unselect_all()

    def cm_on_item_button_release(self,
                                  _: Gtk.MenuItem,
                                  event: Gdk.EventButton,
                                  user_data: any=None) -> None:
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

    def on_button_release(self, _: Gtk.TreeView, event: Gdk.EventButton) -> None:
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
                    self.file_mgr.cd(Path(value))

    def on_button_press(self, _: Gtk.TreeView, event: Gdk.EventButton) -> None:
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

    def on_row_deleted(self, _: Gtk.ListStore, __: any=None) -> None:
        """callback for treestore row deleted, catching the user drag icons to reorder"""
        if self._drag_drop:
            self._drag_drop = False
            self.update_bookmark_config()
            signal_.GLOBAL_TRANSMITTER.send('bookmark_list_changed')

    def update_bookmark_config(self) -> None:
        """clear and re-save all the bookmarks with current values"""
        cmap = BookMark.column_map
        data = tuple(BookMarkData(id_=row[cmap['id']['g_col']],
                                  name=row[cmap['name']['g_col']],
                                  target=row[cmap['target']['g_col']],
                                  index=i)
                     for i, row in enumerate(self.bookmark_model))

        self.book_mark_dbi.set_book_marks(data)

    def reload_bookmarks(self, sender: BookMark|None=None) -> None:
        """
        load saved bookmarks into the bookmark treeview

        When this is called via callback, a reference to the sender is used to
        exclude the sender from reloading its bookmarks, because the sender has already updated itself.

        If this method is called directly, the sender arg can be omitted.
        """
        if sender is not self or sender is None:
            bookmarks = self.book_mark_dbi.get_bookmarks()
            self.bookmark_model.clear()
            for row in bookmarks:
                if os.path.isdir(row.target):
                    icon = Gtk.IconTheme.get_default().load_icon('folder', 24, Gtk.IconLookupFlags.GENERIC_FALLBACK)
                    self.bookmark_model.append([icon, row.id_, row.name, row.target])

    def on_drag_drop(self, *_):  # Don't typehint this b/c there are a half dozen args for this callback.
        """Callback for using drag and drop to reorder the treeview rows."""
        self._drag_drop = True
