# -*- coding: utf-8 -*-
#
#  book_view.py
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
This module is responsible for displaying books in the view
"""
from pathlib import Path
import itertools
import gi
#pylint: disable=wrong-import-position
gi.require_version("Gtk", "3.0")
#pylint: enable=wrong-import-position
from gi.repository import Gtk
import playlist
import signal_
from gui.gtk import book_view_columns
import pdb #pylint: disable=unused-import, wrong-import-order


class BookV:
    """
    BookV is a container for displaying the different
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
        """close all gui components in preperation for this object to close"""
        self.book_v_box.destroy()
        #self.pinned_v_box.destroy()

    def get_gui_builder(self) -> 'Gtk.builder':
        """return the gtk.builder object"""
        return self.book_view_builder

class BookVC:
    """
    BookVC is a controller for BookV
    """
    def __init__(self, book_tx_signal):
        book_tx_signal.connect('close', self.close)
        self.book_v = BookV()

    def get_view(self):
        """get the view container so it can be added to the main application window"""
        return self.book_v.book_v_box

    def close(self):
        """relay the message to close the view"""
        self.book_v.close()

    def get_gui_builder(self):
        """get the builder object, so the sabe instance of the builder can be passed to the component views"""
        return self.book_v.get_gui_builder()


class TitleV:
    """display the book title"""

    def __init__(self, book_view_builder):
        # the topmost box in the glade file; add it to self
        self.title_view = book_view_builder.get_object('title_v_box')
        # The label used to display the title of the book
        self.title_label = book_view_builder.get_object('title_label')
        self.title_label.set_max_width_chars(40)
        # The entry that allows the user to change the title of the book
        self.title_entry = book_view_builder.get_object('title_entry')
        self.title_entry.set_max_width_chars(40)

    def close(self):
        """delete the objects controlled by this view"""
        self.title_entry.destroy()
        self.title_label.destroy()
        self.title_view.destroy()

    def get_view(self):
        """get the view that this class is controlling"""
        return self.title_view



class TitleVC:
    """controller for displaying the book title"""

    def __init__(self, book_, book_tx_signal, component_transmitter, book_view_builder):
        # save a reference to the transmitter that this class uses to send messages back to BookC
        self.transmitter = component_transmitter
        # subscribe to the signals relevant to this class
        book_tx_signal.connect('close', self.close)
        book_tx_signal.connect('begin_edit_mode', self.begin_edit_mode)
        book_tx_signal.connect('begin_display_mode', self.begin_display_mode)
        book_tx_signal.connect('update', self.update)
        book_tx_signal.connect('save_title', self.save)
        # save a reference to the book model so TitleVC can get data when it needs to
        self.book = book_
        # create the Gtk view
        self.title_v = TitleV(book_view_builder)

    def get_view(self):
        """get the view that this class is controlling"""
        return self.title_v.get_view()

    def update(self):
        """get title from book and load it into the view"""
        # get title from book
        book_title = self.book.get_playlist_data().get_title()
        # load the title into the title label thats shown during display mode
        self.title_v.title_label.set_label(book_title)

    def begin_edit_mode(self):
        """set the Title view to the proper mode for editing the title"""
        # load existing title into entry widget
        self.title_v.title_entry.set_text(self.title_v.title_label.get_text())
        self.title_v.title_entry.show()
        self.title_v.title_label.hide()

    def begin_display_mode(self):
        """set the Title view to the proper mode for displaying the title"""
        self.title_v.title_entry.hide()
        self.title_v.title_label.show()

    def close(self):
        """relay the message to close the view"""
        self.title_v.close()

    def save(self):
        """get the playlist title from the title_v model and save it to the book."""
        self.book.get_playlist_data().set_title(self.title_v.title_entry.get_text())
        self.book.save_playlist_data()

class ControlBtnV:
    """display the control buttons"""

    def __init__(self, book_view_builder):
        self.save_button = book_view_builder.get_object('save_button')
        self.cancel_button = book_view_builder.get_object('cancel_button')
        self.edit_button = book_view_builder.get_object('edit_button')

    def get_save_button(self):
        """get the save button object"""
        return self.save_button

    def get_cancel_button(self):
        """get the cancel button object"""
        return self.cancel_button

    def get_edit_button(self):
        """get the edit button object"""
        return self.edit_button

    def close(self):
        """delete the components controlled by this view"""
        self.save_button.destroy()
        self.cancel_button.destroy()
        self.edit_button.destroy()


