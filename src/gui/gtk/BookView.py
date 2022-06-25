# -*- coding: utf-8 -*-
#
#  BookView.py
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
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
from pathlib import Path
import itertools
import playlist
import signal_
import book
from gui.gtk import book_view_columns
import pdb


class Edit_Row_Dialog:

    def __init__(self, row, g_col, book_view, model):
        self.row = row
        self.selected_col = None
        for i in book_view.display_cols:
            if i['name'] == g_col.get_title():
                self.selected_col = i
                break
        self.book_view = book_view
        self.track_edit_list_tmp = []
        self.model = model
        itr = self.model.get_iter(row)
        self.pl_track_id = self.model.get_value(itr, book_view_columns.pl_track_id['col'])

        builder = Gtk.Builder()
        builder.add_from_file("gui/gtk/BookViewDialogs.glade")
        self.dialog = builder.get_object("edit_row_dialog")

        # buttons
        self.add_button = builder.get_object("add_button")
        self.add_button.connect('clicked', self.on_button_clicked)
        #
        self.remove_button = builder.get_object("remove_button")
        self.remove_button.connect('clicked', self.on_button_clicked)
        #
        self.ok_button = builder.get_object("ok_button")
        #self.ok_button.connect('clicked', self.on_button_clicked)
        #
        self.cancel_button = builder.get_object("cancel_button")
        #self.cancel_button.connect('clicked', self.on_button_clicked)
        #
        self.up_button = builder.get_object("up_button")
        self.up_button.connect('clicked', self.on_button_clicked)
        #
        self.down_button = builder.get_object("down_button")
        self.down_button.connect('clicked', self.on_button_clicked)

        # setup  treeview with column and renderer
        self.col_tv_model = builder.get_object("col_value")
        self.col_tv_r = Gtk.CellRendererText()
        self.col_tv_c = Gtk.TreeViewColumn()
        self.col_tv_c.pack_start(self.col_tv_r, True)
        self.col_tv_c.add_attribute(self.col_tv_r, "text", 0)
        #self.col_tv_c.set_sort_column_id(0)
        self.col_tv_c.set_clickable(False)
        #
        self.col_treeview = builder.get_object("col_treeview")
        self.col_treeview.append_column(self.col_tv_c)
        self.col_treeview.unset_rows_drag_dest()
        self.col_treeview.unset_rows_drag_source()
        self.col_treeview.set_reorderable(True)

        # combo for new user entries
        self.new_value_combo = builder.get_object("new_value_combo")
        self.new_value_combo.set_entry_text_column(0)
        self.new_value_model = builder.get_object("new_value")
        self.new_value_entry = builder.get_object("new_value_entry")
        self.new_value_entry.connect('activate', self.col_tv_add_entry)

        # combo to let user select column to edit
        self.col_combo = builder.get_object("col_combo")
        self.col_combo.set_entry_text_column(0)
        self.col_combo.connect("changed", self.on_combo_changed)
        # add list of displayed columns to combo entries
        for i, c in enumerate(book_view.display_cols):
            self.col_combo.append_text(c['name'])
            #set selection
            if c['col'] == self.selected_col['col']:
                self.col_combo.set_active(i)
                self.set_active_column(c['name'])

        #response = self.dialog.show_all()

    def destroy(self):
        self.dialog.destroy()

    def run(self):
        return self.dialog.run()

    def col_tv_move_entry(self, _dir='up'):
        sel = self.col_treeview.get_selection()
        model, paths = sel.get_selected_rows()
        sel.unselect_all()
        if _dir == 'up':
            for p in paths:
                itr = model.get_iter(p)
                prev = p[0]-1
                if prev < 0:
                    return
                itr_prev = model.get_iter((prev,))
                itr_dest = model.insert_before(itr_prev)
                model.set_value(itr_dest,0,model.get_value(itr, 0))
                model.remove(itr)
                sel.select_iter(itr_dest)
        else:
            for p in paths:
                itr = model.get_iter(p)
                nxt = p[0]+1
                print('len(model)', len(model))
                if nxt >= len(model):
                    return
                itr_nxt = model.get_iter((nxt,))
                itr_dest = model.insert_after(itr_nxt)
                model.set_value(itr_dest,0,model.get_value(itr, 0))
                model.remove(itr)
                sel.select_iter(itr_dest)
        # update the temp list
        self.track_edit_list_tmp_update()


    def track_edit_list_tmp_update(self):
        # build tmp list of TrackMDEntry from col_tv_model data
        val_list = []
        for i, row in enumerate(self.col_tv_model):
            val_list.append(playlist.TrackMDEntry(id_=row[1], index=i, entry=row[0]))
        if len(val_list) > 0:
            # get existing entry or create now one and
            # add it to the track_edit_list_tmp
            existing_edit = False
            for edt in self.track_edit_list_tmp:
                if self.pl_track_id in edt.get_pl_track_id():
                    edit = edt
                    existing_edit = True
                    break

            if not existing_edit:
                edit = playlist.TrackEdit(self.selected_col)
                self.track_edit_list_tmp.append(edit)

            edit.set_entry(edit.col_info['key'], val_list)
            edit.set_pl_track_id(pl_track_id)

    def col_tv_remove_entry(self):
        sel = self.col_treeview.get_selection()
        model, paths = sel.get_selected_rows()
        sel.unselect_all()

        # remove entry from treeview
        # reversed so the itr isn't corrupted on multiselect
        for p in reversed(paths):
            itr = model.get_iter(p)
            model.remove(itr)

        # update the temp list
        self.track_edit_list_tmp_update()

    def on_button_clicked(self, widget, user_data=None):

        if self.ok_button == widget:
            # we aint updating shit except the tmp list from inside the dialog
            #self.book_view.pending_entry_list_update(self.track_edit_list_tmp)
            self.dialog.destroy()

        elif self.cancel_button == widget:
            print('cancel')

        elif self.add_button == widget:
            self.col_tv_add_entry(self.new_value_entry)

        elif self.remove_button == widget:
            self.col_tv_remove_entry()

        elif self.up_button == widget:
            self.col_tv_move_entry('up')

        elif self.down_button == widget:
            self.col_tv_move_entry('down')

    def set_active_column(self, col_name):
        # load new_value combo with suggestions
        self.new_value_model.clear()
        track = self.book_view.book.get_track(self.pl_track_id)
        new_values = track.get_entries(self.selected_col['key'])
        for i in track.get_entry_lists_new(self.selected_col['alt_keys']):
            # un-include duplicate values
            if not i.get_entry() in [v.get_entry() for v in new_values]:
                new_values.append(i)
        for i in new_values:
            self.new_value_model.append([i.get_entry(), i.get_id()])

        # load treeview with entries
        self.col_tv_model.clear()
        itr = self.model.get_iter(self.row)
        row_id = self.model.get_value(itr, book_view_columns.pl_track_id['col'])
        # look for unsaved changes from this dialog first
        unsaved_changes = False
        for i in self.track_edit_list_tmp:
            if i.col_info == self.selected_col:
                unsaved_changes = True
                for x in i.get_entries(self.selected_col['key']):
                    self.col_tv_model.append([x.get_entry(), x.get_id()])
                break
        # load saved entries from book track
        if not unsaved_changes:
            track = self.book_view.book.get_track(row_id)
            for i in track.get_entries(self.selected_col['key']):
                self.col_tv_model.append([i.get_entry(), i.get_id()])
        # set column title
        self.col_tv_c.set_title(col_name)

    def set_selected_col(self,col_title):
        for i in self.book_view.display_cols:
            if i['name'] == col_title:
                self.selected_col = i
                break


    def on_combo_changed(self, combo, Data=None):
        if combo == self.col_combo:
            #user has selected a column to edit
            txt = combo.get_active_text()
            self.set_selected_col(txt)
            self.set_active_column(txt)


    def col_tv_add_entry(self, entry=None, user_data=None):
        # add user text to the treeview (strip whitespace)
        text = entry.get_text().strip()
        entry.set_text('')
        if text:
            itr = self.col_tv_model.append()
            self.col_tv_model.set_value(itr,0,text)
            # update the temp list
            self.track_edit_list_tmp_update()

    def on_button_released(self, widget, event, data=None):
        print('dialog.on_button_released, widget, event, data', widget, event, data)
        if event.get_button()[0] is True:
            if widget == self.add_button:
                if event.get_button()[1] == 1:
                    print('add_button L clicked')
            if widget == self.remove_button:
                if event.get_button()[1] == 1:
                    print('remove_button L clicked')


