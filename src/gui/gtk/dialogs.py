# -*- coding: utf-8 -*-
#
#  untitled.py
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
import gi
gi.require_version("Gtk", "3.0") # pylint: disable=wrong-import-position
from gi.repository import Gtk
import playlist
from gui.gtk import book_view_columns


class EditTrackDialog:
    """This dialog allows for the editing of one Track object (or one row in the playlist, Gtk.Liststore)"""
    # pylint: disable=too-many-instance-attributes
    # Eight is reasonable in this case.


    def __init__(self, col, track, playlist_row_id):
        self.selected_col = col
        self.track = track
        self.playlist_row_id = playlist_row_id

        builder = Gtk.Builder()
        builder.add_from_file("gui/gtk/BookViewDialogs.glade")
        self.dialog = builder.get_object("edit_row_dialog")

        # buttons
        add_button = builder.get_object("add_button")
        add_button.connect('clicked', self.on_button_clicked, 'add')

        remove_button = builder.get_object("remove_button")
        remove_button.connect('clicked', self.on_button_clicked, 'remove')

        ok_button = builder.get_object("ok_button")
        ok_button.connect('clicked', self.on_button_clicked, 'ok')

        up_button = builder.get_object("up_button")
        up_button.connect('clicked', self.on_button_clicked, 'up')

        down_button = builder.get_object("down_button")
        down_button.connect('clicked', self.on_button_clicked, 'down')

        # setup treeview with column and renderer.
        # The col_tv_model is used to display a list of metadata tied to a key selected in self.col_combo.
        self.col_tv_model = builder.get_object("col_value")
        col_tv_r = Gtk.CellRendererText()
        self.col_tv_c = Gtk.TreeViewColumn()
        self.col_tv_c.pack_start(col_tv_r, True)
        self.col_tv_c.add_attribute(col_tv_r, "text", 0)
        self.col_tv_c.set_clickable(False)
        #
        self.col_treeview = builder.get_object("col_treeview")
        self.col_treeview.append_column(self.col_tv_c)
        self.col_treeview.unset_rows_drag_dest()
        self.col_treeview.unset_rows_drag_source()
        self.col_treeview.set_reorderable(True)

        # entry widget for new user entries. Text entered here is meant to added to a Track's metadata.
        self.new_value_entry = builder.get_object("new_value_entry")

        # combo to let user select column to edit. The selections are metadata keys. eg title, author, length, etc
        col_combo = builder.get_object("col_combo")
        col_combo.set_entry_text_column(0)
        # add list of displayed columns to combo entries (metadata keys).
        for i, column in enumerate(book_view_columns.display_cols):
            col_combo.append_text(column['name'])
            # The selected column is the column in the main playlist that the user clicked to trigger this dialog.
            # Make the selected column the active column in the col_combo
            if column['g_col'] == self.selected_col['g_col']:
                col_combo.set_active(i)
        # Populate the col_tv_model (metadata entries) with metadata entries corresponding to the key in selected column
        self.col_tv_model_load(self.selected_col)
        # Watch col_combo for changes so that the col_tv_model can be updated with corresponding metadata.
        col_combo.connect("changed", self.on_combo_changed)

    def destroy(self):
        """Get rid of this dialog."""
        self.dialog.destroy()

    def run(self):
        """Tell the dialog to display itself."""
        return self.dialog.run()

    def col_tv_move_entry(self, direction='up'):
        """
        Move entry in col_tv_model either up or down, with the ability to wrap around to the beginning or end as needed.
        """
        sel = self.col_treeview.get_selection()
        model, paths = sel.get_selected_rows()
        sel.unselect_all()
        for path in paths:
            selected_itr = model.get_iter(path)
            target_iter = self.col_tv_get_move_destination(direction, selected_itr, model)
            model.swap(selected_itr, target_iter)
            sel.select_iter(selected_itr)

    def col_tv_get_move_destination(self,
                                    direction: str,
                                    current_iter: Gtk.TreeIter,
                                    model: Gtk.TreeModel) -> Gtk.TreeIter:
        """
        Get a Gtk.TreeIter that points to a move destination, either one row above or below current_iter.
        target_iter will be wrapped around to point to the beginning or end of the model when necessary.
        """
        if direction == 'up':
            target_iter = model.iter_previous(current_iter) or model.get_iter((len(model) - 1,))
        else:
            target_iter = model.iter_next(current_iter) or model.get_iter_first()
        return target_iter

    def col_tv_remove_entry(self):
        """remove entry from treeview"""
        sel = self.col_treeview.get_selection()
        model, paths = sel.get_selected_rows()
        sel.unselect_all()
        # reversed so the itr isn't corrupted on multiselect
        for path in reversed(paths):
            itr = model.get_iter(path)
            model.remove(itr)

    def on_button_clicked(self, widget, command):  # pylint: disable=unused-argument
        """One of the control buttons was clicked. call method associated with the clicked button"""
        if 'ok' == command:
            # update the Track because this dialog is closing, and the Track data is about to be consumed by the caller.
            self.update_track()
        elif 'add' == command:
            self.col_tv_add_entry(self.new_value_entry)
        elif 'remove' == command:
            self.col_tv_remove_entry()
        elif 'up' == command:
            self.col_tv_move_entry('up')
        elif 'down' == command:
            self.col_tv_move_entry('down')

    def col_tv_model_load(self, col: dict):
        """load metadata entries from self.track into the displayed treeview"""
        self.col_tv_model.clear()
        for md_entry in self.track.get_entries(col['key']):
            self.col_tv_model.append([md_entry.get_entry(), md_entry.get_id()])
        # set column title
        self.col_tv_c.set_title(col['name'])

    def set_selected_col(self, col_title: str) -> None:
        """Set self.selected_col to point to the column in book_view_columns.display_cols that matches title."""
        for col in book_view_columns.display_cols:
            if col['name'] == col_title:
                self.selected_col = col
                break

    def on_combo_changed(self, combo, data=None): #pylint: disable=unused-argument
        """The combo box containing the column titles has changed its selection.
        Update col_tv_model with the correct metadata entries.
        """
        # update the track, since the data in the treeview model is about to get wiped.
        self.update_track()
        # clear the entry widget
        self.new_value_entry.set_text('')
        # switch to the newly selected column
        column_title = combo.get_active_text()
        self.set_selected_col(column_title)
        self.col_tv_model_load(self.selected_col)

    def col_tv_add_entry(self, entry=None, user_data=None): #pylint: disable=unused-argument
        """Add user text to the treeview (strip whitespace), creating a new metadata entry."""
        text = entry.get_text().strip()
        entry.set_text('')
        if text:
            self.col_tv_model.append([text, None])

    def update_track(self):
        """
        Copy the contents of the self.col_tv_model to a list of TrackMDEntries.
        Move that list to Track.metadata with the correct key/val placement
        """
        entry_list = []
        # noinspection PyTypeChecker
        for i, row in enumerate(self.col_tv_model):
            md_entry = playlist.TrackMDEntry(entry=row[0], index=i, id_=row[1])
            entry_list.append(md_entry)
        self.track.set_entry(self.selected_col['key'], entry_list)