class ControlBtnVC:
    """control the control buttons display"""

    def __init__(self, book_, book_tx_signal, component_transmitter, book_view_builder):
        # save a reference to the transmitter that this class uses to send messages bak to BookC
        self.transmitter = component_transmitter
        # subscribe to the signals relevant to this class.
        book_tx_signal.connect('close', self.close)
        book_tx_signal.connect('begin_edit_mode', self.begin_edit_mode)
        book_tx_signal.connect('begin_display_mode', self.begin_display_mode)

        # save a reference to the book model so ControlBtnVC can get data when it needs to.
        self.book = book_

        # instantiate the view
        self.control_btn_v = ControlBtnV(book_view_builder)

        # connect to the control button signals
        self.control_btn_v.save_button.connect(
                'button-release-event',
                self.on_control_button_released,
                'save_button'
            )
        self.control_btn_v.cancel_button.connect(
                'button-release-event',
                self.on_control_button_released,
                'cancel_button'
            )
        self.control_btn_v.edit_button.connect(
                'button-release-event',
                self.on_control_button_released,
                'edit_button'
            )

    def begin_edit_mode(self):
        """dislay the correct buttons for editing mode"""
        self.control_btn_v.save_button.show()
        self.control_btn_v.cancel_button.show()
        self.control_btn_v.edit_button.hide()

    def begin_display_mode(self):
        """dislay the correct buttons for display mode"""
        self.control_btn_v.save_button.hide()
        self.control_btn_v.cancel_button.hide()
        self.control_btn_v.edit_button.show()

    def close(self):
        """relay the message to close the view"""
        self.control_btn_v.close()

    def on_control_button_released(self, button, event_button, control_signal): #pylint: disable=unused-argument
        """
        callback for control button release events originating in ControlBtnV.
        relay the event to BookC
        """
        self.transmitter.send(control_signal)


class  PlaylistV:
    """dislay the playlist in a Gtk.Treeview"""

    def __init__(self, display_columns, book_view_builder):
        # display the playlist in a gtk treeview
        self.playlist_view = book_view_builder.get_object('playlist_view')
        self.playlist_view.set_reorderable(True)
        # a list of cell renderers used in the playlist view
        self.cell_renderers = []
        # Relay Gtk signals back to the controller
        self.transmitter = signal_.Signal()
        self.transmitter.add_signal('col_header_clicked')

        self.tvc_list = []
        # initialize the TreeView columns and add them to the playlist view
        for col in display_columns:
            rend = self.init_cell_renderer(col)
            tvc = self.init_tree_view_column(col, rend)
            # track number is the default sort column for the playlist
            if col is book_view_columns.md_track_number:
                self.default_sort_tree_view_col = tvc
            self.tvc_list.append(tvc)
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

    def init_tree_view_column(self, col, rend) -> Gtk.TreeViewColumn:
        """initialize a single column for display in the treeview"""
        tvc = Gtk.TreeViewColumn(col['name'])
        tvc.pack_start(rend, True)
        tvc.add_attribute(rend, "text", col['g_col'])
        tvc.set_sort_order(Gtk.SortType.DESCENDING)
        tvc.set_clickable(True)
        tvc.connect('clicked', self.on_header_clicked, col)
        return tvc

    def get_cell_renderers(self) -> list:
        """
        get the list of Gtk.CellRenderersCombo's
        associated with the playlist view
        """
        return self.cell_renderers

    def set_model(self, playlist_model):
        """
        assign a GTK.TreeViewModel to the TreeView.

        From the Gtk docs:
        Sets the model for a GtkTreeView.
        If the tree_view already has a model set, it will remove it before setting the new model.
        If model is NULL, then it will unset the old model.
        """
        self.playlist_view.set_model(playlist_model)

    def close(self):
        """close all gui components in preperation for this object to close"""
        self.playlist_view.destroy()

    def on_header_clicked(self, tvc, col):
        """repeat the clicked/col_header_clicked signal on self's own transmitter"""
        self.transmitter.send('col_header_clicked', tvc, col)


class PlaylistSortable:
    """
    A Data container that overrides __lt__ so numeric data can be displayed as strings but be sorted like numbers.
    __lt__ is overridden if the passed in col info dict has a 'data_type' key with a value of 'numeric'.
    """

    def __init__(self, value, col):
        self.value = value
        self.type_ = col['data_type'] if 'data_type' in col else None

    def __lt__(self, other):
        """overidee the lt comparison if self.value is a string representing a numeric type"""
        if self.type_ == 'numeric':
            return self.less_than_str_as_num(other)
        return self.value < other.value

    def less_than_str_as_num(self, other):
        """
        convert strings (self.value and other.value) to ints before comparing.
        All strings that are not proper numbers are evaluated equal to each other, but less than numbers.
        """
        try:
            num1 = int(self.value)
        except (ValueError, TypeError):
            num1 = -1
        try:
            num2 = int(other.value)
        except (ValueError, TypeError):
            num2 = -1

        if num1 < num2:
            return True
        return False