class Book_View(Gtk.Box):
    """
    this class displays the book playlist
    """

    def __init__(self, book_, book_reader):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.signal = signal_.Signal()
        self.signal.add_signal('pinned_state_changed')
        self.book = book_
        self.notebook = self.book.book_reader.book_reader_view.book_reader_notebook
        self.book_reader = book_reader
        self.editing = None
        # the liststore for the main treeview
        self.playlist = self.get_playlist_new()

        self.playlist_tree_view = Gtk.TreeView()
        self.playlist_tree_view.set_model(self.playlist)
        self.playlist_tree_view.set_reorderable(True)
        self.playlist_tv_bp_signal = None
        self.playlist_tv_br_signal = None
        # enable editing of combo boxes in the treeview
        self.playlist_tv_bp_signal = self.playlist_tree_view.connect('button-press-event', self.on_button_pressed)
        self.playlist_tv_br_signal = self.playlist_tree_view.connect('button-release-event', self.on_button_release)

        self.scrolled_playlist_view = Gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
        self.scrolled_playlist_view.add(self.playlist_tree_view)


        #header
        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        # The container that will hold the pinned playlist check button
        self.pinned_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.pinned_button = False
        self.header_box.pack_start(self.pinned_button_box, expand=False, fill=False, padding=0)
        self.title_label = Gtk.Label(label=self.book.playlist_data.get_title())
        self.title_label.set_no_show_all(True)
        self.title_label.set_halign(Gtk.Align.END)
        self.header_box.pack_start(self.title_label, expand=True, fill=True, padding=0)
        title_store = Gtk.ListStore(book_view_columns.md_title['g_typ'])
        self.title_combo = Gtk.ComboBox.new_with_model_and_entry(title_store)
        self.title_combo.set_halign(Gtk.Align.END)
        self.title_combo.set_no_show_all(True)
        self.title_combo.set_entry_text_column(0)
        self.header_box.pack_start(self.title_combo, expand=True, fill=True, padding=0)

        # editing controls
        self.edit_playlist_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.edit_playlist_box.set_no_show_all(True)
        self.edit_playlist_box.show()
        #
        self.save_button = Gtk.Button.new_from_icon_name("document-save-symbolic", Gtk.IconSize.BUTTON)
        self.save_button.set_label('Save')
        self.save_button.connect('clicked', self.on_clicked)
        self.edit_playlist_box.pack_end(self.save_button, expand=False, fill=False, padding=4)
        #
        self.cancel_button = Gtk.Button.new_from_icon_name("window-close-symbolic", Gtk.IconSize.BUTTON)
        self.cancel_button.set_label('Cancel')
        self.cancel_button.connect('clicked', self.on_clicked)
        self.edit_playlist_box.pack_end(self.cancel_button, expand=False, fill=False, padding=4)
        #
        self.edit_button = Gtk.Button.new_from_icon_name("document-properties-symbolic", Gtk.IconSize.BUTTON)
        self.edit_button.set_label('Edit')
        self.edit_button.connect('clicked', self.on_clicked)
        self.edit_playlist_box.pack_end(self.edit_button, expand=False, fill=False, padding=4)
        #
        self.header_box.pack_start(self.edit_playlist_box, expand=True, fill=True, padding=0)


        self.display_cols = [book_view_columns.md_track_number,
                             book_view_columns.md_title,
                             book_view_columns.md_author,
                             book_view_columns.md_read_by,
                             book_view_columns.md_length,
                             book_view_columns.track_file]

        self.col_to_renderer_map = {}
        for i in self.display_cols:
            rend = Gtk.CellRendererCombo()
            rend.set_property("text-column",0 ) #0 i['col']
            rend.set_property("editable", True)
            rend.set_property("has-entry", False)
            # col 0 is playlist.TrackMDEntry.entry(type depends on column);
            # col 1 is playlist.TrackMDEntry.id_ (int for all columns)
            rend.set_property("model", Gtk.ListStore(i['g_typ'], int))
            col = Gtk.TreeViewColumn(i['name'])
            col.pack_start(rend, True)
            col.add_attribute(rend, "text", i['col'])
            col.set_sort_order(Gtk.SortType.DESCENDING)
            col.set_clickable(True)
            col.connect("clicked", self.on_clicked, i['col'])
            self.playlist_tree_view.append_column(col)
            self.col_to_renderer_map[col] = rend
            rend.connect("edited", self.on_edited, i)
            rend.connect("editing-started", self.on_editing_started, i)
            rend.connect("editing-canceled", self.on_editing_cancelled)

        # default sort column tuple (tv_col, model_index)
        self.default_sort_col =  (self.playlist_tree_view.get_column(self.display_cols.index(book.md_track_number)),
                                  book.md_track_number['col'])
        self.default_sort_col[0].set_sort_order(Gtk.SortType.DESCENDING)
        self.old_sort_order = Gtk.SortType.DESCENDING

    def close(self):
        # closes the notebook page b/c this view is the page
        self.destroy()

    def get_playlist(self):
        return self.playlist

    def get_playlist_new(self):
        return Gtk.ListStore(book_view_columns.md_title      ['g_typ'],
                             book_view_columns.md_author     ['g_typ'],
                             book_view_columns.md_read_by    ['g_typ'],
                             book_view_columns.md_length     ['g_typ'],
                             book_view_columns.md_track_number      ['g_typ'],
                             book_view_columns.track_file       ['g_typ'],
                             book_view_columns.pl_track_id   ['g_typ'],
                             book_view_columns.pl_path       ['g_typ'])

    def on_editing_cancelled(self, renderer):
        m = renderer.get_property('model')
        m.clear()

    def on_editing_started(self, renderer, editable, path, col):
        # build the dropdown menu with suggestions
        m = editable.get_model()
        m.clear()
        itr = self.playlist.get_iter(path)
        pl_track_id = self.playlist.get_value(itr, book_view_columns.pl_track_id['col'])
        # append track entries to combo model
        track = self.book.get_track(pl_track_id)
        for entry in track.get_entries(col['key']):
            m.append([entry.get_entry(), entry.get_id()])

    def on_edited(self, renderer, path, text, col):
        # propagate changes to self.playlist and end editing
        self.playlist[path][col['col']] = text
        model = renderer.get_property('model')
        if self.editing == True :
            val_list = []
            # build a partial TrackMDEntry from selected text
            # and add it to the beginning of the val_list
            val_list.append(playlist.TrackMDEntry(index=0, entry=text))
            # move selected TrackMDEntry to front of list, skip once selected text in list, but do add duplicates
            matched = False
            for i, row in enumerate(model):
                if matched == False and row[0] == text:
                    matched = True
                    # complete the selected TrackMDEntry by setting id_
                    val_list[0].set_id(row[1])
                    continue
                # append fully instantiated TrackMDEntry to val_list
                val_list.append(playlist.TrackMDEntry(id_=row[1], index=len(val_list), entry=row[0]))
            # send the changes to book
            if len(val_list) > 0:
                row_id = self.playlist[path][book_view_columns.pl_track_id['col']]
                edit = playlist.TrackEdit(col)
                edit.set_entry(col['key'], val_list)
                edit.set_pl_track_id(row_id)
                self.book.track_list_update(edit)
        model.clear()

    def on_button_release(self, widget, event, data=None):
        if event.get_button()[0] is True:
            if widget == self.playlist_tree_view:
                if event.get_button()[1] == 1:
                    if self.editing:
                        self.title_combo_fill()
                if event.get_button()[1] == 3:
                    if self.editing == True:
                        # run editing dialog on pressed column and first selected row
                        pth, col, cel_x, cel_y = self.playlist_tree_view.get_path_at_pos(event.x,  event.y)
                        dialog = Edit_Row_Dialog(pth, col, self, self.playlist)
                        response = dialog.run()
                        if response == Gtk.ResponseType.OK:
                            # load the changes from the dialog into the books edit list
                            for edit in dialog.track_edit_list_tmp:
                                self.book.track_list_update(edit)
                                # set value in tree view to pirmary entry
                                for j, row in enumerate(self.playlist):
                                    if edit.get_pl_track_id() == row[book_view_columns.pl_track_id['col']]:
                                        itr = self.playlist.get_iter((j,))
                                        val = edit.get_entries(edit.col_info['key'])[0].get_entry()
                                        self.playlist.set_value(itr, edit.col_info['col'], val)
                                        break

                            print('response', response)
                        dialog.destroy()

    def on_button_pressed(self, btn, event, data=None):
        if event.get_button()[0] is True:
            if btn == self.playlist_tree_view:
                if event.get_button()[1] == 1:
                    if event.type == Gdk.EventType._2BUTTON_PRESS:
                        # edit cell on double press
                        pth, col, cel_x, cel_y = self.playlist_tree_view.get_path_at_pos(event.x,  event.y)
                        rend = self.col_to_renderer_map[col]
                        #rend.set_property("editable", True)
                        self.playlist_tree_view.set_cursor(pth,col,start_editing=True)
                if event.get_button()[1] == 3:
                    # right button
                    pass
        if btn == self.title_combo:
            if event.get_button()[1] == 1:
                self.title_combo_fill()

    def cmp_str_as_num(self, model, row1, row2, user_data=None):
        sort_column, sort_order = model.get_sort_column_id()
        # all strings that are not proper numbers are evaluated equal
        try:
            num1 = int(model.get_value(row1, 4))
        except Exception as e:
            num1 = -1
        try:
            num2 = int(model.get_value(row2, 4))
        except Exception as e:
            num2 = -1

        if num1 < num2:
            return -1
        elif num1 == num2:
            return 0
        else:
            return 1

    def sort_by_column(self, tvc, model_index):
        # toggle sort order
        old_sort_order = tvc.get_sort_order()
        new_sort_order = Gtk.SortType.DESCENDING
        if old_sort_order == Gtk.SortType.DESCENDING:
            new_sort_order = Gtk.SortType.ASCENDING
        self.old_sort_order = new_sort_order
        tvc.set_sort_order(new_sort_order)
        # show sorted column that cant be reordered
        sorted_model = Gtk.TreeModelSort(model=self.playlist)
        sorted_model.set_sort_column_id(model_index, new_sort_order)
        # custom compare functon for the track number column
        sorted_model.set_sort_func(book.md_track_number['col'], self.cmp_str_as_num, None)

        self.playlist_tree_view.set_model(sorted_model)
        # copy sorted sort model to new regular liststore model
        new_model = self.get_playlist_new()
        for i in sorted_model:
            new_row = new_model.append(tuple(i))
        # set up self with the new model
        self.playlist_tree_view.set_model(new_model)
        self.playlist = new_model
        self.book.playlist = new_model
        self.playlist.connect("row_deleted", self.on_row_deleted)
        tvc.set_sort_indicator(True)

    def playlist_backup(self):
        # copy the current liststore
        self.playlist_old.clear()
        for i in self.playlist:
            self.playlist_old.append(tuple(i))

    def playlist_save(self):
        """
        playlist_save is part of the callback chain when the save button
        is pressed.
        populate track data objects with the tracks stored in the edited playlist
        """
        # add row numbers to track  list
        for number, row in enumerate(self.playlist):
            track = playlist.Track()
            track.set_number(number)
            track.set_pl_track_id(row[book_view_columns.pl_track_id['col']])
            self.book.track_list_update(track)

        # apply pending changes
        old_t = self.book.playlist_data.get_title()
        old_p = self.book.playlist_data.get_path()
        # new book title
        entry = self.title_combo.get_child()
        title = entry.get_text()
        self.title_label.set_text(title)
        self.book_reader.on_playlist_save(self.book.get_index(), title)

    def enable_sorting(self, enable=True):
        if enable:
            for i in self.playlist_tree_view.get_columns():
                i.set_clickable(True)
        else:
            for i in self.playlist_tree_view.get_columns():
                i.set_clickable(False)
                if i.get_sort_indicator() == True:
                    i.set_sort_indicator(False)

    def enable_entry(self):
        print('enable_entry')

    def title_combo_show(self):
        cb = self.title_combo
        title_store = cb.get_model()
        entry = cb.get_child()
        entry.set_text(self.title_label.get_text())
        entry.set_width_chars(len(self.title_label.get_text()))
        self.title_combo_fill()
        cb.show()

    def title_combo_hide(self):
        cb = self.title_combo
        title_store = cb.get_model()
        title_store.clear()
        cb.hide()

    def book_data_load_th(self, **kwargs):
        GLib.idle_add(self.book_data_load, priority=GLib.PRIORITY_DEFAULT)

    def has_pinned_button(self):
        """
        determine if BookView has already had a PinnedButtonV
        object added to itself
        """
        return self.pinned_button

    def book_data_load(self):
        self.playlist.clear()
        playlist = self.book.get_track_list()
        self.title_label.set_label(self.book.playlist_data.get_title())
        if playlist:
            if len(playlist) > 0:
                # do the appending
                for track in playlist:
                    cur_row = self.playlist.append()
                    # append entries for each in list of displayed columns
                    for col in self.display_cols:
                        # get first primary entry
                        id_ = track.get_pl_track_id()
                        val = self.book.get_track(id_).get_entries(col['key'])
                        if val:
                            self.playlist.set_value(cur_row, col['col'], val[0].get_entry())

                    # the utility collumns always have a primary entry
                    self.playlist.set_value(cur_row, book_view_columns.pl_track_id['col'],
                                   track.get_pl_track_id())

                    self.playlist.set_value(cur_row, book.pl_path['col'],
                                   track.get_entries('path')[0].get_entry())

    def playlist_set_edit(self, edit):
        # enter/exit editing mode
        if edit == True and (self.editing == False or self.editing == None):
            # tun on the edit functions in the gui
            self.edit_button.hide()
            self.save_button.show()
            self.cancel_button.show()
            self.title_label.hide()
            self.title_combo_show()
            self.enable_sorting(True)
            self.editing = True
            # enable editing of combo boxes in the treeview
            #self.playlist_tv_bp_signal = self.playlist_tree_view.connect('button-press-event', self.on_button_pressed)
            #self.playlist_tv_br_signal = self.playlist_tree_view.connect('button-release-event', self.on_button_release)
            for i in self.col_to_renderer_map:
                self.col_to_renderer_map[i].set_property("has-entry", True)

        elif edit == False and (self.editing == True or self.editing == None):
            # return the gui to static state
            self.save_button.hide()
            self.cancel_button.hide()
            self.edit_button.show()
            self.title_combo_hide()
            self.enable_sorting(False)
            self.editing = False
            self.title_label.show()
            # stop editing of combo boxes in the treeview
            #self.playlist_tree_view.disconnect(self.playlist_tv_bp_signal)
            #self.playlist_tree_view.disconnect(self.playlist_tv_br_signal)
            for i in self.col_to_renderer_map:
                #self.col_to_renderer_map[i].set_property("editable", False)
                self.col_to_renderer_map[i].set_property("has-entry", False)

        # get title suggestions from selected row in conjunction with
        # the book.tracklist. default to the first row if none are selected
        # it always gets row zero, row zero actual text, selected row, selected rows actual text
        # and then just filterws out duplicates.

    def title_combo_fill(self):
        cb = self.title_combo
        title_store = cb.get_model()
        title_store.clear()
        # row zero actual text
        paths = []
        tv_model = self.playlist_tree_view.get_model()

        # row zero actual text
        default_paths = [0]
        paths.append(*default_paths)

        sel = self.playlist_tree_view.get_selection()
        sel_model, sel_paths = sel.get_selected_rows()
        if sel_paths:
            paths.append(*sel_paths)
        else:
            print('not sel_paths')

        for p in paths:
            itr = tv_model.get_iter(p)
            # append the actual current value in the selected row or row zero of the treeview
            p_val = tv_model.get_value(itr, book_view_columns.md_title['col'])
            # make sure selected_val isnt a duplicate
            match = False
            for i in title_store:
                if i[0] == p_val:
                    match = True
                    break
            if not match:
                title_store.append([p_val])

            # append to title_store each val in metadata value list for each p
            pl_track_id = tv_model.get_value(itr, book_view_columns.pl_track_id['col'])
            for meta_val in self.book.get_track(pl_track_id).get_entries(book_view_columns.md_title['key']):
                match = False
                # make sure meta_val isnt a duplicate
                for i in title_store:
                    if i[0] == meta_val.get_entry():
                        match = True
                        break
                if not match:
                    title_store.append([meta_val.get_entry()])

    def on_clicked(self, widget, user_data=None):
        if type(widget) == Gtk.TreeViewColumn:
            # Gtk.TreeViewColumn header was clicked
            tvc = widget
            model_index = user_data
            self.sort_by_column(tvc, model_index)
        elif type(widget) == Gtk.Button:
            btn = widget
            if btn == self.save_button:
                self.playlist_set_edit(False)
                self.playlist_save()
            elif btn == self.cancel_button:
                self.playlist_set_edit(False)
                self.book_reader.book_editing_cancelled(self.book.get_index())
            elif btn == self.edit_button:
                self.playlist_set_edit(True)

    def on_row_deleted(self, a, b):
        cols = self.playlist_tree_view.get_columns()
        for i in cols:
            i.set_sort_indicator(False)

    def remove_all_children(self):
        widgits = self.get_children()
        for i in widgits:
            self.remove(i)

    def on_book_data_ready_th(self, **kwargs):
        if 'is_sorted' not in kwargs:
            raise Exception ('on_book_data_ready_th is_sorted not in kwargs')
        GLib.idle_add(self.on_book_data_ready, kwargs['is_sorted'], priority=GLib.PRIORITY_DEFAULT)

    def on_book_data_ready(self, is_sorted=False):
        self.book_data_load()
        if len(self.playlist) > 0:
            # load the new gui
            self.remove_all_children()
            self.pack_start(self.header_box, expand=False, fill=False, padding=0)
            self.pack_start(self.scrolled_playlist_view, expand=True, fill=True, padding=0)
            #set default sort order for the playlist
            if not is_sorted:
                self.sort_by_column(self.default_sort_col[0], self.default_sort_col[1])
            self.title_label.set_label(self.book.playlist_data.get_title())
            self.show_all()
            self.notebook.set_tab_label_text(self, self.book.playlist_data.get_title()[0:8])
            # show editing buttons
            #self.edit_playlist_box.set_no_show_all(False)
            self.playlist_set_edit(True)
            self.edit_playlist_box.show()
            #self.edit_playlist_box.set_no_show_all(True)
            #self.cancel_button.show()


class Book_V:
    """
    Book_V is a container for displaying the different
    components that comprise a book view
    """
    # The path to the gui builder file that the component book views are going to use to instantiate themselves
    glade_path = Path().cwd() / 'gui' / 'gtk' / 'book.glade'

    def __init__(self):
        # create the gtk.Builder object that the VC classes will use to manage their views
        self.book_view_builder = Gtk.Builder()
        self.book_view_builder.add_from_file(str(self.glade_path))
        # the topmost box in the glade file; add it to self
        self.book_v_box = self.book_view_builder.get_object('book_v_box')

        # the components of a book view
        self.pinned_v_box = self.book_view_builder.get_object('pinned_v_box')

    def close(self):
        self.book_v_box.destroy()
        self.pinned_v_box.destroy()

    def get_gui_builder(self):
        return self.book_view_builder

class Book_VC:
    """
    Book_VC is a controller for Book_V
    """
    def __init__(self, book_tx_signal):
        book_tx_signal.connect('close', self.close)
        self.book_v = Book_V()

    def update(self):
        pass

    def begin_edit_mode(self):
        pass

    def begin_display_mode(self):
        pass

    def get_view(self):
        return self.book_v.book_v_box

    def close(self):
        self.book_v.close()

    def get_gui_builder(self):
        return self.book_v.get_gui_builder()