class PlaylistVC:
    """Controller for the treeview that displays a playlist"""

    def __init__(self, book_, book_transmitter, component_transmitter, book_view_builder):
        # save a reference to the transmitter that this class uses to send messages bak to BookC
        self.transmitter = component_transmitter
        # subscribe to the signals relevant to this class
        book_transmitter.connect('close', self.close)
        book_transmitter.connect('update', self.update)
        book_transmitter.connect('save', self.save)
        book_transmitter.connect('begin_edit_mode', self.begin_edit_mode)
        book_transmitter.connect('begin_display_mode', self.begin_display_mode)

        # Set up the playlist view.
        # Copy the default list of columns that will be displayed.
        self.display_cols = book_view_columns.display_cols.copy()
        # the view
        self.playlist_v = PlaylistV(self.display_cols, book_view_builder)
        self.playlist_v.transmitter.connect('col_header_clicked', self.on_sort_by_column)

        # the Book model that holds the playlist data
        self.book = book_

        # generate the playlist model for display
        self.playlist_model = PlaylistVM()
        # clear sort indicators when a row is manually moved by drag and drop
        self.playlist_model.transmitter.connect('row_deleted', self.clear_col_sort_indicators)
        # assign the playlist to the view
        self.playlist_v.set_model(self.playlist_model.get_model())

    def update(self):
        """get the tracklist from the Book and add the data to the playlist_model and secondary_metadata models"""
        # clear the playlist view
        self.playlist_model.clear()
        # pop each track off of the list and move the data to self.playlist
        while True:
            track = self.book.pop_track()
            if track is None:
                break
            self.playlist_model.add_track(track)
        self.init_default_sort_order()

    def begin_edit_mode(self):
        """pass"""
        self.set_column_clickability(True)

    def begin_display_mode(self):
        """put the Playlist view in display mode"""
        self.clear_col_sort_indicators()
        self.set_column_clickability(False)

    def close(self):
        """relay the message to close the view"""
        self.playlist_v.close()

    def save(self):
        """
        Get Track objects represented by rows in the playlist_model and save them to the Book
        """
        while True:
            track = self.playlist_model.pop()
            if track is None:
                break
            self.book.save_track(track)

    def get_toggled_tv_col_direction(self, tree_view_column):
        """Get the current sort order (Gtk.SortType) for a tree view column and return the opposite Gtk.SortType"""
        if tree_view_column.get_sort_order() == Gtk.SortType.DESCENDING:
            return Gtk.SortType.ASCENDING
        return Gtk.SortType.DESCENDING

    def on_sort_by_column(self, tree_view_column, col):
        """
        Sort the playlist view by the data in one column.
        callback triggered when a column header in the view is clicked
        """
        new_sort_direction = self.get_toggled_tv_col_direction(tree_view_column)
        tree_view_column.set_sort_order(new_sort_direction)
        self.playlist_model.sort_by_col(col, new_sort_direction)
        # make it so that tree_view_column is the only column with its sort indicator set
        self.clear_col_sort_indicators()
        tree_view_column.set_sort_indicator(True)

    def clear_col_sort_indicators(self):
        """hide the sort indicator from all of the displayed treeview columns"""
        for tv_c in self.playlist_v.tvc_list:
            tv_c.set_sort_indicator(False)

    def init_default_sort_order(self):
        """
        When openning a new book, sort the playlist by the default sort column, set in the view.
        Do nothing if the playlist is being pulled from the database
        """
        if not self.book.is_saved():
            self.playlist_v.default_sort_tree_view_col.clicked()

    def set_column_clickability(self, active:bool):
        """
        Set all treview column headers to be either clickable or unclickable.
        This changes the ability to sort the playlist by column.
        """
        for tree_view_column in self.playlist_v.tvc_list:
            tree_view_column.set_clickable(active)