class Title_V:

    def __init__(self, book_view_builder):
        # the topmost box in the glade file; add it to self
        self.title_view = book_view_builder.get_object('title_v_box')
        # The label used to display the title of the book
        self.title_label = book_view_builder.get_object('title_label')
        # The entry that allows the user to change the title of the book
        self.title_entry = book_view_builder.get_object('title_entry')


class Title_VC:

    def __init__(self, book_, book_tx_signal, component_transmitter, book_view_builder):
        # save a reference to the transmitter that this class uses to send messages back to Book_C
        self.transmitter = component_transmitter
        # subscribe to the signals relevant to this class
        book_tx_signal.connect('close', self.close)
        book_tx_signal.connect('begin_edit_mode', self.begin_edit_mode)
        book_tx_signal.connect('begin_display_mode', self.begin_display_mode)
        book_tx_signal.connect('update', self.update)
        book_tx_signal.connect('save_title', self.save)
        # save a reference to the book model so Title_VC can get data when it needs to
        self.book = book_
        # create the Gtk view
        self.title_v = Title_V(book_view_builder)

    def get_view(self):
        return self.title_v.title_view

    def update(self):
        """get title from book and load it into the view"""
        # get title from book
        book_title = self.book.get_playlist_data().get_title()
        # load existing title into entry widget
        self.title_v.title_entry.set_text(book_title)
        self.title_v.title_entry.set_max_width_chars(40)
        # load the title into the title label thats shown during display mode
        self.title_v.title_label.set_max_width_chars(40)
        self.title_v.title_label.set_label(book_title)

    def begin_edit_mode(self):
        self.title_v.title_entry.show()
        self.title_v.title_label.hide()

    def begin_display_mode(self):
        self.title_v.title_entry.hide()
        self.title_v.title_label.show()

    def close(self):
        pass

    def save(self):
        """get the playlist title from the title_v model and save it to the book."""
        self.book.get_playlist_data().set_title(self.title_v.title_entry.get_text())
        self.book.save_playlist_data()

class ControlBtn_V:

    def __init__(self, book_view_builder):
        self.save_button = book_view_builder.get_object('save_button')
        self.cancel_button = book_view_builder.get_object('cancel_button')
        self.edit_button = book_view_builder.get_object('edit_button')

    def get_save_button(self):
        return self.save_button

    def get_cancel_button(self):
        return self.cancel_button

    def get_edit_button(self):
        return self.edit_button


class ControlBtn_VC:

    def __init__(self, book_, book_tx_signal, component_transmitter, book_view_builder):
        # save a reference to the transmitter that this class uses to send messages bak to Book_C
        self.transmitter = component_transmitter
        # subscribe to the signals relevant to this class.
        book_tx_signal.connect('close', self.close)
        book_tx_signal.connect('begin_edit_mode', self.begin_edit_mode)
        book_tx_signal.connect('begin_display_mode', self.begin_display_mode)

        # save a reference to the book model so ControlBtn_VC can get data when it needs to.
        self.book = book_

        # instantiate the view
        self.control_btn_v = ControlBtn_V(book_view_builder)

        # connect to the control button signals
        self.control_btn_v.save_button.connect('button-release-event', self.on_control_button_released, 'save_button')
        self.control_btn_v.cancel_button.connect('button-release-event', self.on_control_button_released, 'cancel_button')
        self.control_btn_v.edit_button.connect('button-release-event', self.on_control_button_released, 'edit_button')

    def get_view(self):
        pass

    def update(self):
        pass

    def begin_edit_mode(self):
        self.control_btn_v.save_button.show()
        self.control_btn_v.cancel_button.show()
        self.control_btn_v.edit_button.hide()

    def begin_display_mode(self):
        self.control_btn_v.save_button.hide()
        self.control_btn_v.cancel_button.hide()
        self.control_btn_v.edit_button.show()

    def close(self):
        pass

    def on_control_button_released(self, button, event_button, control_signal):
        self.transmitter.send(control_signal)