class PlaylistVM:
    """
    wrapper for the PlaylistVC.playlist, Gtk.Liststore.
    gives and takes data passed in Tracks, and manages its storage in the Gtk.Liststore
    """

    def __init__(self):
        # send notifications to the controller
        self.transmitter = signal_.Signal()
        self.transmitter.add_signal('row_deleted')
        # unique id generator for the rows in the playlist model
        self.row_id_iter = itertools.count()

        # the column definitions that will be used to describe the playlist model data
        self.playlist_columns = [
                *book_view_columns.pl_track_col_list,
                *book_view_columns.track_col_list,
                *book_view_columns.metadata_col_list,
                *book_view_columns.metadata_id_col_list,
                book_view_columns.playlist_row_id
            ]

        # The model of the playlist data that will be displayed in the view
        self.playlist = self.get_playlist_new()
        self.playlist.connect("row_deleted", self.on_row_deleted)
        # each track metadata entry is a list. This secondary_metadata list is used to hold
        # track metadata beyond the first entry in each track's metadata list
        # that gets displayed in the playlist view. The secondary_metadata
        # will be used to populate combo box popups on demand when the user
        # wants to see or edit more than just the first metadata entry. Entries will
        # come in the form of a tuple (FK->playlist_row_id, key, TrackMDEntry)
        # *FK = foreign key
        self.secondary_metadata = SecondaryMetadata()


    def get_playlist_new(self):
        """create a new model for the playlist"""
        # sort the displayed columns by g_col number
        sorted_playlist_columns = sorted(self.playlist_columns, key=lambda x: x['g_col'])
        # get a list of the g_typ's from each of the columns
        playlist_col_types = map(lambda x: x['g_typ'], sorted_playlist_columns)
        # create the playlist model
        return Gtk.ListStore(*playlist_col_types)


    def add_track(self, track) -> 'playlist_row_id:int':
        """add data from a track object into the playlist view"""
        # append a new row to the playlist
        cur_row = self.playlist.append()
        # add the column that holds the unique row id specific to this instance of the BookVC
        playlist_row_id = self.__add_row_id_column(cur_row)
        # load the metadata columns
        self.__add_metadata_columns(track, cur_row, playlist_row_id)
        # load track data not stored in the metadata dictionary
        self.__add_track_columns(track, cur_row)
        self.__add_pl_track_columns(track, cur_row)
        return playlist_row_id

    def __add_row_id_column(self, cur_row) -> 'row_id:int':
        """get a unique id for the playlist row and add it to the playlist_row_id column for the current row"""
        id_ = self.genereate_row_id()
        self.playlist.set_value(cur_row, book_view_columns.playlist_row_id['g_col'], id_)
        return id_

    def __add_track_columns(self, track, cur_row):
        """add the non metadata columns, track_file and track_path, to the current row in self.playlist"""
        self.playlist.set_value(cur_row, book_view_columns.track_file['g_col'], track.get_file_name())
        self.playlist.set_value(cur_row, book_view_columns.track_path['g_col'], track.get_file_path())

    def __load_track_columns(self, track, cur_row):
        """load track file path data from the playlist into the Track"""
        # The playlist displays both path and filename, but Tracks only store the path, so only get the path
        track.set_file_path(self.playlist.get_value(cur_row, book_view_columns.track_path['g_col']))

    def __add_metadata_columns(self, track, cur_row, playlist_row_id):
        """
        Load the first entry of all of the track metadata into self.playlist.
        Load subsequent entries into self.secondary_metadata.
        """
        for col in book_view_columns.metadata_col_list:
            track_md_entry_list = track.get_entries(col['key'])
            for track_md_entry in track_md_entry_list:
                if track_md_entry.get_index() == 0:
                    # index zero goes into self.playlist. first the entry portion then id.
                    # The index portion is always zero for the playlist, so its not kept.
                    self.playlist.set_value(cur_row, col['g_col'], track_md_entry_list[0].get_entry())
                    self.playlist.set_value(cur_row, col['id_column']['g_col'], track_md_entry_list[0].get_id())
                else:
                    # Subsequent entries go into self.secondary_metadata
                    self.secondary_metadata.add_entry(playlist_row_id, col['key'], track_md_entry)

    def __load_metadata_columns(self, track, cur_row, row_id):
        """
        Copy data from the displayed Gtk.Liststore (self.playlist) to Track object
        This method copies the track metadata stored in the playlist, referenced by the columns in the metadata_col_list
        """
        for col in book_view_columns.metadata_col_list:
            # Tracks store metadata as a list of TrackMDEntries(index, entry, id)
            entry_list = []
            md_entry = playlist.TrackMDEntry()
            # get the data for the first row of the TrackMDEntry list
            md_entry.set_entry(self.playlist.get_value(cur_row,col['g_col']))
            # don't add empty md_entries to the list even if it has an id. The Book will remove the deleted entry
            if not md_entry.get_entry():
                continue
            md_entry.set_id(self.playlist.get_value(cur_row,col['id_column']['g_col']))
            md_entry.set_index(0)
            # add the TrackMDEntry to the list
            entry_list.append(md_entry)
            # Add any secondary metadata entries to the entry_list.
            secondary_md_entries = self.secondary_metadata.get_entries(row_id, col['key'])
            entry_list.extend(secondary_md_entries)
            # put the metadata entries in the Track object
            track.set_entry(col['key'], entry_list)

    def get_model(self):
        """get the Gtk.Liststore used to display the playlist"""
        return self.playlist

    def clear(self):
        """remove all rows from self.playlist"""
        self.playlist.clear()

    def genereate_row_id(self) -> 'row_id:int':
        """generate a unique row id for the playlist"""
        return next(self.row_id_iter)

    def pop(self):
        """create a track object with data from the model (Gtk.Liststore)"""
        # break out if there is nothing to do here
        if not self.playlist.get_iter_first():
            return None
        # The Track that is built and returned.
        track = playlist.Track()
        # load the last row number into the Track
        self.__load_last_row_number(track)
        cur_row_num = track.get_number()
        # retrieve gtk iter that referenes the last row from the playlist
        cur_row_iter = self.playlist.get_iter((cur_row_num-1,))
        # The gtk row_id for the track
        row_id = self.get_row_id(cur_row_iter)
        # load the metadata columns
        self.__load_metadata_columns(track, cur_row_iter, row_id)
        # load track data not stored in the metadata dictionary
        self.__load_track_columns(track, cur_row_iter)
        self.__load_pl_track_columns(track, cur_row_iter)
        # remove the row from the playlist
        self.playlist.remove(cur_row_iter)
        return track

    def __load_last_row_number(self, track):
        """
        Determine the last row number (a one based index) of self.playlist by testing for length of the playlist.
        Assign the last row number to the Track object.
        """
        last_row_num = len(self.playlist)
        track.set_number(last_row_num)

    def get_row_id(self, cur_row):
        """get the unique row id for cur_row in self.playlist"""
        return self.playlist.get_value(cur_row, book_view_columns.playlist_row_id['g_col'])

    def sort_by_col(self, col, new_sort_direction):
        """
        Sort the playlist model based on the data in a single column.

        Create sortable list of lists of column data:
                    current row numner,
                    data being sorted on

        Use that sortable list to create the required arguments for the Gtk.Liststore.reorder method.

        Use Gtk.Liststore.reorder() to set the playlist model to the new sort order.
        """
        sorting_list = []
        for row_num, row in enumerate(self.playlist):
            # Use PlaylistSortable because columns with a datatype key defined as numeric need to be sorted differently
            row_data = PlaylistSortable(row[col['g_col']], col)
            sorting_list.append([row_num, row_data])

        sorting_list.sort(
                key=lambda row: row[1],
                reverse=(new_sort_direction == Gtk.SortType.DESCENDING)
            )

        self.playlist.reorder([item[0] for item in sorting_list])

    def on_row_deleted(self, *args) -> None: #pylint: disable=unused-argument
        """repeat signal that a row in the playlist model has been deleted"""
        self.transmitter.send('row_deleted')

    def __add_pl_track_columns(self, track, cur_row):
        """add pl_track data from a track object into the playlist view model"""
        self.playlist.set_value(cur_row, book_view_columns.pl_track_id['g_col'], track.get_pl_track_id())

    def __load_pl_track_columns(self, track, cur_row):
        """load pl_track data from the playlist into the Track"""
        track.set_pl_track_id(self.playlist.get_value(cur_row, book_view_columns.pl_track_id['g_col']))