class  Playlist_V:

    def __init__(self, display_columns, book_view_builder):
        # display the playlist in a gtk treeview
        self.playlist_view = book_view_builder.get_object('playlist_view')

        # a list of cell renderers used in the playlist view
        self.cell_renderers = []

        # initialize the TreeView columns and add them to the playlist view
        for col in book_view_columns.display_cols:
            rend = self.init_cell_renderer(col)
            tvc = self.init_tree_view_column(col, rend)
            self.playlist_view.append_column(tvc)
            self.cell_renderers.append(rend)
            #rend.connect("edited", self.on_edited, col)
            #rend.connect("editing-started", self.on_editing_started, col)
            #rend.connect("editing-canceled", self.on_editing_cancelled)

    def init_cell_renderer(self, col):
        """
        initialize a cell renderer for display in the playlist treeview
        This is what gets displayed in a combo box popup.
        """
        rend = Gtk.CellRendererCombo()
        rend.set_property("text-column", 0)
        rend.set_property("editable", True)
        rend.set_property("has-entry", False)
        # col 0 is playlist.TrackMDEntry.entry(type depends on column);
        # col 1 is playlist.TrackMDEntry.id_ (int for all columns)
        rend.set_property("model", Gtk.ListStore(col['g_typ'], int))
        return rend

    def init_tree_view_column(self, col, rend):
        """initialize a single column for display in the treeview"""
        tvc = Gtk.TreeViewColumn(col['name'])
        tvc.pack_start(rend, True)
        tvc.add_attribute(rend, "text", col['g_col'])
        tvc.set_sort_order(Gtk.SortType.DESCENDING)
        tvc.set_clickable(True)
        #tvc.connect("clicked", self.on_clicked, col['g_col'])
        return tvc

    def get_cell_renderers(self) -> 'list':
        """
        get the list of Gtk.CellRenderersCombo's
        associated with the playlist view
        """
        return self.cell_renderers

    def set_model(self, playlist):
        """
        assign a GTK.TreeViewModel to the TreeView.

        From the Gtk docs:
        Sets the model for a GtkTreeView.
        If the tree_view already has a model set, it will remove it before setting the new model.
        If model is NULL, then it will unset the old model.
        """
        self.playlist_view.set_model(playlist)

    def close(self):
        self.playlist_view.destroy()


class Playlist_VC:
    """Controller for the treeview that displays a playlist"""

    def __init__(self, book_, book_transmitter, component_transmitter, book_view_builder):
        # save a reference to the transmitter that this class uses to send messages bak to Book_C
        self.transmitter = component_transmitter
        # subscribe to the signals relevant to this class
        book_transmitter.connect('close', self.close)
        book_transmitter.connect('update', self.update)
        book_transmitter.connect('save', self.save)
        # copy the default list of columns that will be displayed
        self.display_cols = book_view_columns.display_cols.copy()
        # the view
        self.playlist_v = Playlist_V(self.display_cols, book_view_builder)
        # the Book model that holds the playlist data
        self.book = book_
        # the column definitions that will be used to describe the playlist model data
        self.playlist_columns = [
                *book_view_columns.pl_track_col_list,
                *book_view_columns.track_col_list,
                *book_view_columns.metadata_col_list,
                *book_view_columns.metadata_id_col_list,
                book_view_columns.playlist_row_id
            ]

        # unique id generator for the rows in the playlist model
        self.row_id_iter = itertools.count()

        # generate the playlist model for display
        self.playlist = self.get_playlist_new()
        # assign the playlist to the view
        self.playlist_v.set_model(self.playlist)

        # each track metadata entry is a list. This secondary_metadata list is used to hold
        # track metadata beyond the first entry in each track's metadata list
        # that gets displayed in the playlist view. The secondary_metadata
        # will be used to populate combo box popups on demand when the user
        # wants to see or edit more than just the first metadata entry. Entries will
        # come in the form of a tuple (FK->playlist_row_id, TrackMDEntry)
        # *FK = foreign key
        self.secondary_metadata = []

    def get_view(self):
        pass

    def update(self):
        # clear the playlist view
        self.playlist.clear()
        # pop each track off of the list and move the data to self.playlist
        while True:
            track = self.book.pop_track()
            if track is None:
                break
            self.__add_track(track)

    def begin_edit_mode(self):
        pass

    def begin_display_mode(self):
        pass

    def close(self):
        self.playlist_v.close()

    def get_playlist_new(self):
        """create a new model for the playlist"""
        # sort the displayed columns by g_col number
        sorted_playlist_columns = sorted(self.playlist_columns, key=lambda x: x['g_col'])
        # get a list of the g_typ's from each of the columns
        playlist_col_types = map(lambda x: x['g_typ'], sorted_playlist_columns)
        # create the playlist model
        return Gtk.ListStore(*playlist_col_types)

    def genereate_row_id(self) -> 'row_id:int':
        """generate a unique row id for the playlist"""
        return next(self.row_id_iter)

    def __add_track(self, track):
        """add data from a track object into the playlist view"""
        # append a new row to the playlist
        cur_row = self.playlist.append()
        # load the metadata columns
        self.__add_metadata_columns(track, cur_row)
        # load track data not stored in the metadata dictionary
        self.__add_track_columns(track, cur_row)
        # add the column that holds the unique row id specific to this instance of the Book_VC
        self.__add_row_id_column(track, cur_row)

    def __add_row_id_column(self, track, cur_row):
        self.playlist.set_value(cur_row, book_view_columns.playlist_row_id['g_col'], self.genereate_row_id())

    def __add_track_columns(self, track, cur_row):
        self.playlist.set_value(cur_row, book_view_columns.track_file['g_col'], track.get_file_name())
        self.playlist.set_value(cur_row, book_view_columns.track_path['g_col'], track.get_file_path())


    def __add_metadata_columns(self, track, cur_row):
        """load the first entry of all of the track metadata"""
        for col in book_view_columns.metadata_col_list:
            track_md_entry_list = track.get_entries(col['key'])
            if track_md_entry_list:
                # load the entry portion of the first TrackMDEntry
                self.playlist.set_value(cur_row, col['g_col'], track_md_entry_list[0].get_entry())
                # load the id portion of the first TrackMDEntry
                self.playlist.set_value(cur_row, col['id_column']['g_col'], track_md_entry_list[0].get_id())

    def save(self):
        print('Playlist_VC.save()')