class SecondaryMetadata:
    """
    Data storage model for storing secondary Track.metadata.
    Track.metadata is a dict with a list of TrackMDEntries (id, index, entry) for each key.
    The first entries for each key are displayed in the main treeview and are stored in its data model, Gtk.Liststore
    This class stores the entries that are not displayed in the treeview.
    SecondaryMetadata stores its data as a list of tuples, (FK->pl_row_id, key, TrackMDEntry).
    *FK = foreign key
    """

    def __init__(self):
        # create the data storage model for this class
        self.secondary_metadata = []

    def add_entry(self, row_id, key, track_md_entry):
        """add a TrackMDEntry to along with its playlist row and column descriptors self.secondary_metadata"""
        self.secondary_metadata.append((row_id, key, track_md_entry))

    def add_track(self, playlist_row_id, track):
        """
        Pull the metadata from the Track.
        append entries with non zero indices to self.secondary_metadata
        """
        for key in track.get_key_list():
            for entry in track.get_entries(key):
                if entry.get_index() == 0:
                    continue
                self.add_entry(playlist_row_id, key, entry)

    def get_entries(self, row_id, key):
        """get a list of trackMdEntries that match that the row id and key"""
        return [entry[2] for entry in self.secondary_metadata if entry[0] == row_id and entry[1] == key]
