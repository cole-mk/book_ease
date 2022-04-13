#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  untitled_python3.py
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
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, GLib, Gdk
from gi.repository.GdkPixbuf import Pixbuf
import os
import configparser
from datetime import datetime
import re
import vlc
import mutagen
from mutagen.easyid3 import EasyID3
from threading import Thread
import cairo
import sqlite3
from pathlib import Path
import playlist
from gui.gtk import BookView
import signal_
import pdb

#p = playlist_data.

class media_player:

    def __init__(self, config):
        self.config = config
        #self.player = vlc.Instance()
        #self.media_list = []
        #self.playlist_file = 'playlist.m3u'        
        #if config.has_option('app', 'playlist_file'):
        #   tmp_playlist_file = config['app']['playlist_file']
        #   if os.path.exists(tmp_playlist_file.rstrip()):
        #       print('tmp_playlist_file exists')
        #       self.playlist_file = tmp_playlist_file
        


class RenameTvEntryDialog(Gtk.Dialog):

    def __init__(self, parent, title="My Dialog"):
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
            self.entry_2.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, 'folder')
            self.entry_2.connect('icon-press', self.on_file_chooser_icon_pressed, file_chooser_method)

    def on_file_chooser_icon_pressed(self, entry, icon_pos, event, file_chooser_method=None):
        name, path = file_chooser_method()
        if name and path:
            self.entry_2.set_text(path)


class BookMark:
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
        self.rendererIcon = Gtk.CellRendererPixbuf()

        self.rendererText = Gtk.CellRendererText()
        self.rendererText.editable = True
        
        self.column = Gtk.TreeViewColumn("Bookmarks")
        self.column.pack_start(self.rendererIcon, False)
        self.column.pack_start(self.rendererText, True)
        self.column.add_attribute(self.rendererIcon, "pixbuf", self.icon_pos)
        self.column.add_attribute(self.rendererText, "text", self.name_pos)

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
        sel = self.bookmark_view.get_selection()
        model, paths = sel.get_selected_rows()
        sel.unselect_all()
        # reversed so the itr isn't corrupted on multiselect
        for p in reversed(paths):
            itr = model.get_iter(p)
            name = model.get_value(itr, self.name_pos)
            model.remove(itr)

    def rename_selected_bookmark(self):
        sel = self.bookmark_view.get_selection()
        model, paths = sel.get_selected_rows()
        sel.unselect_all()
        # get the selected bookmark model from the row
        for p in paths:
            itr = model.get_iter(p)
            name = model.get_value(itr, self.name_pos)
            target = model.get_value(itr, self.target_pos)
            # get rename info from the user
            dialog = RenameTvEntryDialog(self, title='Rename Bookmark')
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
    
    def select_dir_dialog(self, path=None):
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
        if name is not None and path is not None:
            icon = Gtk.IconTheme.get_default().load_icon('folder', 24, 0)
            self.bookmark_model.append([icon, name, path])
            # update the config for data persistence
            self.config.set(self.config_section_name, name, path)

    def cm_on_deactivate(self, user_data=None):
        sel = self.bookmark_view.get_selection()
        sel.unselect_all()

    def cm_on_item_button_release(self, button, event, user_data=None):
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
    
    def on_button_release(self, button, event):
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

    def on_button_press(self, button, event, user_data=None):
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

    #callback for treestore row deleted, catching the user drag icons to reorder
    def on_row_deleted(self, path, user_data=None):
        self.update_bookmark_config()

    def update_bookmark_config(self):
        self.config.remove_section(self.config_section_name)
        self.config.add_section(self.config_section_name)
        for i in self.bookmark_model:
            self.config.set(self.config_section_name, i[1], i[2])

    def reload_bookmarks(self):
        for key in self.config[self.config_section_name]:
            if os.path.isdir(self.config[self.config_section_name][key]):
                icon = Gtk.IconTheme.get_default().load_icon('folder', 24, 0)
                self.bookmark_model.append([icon, key, self.config[self.config_section_name][key]])


class Image_View:
    def __init__(self, image_view, files, config, builder):
        self.image_view_section = 'image_view'
        self.files = files
        self.config = config
        self.builder = builder
        #self.image_view = image_view
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

    def is_image_file(self, file):
        for i in self.f_type_re:
            if i.match(file):
                return True
        return False

    def on_btn_release_event(self, button, event, user_data=None ):
        pass


    def on_configure(self, area, event, data=None): 
        # redraw the image
        self.init_surface(self.image_view_da)
        self.surface.flush()

    def init_surface(self, area):
        # Destroy previous buffer
        if self.surface is not None:
            self.surface.finish()
            self.surface = None
        # Create a new buffer
        (w, h) = self.get_image_scale()
        disp_pixbuf = self.pixbuf.scale_simple(w, h, GdkPixbuf.InterpType.BILINEAR)
        self.surface = Gdk.cairo_surface_create_from_pixbuf(disp_pixbuf, 1, None)
    
    def on_draw(self, area, context):
        if self.surface is not None:
            context.set_source_surface(self.surface, 0.25, 0.25)            
            context.paint()
        else:
            print('Invalid surface')
        return False
    
    def get_image_scale(self):
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




# TODO: file_list can be removed from the constructor all together. create_book can get it from self.files 
class Book(playlist.Playlist, signal_.Signal_):
    def __init__(self, path, file_list, config, files, book_reader):
        playlist.Playlist.__init__(self)
        signal_.Signal_.__init__(self)
        self.index = None
        self.title = 'New Book'                 #####
        self.playlist_id = None                 #####
        self.config = config
        self.files = files
        self.book_section = 'books'
        self.path = path                        #####
        self.book_reader = book_reader
        self.db = BookReader_DB(self)
        # track metadata
        self.file_list = file_list
        # added to parent as track_list
        #self.track_list = []
        self.title_keys = ['title', 'album']
        self.author_keys = ['author', 'artist', 'performer', 'composer']
        self.read_by_keys = ['performer','author', 'artist', 'composer']
        self.length_keys = ['length']
        self.track_keys = ['tracknumber']
        # playlist_filetypes key has values given in a comma separated list
        file_types = config[self.book_section]['playlist_filetypes'].split(",")
        # build compiled regexes for matching list of media suffixes. 
        self.f_type_re = []
        for i in file_types:
            i = '.*.\\' + i.strip() + '$'
            self.f_type_re.append(re.compile(i))

        # initialize the callback system
        self.add_signal('book_data_loaded')
        self.add_signal('book_data_created')
        self.add_signal('book_saved')

        # path needs to be stored with the metadata info. what if someone add tracks from outside the playlist directory? hmmm? 
        self.pl_title    = {'name':'Title',         'col':0, 
                            'g_typ':str,            'editable':True,
                            'table':'track_title',  'field':'title',
                            'key':'title',  'alt_keys':['album']}   

        self.pl_author   = {'name':'Author',            'col':1,
                            'g_typ':str,                'editable':True ,
                            'table':'track_author',     'field':'author',
                            'key':'author',             'alt_keys':['artist', 'performer', 'composer']}

        self.pl_read_by  = {'name':'Read by',           'col':2, 
                            'g_typ':str,                'editable':True ,
                            'table':'track_read_by',    'field':'read_by', 
                            'key':'performer',          'alt_keys':['author', 'artist', 'composer']}
        
        self.pl_length   = {'name':'Length',            'col':3,
                            'g_typ':str,                'editable':True ,
                            'table':'track_length',     'field':'length', 
                            'key':'length',             'alt_keys':[None]}
        
        self.pl_track    = {'name':'Track',             'col':4,
                            'g_typ':str,                'editable':True ,
                            'table':'track_number',     'field':'number', 
                            'key':'tracknumber',        'alt_keys':[None]}
                            
        self.pl_file     = {'name':'File',      'col':5,
                            'g_typ':str,        'editable':False,
                            'table':'track',    'field':'filename', 
                            'key':'file',       'alt_keys':[None]}
                            
        self.pl_row_id   = {'name':'pl_row_id',     'col':6,
                            'g_typ':int,            'editable':True , 
                            'table':None,           'field':None,
                            'key':'pl_row_id',      'alt_keys':[None]}

        self.pl_path      = {'name':'pl_path',  'col':7,
                            'g_typ':str,        'editable':False , 
                            'table':'track',    'field':'path',
                            'key':None,         'alt_keys':[None]}
        
        self.pl_saved_col_list = [self.pl_title,  self.pl_author, self.pl_read_by,
                                  self.pl_length, self.pl_track,  self.pl_file, self.pl_path]
 
        self.metadata_col_list =[self.pl_title,  self.pl_author, self.pl_read_by,
                                 self.pl_length, self.pl_track] 

    # get list of playlists associated with current path
    def get_cur_pl_list(self):
        return self.db.get_cur_pl_list()

    def get_cur_pl_row(self):
        cur_pl_list = self.get_cur_pl_list()
        cur_pl_row = None
        for row in cur_pl_list:
            if row[self.db.cur_pl_id['col']] == self.playlist_id:
                cur_pl_row = row
                break
        if cur_pl_row == None:
            raise KeyError(self.playlist_id, 'not found in currently saved playlists associated with this path')
        return cur_pl_row

    def get_track_list(self):
        return self.track_list

    def get_index(self):
        return self.index

    def set_index(self, index):
        self.index = index

    def get_title_l(self, row):
        track = self.track_list[row]
        return track.get_entries(self.title_keys)
    # initialize the playlist 

    def book_data_load(self, pl_row):
        # pl_row is row (tuple) from playlist database table (displayed in BookView)
        #TODO: get rid of the g_cols
        self.db.cur_pl_path['col'] 
        self.title = pl_row[self.db.cur_pl_title['col']]
        self.playlist_id = pl_row[self.db.cur_pl_id['col']]
        self.path = pl_row[self.db.cur_pl_path['col']]
        track_list = self.db.playlist_get_tracks(self.playlist_id)
        # move track data from database into internal tracklist   
        for i, tr in enumerate(track_list):
            file_path = self.db.track_get_path(tr['track_id'])
            track = playlist.Track(file_path)
            track.set_entry(self.pl_row_id['key'], [tr['id']])
            track.set_saved(True)
            track.set_row_num(tr['track_number'])
            self.track_list.append(track)
            # move the track attributes(metadata) from db to tracklist
            for col in self.metadata_col_list:
                entries = self.db.track_metadata_get(tr['id'], col['key'])
                tr_entries_list = []
                for entry in entries:
                    tr_entries_list.append(entry['entry'])
                track.set_entry(col['key'], tr_entries_list)
        # playlist is now a saved playlist
        self.saved_playlist = True
        # sort playlist by  row_num
        self.track_list_sort_row_num()
        # notify listeners that book data has been loaded
        self.signal('book_data_loaded')

    # initialize the playlist 
    def create_book_data(self, callback=None, **kwargs):
        #dont enumerate filelist, we nee more control over i
        i = 0
        for f in self.file_list:
            # populate playlist data
            file_path = os.path.join(self.path, f[1])
            if not f[self.files.is_dir_pos] and self.book_reader.is_media_file(file_path):
                track = playlist.Track(file_path)
                track.load_metadata_from_file()
                track.set_entry(self.pl_row_id['key'], [i])
                # do the appending  
                self.track_list.append(track)
                i+=1
                # check for alt values if this entry is empty
                for col in self.pl_saved_col_list:
                    if not track.get_entries(col['key']):
                        #has_entry = False
                        for k in col['alt_keys']:
                            val = track.get_entries(k)
                            if val:
                               track.set_entry(col['key'], val)
                               break
        # set book title from the first track title
        title_list = self.track_list[0].get_entries('title')
        if title_list:
            self.title = title_list[0]
        # emit book_data_created signal
        self.signal('book_data_created')

    def track_list_update(self, track):
        # find existing track
        e_track = None
        for tr in self.track_list:
            if tr.get_entries(self.pl_row_id['key'])[0] == track.get_entries('pl_row_id')[0]:
                e_track = tr
                break
        if e_track == None:
            # add new track
            self.track_list.append(track)
        else:
            # modify existing track
            [e_track.set_entry(key, track.get_entries(key)) for key in track.get_key_list()]
            e_track.set_row_num(track.get_row_num())
   
    def save(self, title):
        # playlist
        pl_id = None
        con = self.db.create_connection()
        if con is None:
            return None
        try:
            cur = con.cursor()
            cur.execute("""BEGIN""")
            # add a incremented suffix to playlist title if there are duplicates
            suffix = ''
            ct = 1
            while self.db.playlist_count_duplicates(title, self.path, self.playlist_id, cur) > 0:
                title = title.rstrip(suffix)
                suffix = '_' + str(ct)
                title = title + suffix
                ct += 1
            # set book title to incremented value
            self.title = title
            # set playlist title
            if self.playlist_id is None:
                # insert the newly created playlist
                self.playlist_id = self.db.playlist_insert(title, self.path, cur)
            else:
                self.db.playlist_update(title, self.path, self.playlist_id, cur)
            if self.playlist_id is not None:
                self.title = title
                # save playlist tracks,tracks and their metadata
                for track in self.track_list:
                    track_id = self.db.track_add(path=track.get_file_path(), filename=track.get_file_name(), cur=cur)
                    pl_track_num = track.get_row_num()
                    pl_track_id = track.get_entries(self.pl_row_id['key'])[0]
                    if track_id is not None:
                        if not track.is_saved():
                            pl_track_id = self.db.playlist_track_add(self.playlist_id,
                                                                     pl_track_num,
                                                                     track_id,
                                                                     pl_track_id,
                                                                     cur)
                            track.set_saved(True)
                        else:
                            pl_track_id = self.db.playlist_track_update(self.playlist_id,
                                                                        pl_track_num,
                                                                        track_id,
                                                                        pl_track_id,
                                                                        cur)

                        track.set_entry(self.pl_row_id['key'], [pl_track_id])
                        if pl_track_id is not None:
                            for col in self.metadata_col_list:
                                
                                self.db.track_metadata_add(track_id, 
                                                           track.get_entries(col['key']),
                                                           col['key'],
                                                           pl_track_id, cur)

            self.db.playlist_track_remove_deleted(self.playlist_id, len(self.track_list), cur)
            self.saved_playlist = True

        except sqlite3.Error as e:
            print('on_playlist_save', e)
        # reload the list of playlist names saved relative to this books directory
        self.db.set_playlists_by_path(self.book_reader.cur_path, con)
        con.commit()
        con.close()
        self.track_list_sort_row_num()
        # notify any listeners that the playlist has been saved
        self.signal('book_saved')


class BookReader_View:

    def __init__(self, br_view, book_reader):
        self.br_view = br_view
        self.book_reader = book_reader
        self.outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        
        self.pinned_view = Gtk.TreeView()
        self.pinned_view.set_model(self.book_reader.pinned_list)
        # title column
        title_r = Gtk.CellRendererText()    
        title_col = Gtk.TreeViewColumn("Title")
        title_col.pack_start(title_r, True)
        title_col.add_attribute(title_r, "text", self.book_reader.pinned_title['col'])
        self.pinned_view.append_column(title_col)
        # path column
        path_r = Gtk.CellRendererText() 
        path_col = Gtk.TreeViewColumn("Location")
        path_col.pack_start(path_r, True)
        path_col.add_attribute(path_r, "text", self.book_reader.pinned_path['col'])
        self.pinned_view.append_column(path_col)
        
        
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
        self.has_new_media_box.set_child_packing(child=self.create_pl_label, expand=False, fill=False, padding=0, pack_type=Gtk.PackType.END)
        self.has_new_media_box.set_child_packing(child=self.create_pl_btn, expand=False, fill=False, padding=0, pack_type=Gtk.PackType.END)
        self.create_pl_btn.connect('button-release-event', self.on_button_release)

        self.header_box.pack_end(self.has_new_media_box, expand=False, fill=False, padding=10)

        # has_book_box notification
        self.has_book_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.has_book_box.set_no_show_all(True)
        self.has_book_box.show()
        self.open_book_btn = Gtk.Button(label='Open')
        #self.open_book_btn.show()
        self.has_book_box.pack_start(self.open_book_btn, expand=False, fill=False, padding=0)
        self.has_book_box.set_child_packing(child=self.open_book_btn, expand=False, fill=False, padding=0, pack_type=Gtk.PackType.END)
        self.cur_pl_list = Gtk.ListStore(self.book_reader.db.cur_pl_id['g_typ'], 
                                         self.book_reader.db.cur_pl_title['g_typ'],
                                         self.book_reader.db.cur_pl_path['g_typ'])

        self.has_book_combo = Gtk.ComboBox.new_with_model(self.cur_pl_list)
        renderer_text = Gtk.CellRendererText()
        self.has_book_combo.pack_start(renderer_text, True)
        self.has_book_combo.add_attribute(renderer_text, "text", self.book_reader.db.cur_pl_title['g_col'])
        self.has_book_combo.set_active(0)
        self.has_book_box.pack_start(self.has_book_combo, expand=False, fill=False, padding=0)
        self.has_book_box.set_child_packing(child=self.has_book_combo, expand=False, fill=False, padding=0, pack_type=Gtk.PackType.END)

        self.open_book_btn.connect('button-release-event', self.on_button_release)

        self.header_box.pack_end(self.has_book_box, expand=False, fill=False, padding=10)


        self.header_box.hide()      
        
        self.outer_box.pack_start(self.header_box, expand=False, fill=False, padding=0)
        self.outer_box.pack_start(self.book_reader_notebook, expand=True, fill=True, padding=0)
        
        self.br_view.pack_start(self.outer_box, expand=True, fill=True, padding=0)
        
    def on_button_release(self, btn, evt, data=None):
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
                    cols = map(lambda x: x['col'], self.book_reader.db.cur_pl_helper_l)
                    pl_row = model.get(itr, *cols)
                    self.book_reader.open_existing_book(pl_row)
    
    def on_has_new_media(self, has_new_media, user_data=None):
        if has_new_media:
            self.has_new_media_box.set_no_show_all(False)
            self.has_new_media_box.show_all()
            self.has_new_media_box.set_no_show_all(True)
        else:
            self.has_new_media_box.hide()
    
    def on_has_book(self, has_book, playlists_in_path=None):
        # model holds list of existing playlist titles
        model = self.has_book_combo.get_model()
        model.clear()
        if  has_book:
            for row in playlists_in_path:
                col = self.book_reader.db.cur_pl_title['col']
                model.append(tuple(row))
            # display option to open existing playlist
            self.has_book_box.set_no_show_all(False)
            self.has_book_box.show_all()
            self.has_book_combo.set_active(0)
            self.has_book_box.set_no_show_all(True)
        else:
            self.has_book_box.hide()

    def append_book(self, view, title):
        label = Gtk.Label(label=title[0:8])
        newpage = self.book_reader_notebook.append_page(view, label)
        self.book_reader_notebook.show_all()
        self.book_reader_notebook.set_current_page(newpage)
        # this needs to be changed we're not using the returned tuple
        return newpage, view

    def build_start_page(self):
        start_label = Gtk.Label(label="Welcome to BookEase")
        start_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        start_box.pack_start(start_label, expand=False, fill=False, padding=20)
        start_box.pack_start(self.pinned_view, expand=True, fill=True, padding=20)
        
        return start_box
        #self.add(start_box)

#TODO: make a MapList(list) class that has methods to sort based on map key and get expandable map from a map key
class BookReader_DB:
    def __init__(self, book=None):
        self.book = book
        config_dir = Path.home() / '.config' / 'book_ease'
        db_dir = config_dir / 'data'
        db_dir.mkdir(mode=511, parents=True, exist_ok=True)
        self.db = db_dir / 'book_ease.db'
        
        # playlists saved in cur dir
        self.cur_pl_id = {'col':0, 'g_typ':int, 'col_name':'id', 'g_col':0}    
        self.cur_pl_title  = {'col':1, 'g_typ':str, 'col_name':'title', 'g_col':1}
        self.cur_pl_path  = {'col':2, 'g_typ':str, 'col_name':'path', 'g_col':2}
        self.cur_pl_helper_l = [self.cur_pl_id, self.cur_pl_title, self.cur_pl_path]
        self.cur_pl_helper_l.sort(key=lambda col: col['col'])
        
        self.cur_pl_list = []
        
        self.init_tables()
        con = self.create_connection()
        if con is None:
            return None
    
    def get_cur_pl_list(self):
        return self.cur_pl_list

    def playlist_exists(self, path):
        if self.playlist_get_by_path(path) is not None:
            return True
        return False

    def set_playlists_by_path(self, path, con=None):
        pl_list = None
        if con is None:
            con = self.create_connection()
        try:
            sql = '''
                SELECT * FROM playlist
                WHERE path = ?
                '''
            cur = con.execute(sql, (path,))
            pl_list = cur.fetchall()

            # fill cur_pl_list with pl_list
            self.cur_pl_list.clear()
            for i, row in enumerate(pl_list):
                self.cur_pl_list.append(row)
                
        except sqlite3.Error as e:
            print("couldn't set_playlists_by_path", e)
        return pl_list

    def track_get_path(self, track_id):
        con = self.create_connection()
        if con is None:
            return None
        sql = """
            SELECT path FROM track
            WHERE id = (?)
            """
        try:
            cur = con.execute(sql, (track_id,))
            path = cur.fetchone()[0]
        except sqlite3.IntegrityError as e:
            path = None
            print('SELECT id FROM', md_table_name, e)
        con.close()
        return path
        


    def track_metadata_set_primary(self, primary_index, track, key, pl_track_id, cur):
        # a track metadata table
        if primary_index is not None:
            # get the id of the primary entry
            sql = """
                SELECT id FROM pl_track_metadata
                WHERE   pl_track_id = (?)
                AND     ent_index = (?)
                AND     _key = (?)
                """
            track_primary_id = None
            try:
                cur.execute(sql, (pl_track_id, primary_index, key))
                row = cur.fetchone()
                track_primary_id = None
                if row is not None:
                    track_primary_id = row['id']
            except sqlite3.IntegrityError as e:
                print('SELECT id FROM', md_table_name, e)

            # save primary entry, insert or update
            if track_primary_id is not None:
                primary_id = None
                sql = """
                    INSERT INTO primary_metadata(pl_track_id, pl_track_metadata_id, pl_track_metadata_key)
                    VALUES (?,?,?)
                    """
                try:
                    cur.execute(sql, (pl_track_id, track_primary_id, key))
                    primary_id = cur.lastrowid
                except sqlite3.IntegrityError as e:
                    print('track_metadata_add()primary_metadata error', e)
    
                if primary_id is None:
                    sql = """
                        UPDATE  primary_metadata
                        SET     pl_track_metadata_id = (?) 
                        WHERE   pl_track_id = (?)
                        AND     pl_track_metadata_key = (?)
                        """
                    try:
                        cur.execute(sql, (track_primary_id, pl_track_id, key))
                    except sqlite3.Error as e:
                        print("track_metadata_add() update error", e)
            
    def track_metadata_get(self, pl_track_id, key):
        con = self.create_connection()
        if con is None:
            return None
        #cur = con.cursor()
        sql = """
            SELECT * FROM pl_track_metadata
            WHERE pl_track_id = (?)
            AND _key = (?)
            ORDER BY
            ent_index ASC            
            """
            
        try:
            #cur.execute("""BEGIN""")
            cur = con.execute(sql, (pl_track_id,key))
            playlist = cur.fetchall()
        except sqlite3.Error as e:
            print("playlist_get_tracks() error", e)
            playlist = []
        return playlist
        
        

    def track_metadata_add(self, track_id, entries, key, pl_track_id, cur): #field = key
        if cur is None:
            return None
        #TODO: remove previous occurances of pl_track_id, _key
        #TODO: inseert new list of  pl_track_id, entry, ent_index, _key 
        sql = """
            DELETE FROM pl_track_metadata 
            WHERE pl_track_id = (?)
            AND   _key = (?)
            """
        # add each track metadata entry into its respective table
        try:
            cur.execute(sql, (pl_track_id, key))
        except sqlite3.Error as e:
            print('track_metadata_add DELETE error', e)
        try:
            if len(entries) > 0: 
                for ent_index, entry in enumerate(entries):
                    if entry is None:
                        continue
                    # pl_track metadata table
                    sql = """
                        INSERT INTO pl_track_metadata(pl_track_id, entry, ent_index, _key)
                        VALUES (?,?,?,?)
                        """
                    cur.execute(sql, (pl_track_id, entry, ent_index, key)) 
        except sqlite3.Error as e:
            print('track_metadata_add', e)
                    
    def track_add(self, path, filename, cur):
        if cur is None:
            return None
        track_id = None

        # insert track and retrieve new track_id
        sql = """
              INSERT INTO track(path, filename)
              VALUES (?,?)
              """
        try:
            cur.execute(sql, (path, filename))
            track_id = cur.lastrowid
        except sqlite3.IntegrityError as e:
            pass

        # get track id if the track was pre-existing
        if track_id is None:
            sql = """
                    SELECT id FROM track
                    WHERE path = (?)
                    AND filename = (?)
                    """
            try:
                cur.execute(sql, (path, filename))
                track_id = cur.fetchone()['id']
            except sqlite3.Error as e:
                print(e)
        return track_id

    def playlist_get_tracks(self, playlist_id):
        con = self.create_connection()
        cur = con.cursor()
        sql = """
            SELECT * FROM pl_track
            WHERE playlist_id = (?)
            ORDER BY track_number ASC
            """
        try:
            cur.execute(sql, (playlist_id,))
            playlist = cur.fetchall()
        except sqlite3.Error as e:
            print("playlist_get_tracks() error", e)
            playlist = []
        return playlist
        
        
    def playlist_get_by_path(self, path):
        con = self.create_connection()
        cur = con.cursor()
        sql = """
            SELECT * FROM playlist
            WHERE path = (?)
            """
        try:
            cur.execute(sql, (path,))
            playlist = cur.fetchall()
        except sqlite3.Error as e:
            print("playlist_get_by_path() error", e)
            playlist = []
        return playlist

    def playlist_update(self, title, path, playlist_id, cur):
        #con = sqlite3.connect(self.db)
        pl_id = None
        try:
            sql = """
                    UPDATE playlist
                    SET title = ?
                    WHERE id = ?
                    """
            cur.execute(sql, (title, playlist_id))
            pl_id = playlist_id
        except sqlite3.IntegrityError:
            print("playlist", title, "already exists at", path)
        return pl_id
    
    def create_connection(self):
        con = None
        try:
            con = sqlite3.connect(self.db, isolation_level=None) 
            con.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            print('create_connection() error', e)
        return con
        
    def playlist_track_update(self, playlist_id, track_number, track_id, _id, cur):
        if cur is None:
            return None

        lastrowid = None

        # look for what will be a duplicate track_num and change it to NULL
        sql = """
            UPDATE pl_track
            SET track_number = (?)
            WHERE playlist_id = (?)
            AND  track_number = (?)
            """
        try:
            cur.execute(sql, (None, playlist_id, track_number))
        except sqlite3.Error as e:
            print("playlist_track_add() duplicate error", e)

        success = False
        # update track
        sql = """
            UPDATE pl_track
            SET track_id = (?), track_number = (?)
            WHERE id = (?)
            """
        try:
            cur.execute(sql, (track_id, track_number, _id))
            success = True
        except sqlite3.Error as e:
            print("playlist_track_add() update error", e)

        if success:
            sql = """
                SELECT id
                FROM pl_track
                WHERE playlist_id = (?)
                AND track_number = (?)
                """
            try:
                cur.execute(sql, (playlist_id, track_number))
                row = cur.fetchone()
                if row != None:
                    lastrowid = row['id']
            except sqlite3.Error as e:
                print("playlist_track_add()update error", e)

        return lastrowid

    def playlist_track_remove_deleted(self, playlist_id, playlist_len, cur):
        if cur is None:
            return None
        sql = """
            DELETE FROM pl_track
            WHERE playlist_id = (?)
            AND (track_number >= (?) OR track_number IS NULL)
            """
        cur.execute(sql, (playlist_id, playlist_len))

    def playlist_track_add(self, playlist_id, track_number, track_id, _id, cur):
        #con = self.create_connection()
        if cur is None:
            return None
        # insert track
        sql = """
              INSERT INTO pl_track(playlist_id, track_number, track_id)
              VALUES (?,?,?)
              """
        lastrowid = None
        try:
            cur.execute(sql, (playlist_id, track_number, track_id))
            lastrowid = cur.lastrowid
        except sqlite3.IntegrityError as e:
            pass

        return lastrowid

    def playlist_insert(self, title, path, cur):
        lastrowid = None
        try:
            cur.execute("INSERT INTO playlist(title, path) VALUES (?,?)", (title, path))
            lastrowid = cur.lastrowid
        except sqlite3.IntegrityError:
            print("couldn't add", (title, path),"twice")
        return lastrowid

    def playlist_count_duplicates(self, title, path, playlist_id, cur):
        if playlist_id == None:
            playlist_id = 'NULL'

        sql = """
            SELECT COUNT(*) FROM playlist
            WHERE title = (?)
            AND path = (?)
            AND id != (?)
            """
        cur.execute(sql, (title, path, playlist_id))
        ct = cur.fetchone()
        return ct[0]

    def init_tables(self):
        con = self.create_connection()

        # Table: playlist
        sql = '''
                CREATE TABLE playlist (
                    id INTEGER PRIMARY KEY ON CONFLICT ROLLBACK AUTOINCREMENT NOT NULL,
                    title       TEXT NOT NULL,
                    path        TEXT NOT NULL,
                    UNIQUE (
                        title,
                        path
                    )
                    ON CONFLICT ROLLBACK
                )
                ''' 

        try:
            with con:
                con.execute(sql)
        except sqlite3.OperationalError as e:
            pass
        
        # Table: track
        sql = """
                CREATE TABLE track (
                    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    path     TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    UNIQUE (
                        path,
                        filename
                    )
                )
                """
        try:
            with con:
                con.execute(sql)
        except sqlite3.OperationalError:
            pass

        # Table: pl_track
        sql = """
                CREATE TABLE pl_track (
                    id INTEGER PRIMARY KEY ON CONFLICT ROLLBACK AUTOINCREMENT NOT NULL,
                    playlist_id  INTEGER REFERENCES playlist (id) 
                                        NOT NULL,
                    track_number INTEGER,
                    track_id     INTEGER NOT NULL REFERENCES track(id),
                    UNIQUE (
                        playlist_id,
                        track_number
                    )
                )
                """
        try:
            with con:
                con.execute(sql)
        except sqlite3.OperationalError:
            pass
                

        # Table: pl_track_metadata
        sql = """
                CREATE TABLE  pl_track_metadata (
                    id          INTEGER PRIMARY KEY ON CONFLICT ROLLBACK AUTOINCREMENT
                                    UNIQUE
                                    NOT NULL,
                    pl_track_id    INTEGER REFERENCES pl_track (id) 
                                    NOT NULL,
                    entry      TEXT NOT NULL,
                    ent_index      INTEGER NOT NULL,
                    _key      TEXT NOT NULL,
                    UNIQUE (
                       pl_track_id,
                       ent_index,
                       _key
                   )
                  ON CONFLICT ROLLBACK
                )
                """
 

        try:
            with con:
                con.execute(sql)
        except sqlite3.OperationalError as e:
            print("CREATE TABLE track_author exists", e)

        # primary metadata selection
        sql = """
                CREATE TABLE primary_metadata (
                    id                      INTEGER PRIMARY KEY ON CONFLICT ROLLBACK AUTOINCREMENT
                                                UNIQUE
                                                NOT NULL,
                    pl_track_id             INTEGER NOT NULL 
                                                REFERENCES pl_track (id),
                    pl_track_metadata_id    INTEGER REFERENCES pl_track_metadata (id) 
                                                NOT NULL,
                    pl_track_metadata_key   TEXT REFERENCES pl_track_metadata (_key) 
                                                NOT NULL,
                    UNIQUE (
                        pl_track_id,
                        pl_track_metadata_id,
                        pl_track_metadata_key
                    )
                    ON CONFLICT ROLLBACK
                )       
                """
        try:
            with con:
                con.execute(sql)
        except sqlite3.OperationalError:
            pass


class BookReader_:
    def __init__(self, files, config, builder):
        self.book_reader_section = 'book_reader'
        self.cur_path = None
        self.files = files
        self.config = config
        self.playlist_file = self.config['book_reader']['playlist_file']
        self.book_reader_dir = self.config['book_reader']['book_reader_dir']
        # playlists database helper
        self.db = BookReader_DB()

        # pinned playlists
        self.pinned_title = {'col':0, 'g_typ':str}  
        self.pinned_path  = {'col':1, 'g_typ':str}
        self.pinned_list = Gtk.ListStore(self.pinned_title['g_typ'], 
                                         self.pinned_path['g_typ'])

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
            self
        )
    
    def pinned_list_get(self, title, path):
        pinned_path = None
        for i , v in enumerate(self.pinned_list):
            if v[self.pinned_title['col']] == title and v[self.pinned_path['col']] == path:
                pinned_path = i
                break
        return pinned_path
    
    def pinned_list_add(self, title, path):
        for i in self.pinned_list:
            if i[self.pinned_title['col']] == title and i[self.pinned_path['col']] == path:
                return None
        return self.pinned_list.append([title, path])

    def pinned_list_remove(self, title, path):
        i = self.pinned_list.get_iter_first()
        while i != None:
            l_title, l_path = self.pinned_list.get(i, self.pinned_title['col'], self.pinned_path['col'])
            if l_title == title and l_path  == path:
                self.pinned_list.remove(i)
                break
            i = self.pinned_list.iter_next(i)

    def has_book(self, pth):
        
        br_path = os.path.join(pth, self.book_reader_dir, self.playlist_file)
        if os.path.exists(br_path):
            return True
        return False
        
    def book_updated(self, index):
        cur_pl_list=self.get_book(index)[0].get_cur_pl_list()
        self.book_reader_view.on_has_book(has_book=True, playlists_in_path=cur_pl_list)

    def get_book(self, index):
        return self.books[index]

    def remove_book(self, book_index):
        self.books.pop(book_index)
        # propogate changes to book list indices
        while book_index < len(self.books):
            self.get_book(book_index)[0].set_index(book_index)
            book_index+=1

    def on_playlist_save(self, index, title):
        bk = self.get_book(index)
        bk[0].save(title)

    def on_file_list_updated(self, get_cur_path, user_data=None):
        # conditions that need to be considered:
        # are there any media files in the directory
        # Is there a pre-existing playlist in the dir already
        # Do in View: Is there a playlist for the directory open in the bookreader view(is there an open book)
        # deal with the cache complication I created on day 1
        self.cur_path = get_cur_path()
        self.db.set_playlists_by_path(self.cur_path)
        playlists_in_path = self.db.cur_pl_list
        if len(playlists_in_path) > 0:
            self.book_reader_view.on_has_book(has_book=True, playlists_in_path=playlists_in_path)
        else:
            self.book_reader_view.on_has_book(has_book=False)

        # tell view we have files available if they are media files. offer to create new playlist
        fl = self.files.get_file_list()
        has_new_media=False
        for i in fl:
            if self.is_media_file(i[1]):
                has_new_media=True
                break
        self.book_reader_view.on_has_new_media(has_new_media)

    def append_book(self, book, view):
        index = len(self.books)
        book.set_index(index)
        self.books.append((book, view))
        return index

    def open_existing_book(self, pl_row):
        self.db
        bk = Book(self.cur_path, None, self.config, self.files, self)
        book_view = BookView.Book_View(bk, self)
        bk.connect('book_data_loaded', book_view.on_book_data_ready_th, is_sorted=True)
        bk.connect('book_saved', book_view.book_data_load_th)
        bk.page = self.book_reader_view.append_book(book_view, bk.title)
        # load the playlist metadata in background
        #load_book_data_th = Thread(target=bk.book_data_load, args={row})
        #load_book_data_th.setDaemon(True)
        #load_book_data_th.start()
        bk.book_data_load(pl_row)
        index = self.append_book(bk, book_view)
        bk.connect('book_saved', self.book_updated, index=index)

    def open_new_book(self):
        fl = self.files.get_file_list_new()
        self.files.populate_file_list(fl, self.cur_path)
        bk = Book(self.cur_path, fl, self.config, self.files, self)
        book_view = BookView.Book_View(bk, self)
        bk.connect('book_data_created', book_view.on_book_data_ready_th, is_sorted=False)
        bk.connect('book_saved', book_view.book_data_load_th)
        bk.page = self.book_reader_view.append_book(book_view, bk.title)
        # load the playlist metadata in background
        create_book_data_th = Thread(target=bk.create_book_data, args={book_view.on_book_data_ready_th})
        create_book_data_th.setDaemon(True)
        create_book_data_th.start()
        index = self.append_book(bk, book_view)
        bk.connect('book_saved', self.book_updated, index=index)
        self.book_reader_view.on_has_new_media(False)

    def is_media_file(self, file):
        for i in self.f_type_re:
            if i.match(file):
                return True
        return False

    def close_book(self, books_index):
        self.remove_book(books_index)
        # close the bookview
        bk, bv = self.get_book(books_index)
        bv.close()

    def book_editing_cancelled(self, books_index):
        bk, bv = self.get_book(books_index)
        if bk.is_saved():
            # clear the tracklist and reload from DB
            pl_row = bk.get_cur_pl_row()
            bk.clear_track_list()
            bk.db.set_playlists_by_path(bk.path)
            bk.book_data_load(pl_row)
        else:
            # close the playlist
            self.close_book(books_index)


class Files_(signal_.Signal_):
    def __init__(self, config):
        signal_.Signal_.__init__(self)
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
        self.icon_pos, self.f_name_pos, self.is_dir_pos, self.f_size_pos, self.f_units_pos, self.ctime_pos = (0, 1, 2, 3, 4, 5)

        # Signals
        # Notify of file changes
        self.add_signal('file_list_updated')
        # populate the file_list
        self.__update_file_list()
    
    def __update_file_list(self):
        self.file_list.clear() 
        self.populate_file_list(self.file_list, self.current_path)
        # notify subscribers that the file list has been updated
        self.signal('file_list_updated')
                
    def get_file_list_new(self):
            fl = Gtk.ListStore(Pixbuf, str, bool, str, str, str)
            return fl
            
    def populate_file_list(self, file_list, path):
        fl = file_list
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
            fl.append([icon, i.name, i.is_dir(), size_f, units, str(timestamp_formatted)])
        

    def get_file_list(self):
        return self.file_list
    
    # callback signaled by Files_View   
    def cmp_f_list_dir_fst(self, model, row1, row2, user_data=None):
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
            elif not is_dir_1 and is_dir_2:
                return 1 * direction

        if name1 < name2:
            return -1
        elif name1 == name2:
            return 0
        else:
            return 1

    # convert filesize to string with appropriate units     
    def format_f_size(self, size):
        units = 'b'
        length = len("{:.0f}".format(size))
        if length <= 3:
            val = str(size)
        elif length <= 6:
            val = "{:.1f}".format(size / 10e+2)
            units = 'kb'
        elif length <= 9:
            val = "{:.1f}".format(size / 10e+5)
            units = 'mb'
        elif length <= 12:
            val = "{:.1f}".format(size / 10e+8)
            units = 'gb'
        else:
            val = "{:.1f}".format(size / 10e+11)
            units = 'tb'
        return (val, units)
    
    def append_to_path_back(self):
        if len(self.path_back) >= self.path_back_max_len:
            self.path_back.pop(0)
        self.path_back.append(self.current_path)
        
    def append_to_path_ahead(self):
        if len(self.path_ahead) >= self.path_ahead_max_len:
            self.path_ahead.pop(0)
        self.path_ahead.append(self.current_path)
        
        
    def get_path_current(self):
        return self.current_path

    def cd(self, path):
        if os.path.isdir(path):
            self.append_to_path_back()
            self.path_ahead.clear()
            self.current_path = path
            self.__update_file_list()
        
    def cd_ahead(self):
        if len(self.path_ahead) > 0:
            path = self.path_ahead.pop()            
            if os.path.isdir(path):
                self.append_to_path_back()
                self.current_path = path
                self.__update_file_list()
            else:
                self.path_ahead.append(path)
            
    def cd_up(self):
        if os.path.isdir(path):
            self.append_to_path_back()
            self.cd(os.path.split(self.get_path_current())[0])
            self.__update_file_list()
        
    def cd_previous(self):
        if len(self.path_back) > 0: 
            path = self.path_back.pop()
            if os.path.isdir(path):
                self.append_to_path_ahead()
                self.current_path = path
                self.__update_file_list()
            else:
                elf.path_back.append(path)

    def is_hidden_file(self, file_name):
        valid = re.compile(r"^[\.]")
        if valid.match(file_name):
            return True
        return False 


class Files_View:
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
        
    def on_button_release(self, button, event):
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
        name_width_config = int(self.config[self.config_section_name]['column_width_name'])
        name_width = self.name_col.get_width()
        if name_width_config != name_width:
            self.config.set(self.config_section_name, 'column_width_name', str(name_width))
        
    def row_activated(self, treeview, path, column, user_data=None):
        model = treeview.get_model()
        tree_iter = model.get_iter(path)
        value = model.get_value(tree_iter,1)
        is_dir = model.get_value(tree_iter,2)
        if is_dir:
            # cd into selected dir
            new_path = os.path.join(self.files.get_path_current(), value)
            self.files.cd(new_path)
    
class MainWindow(Gtk.Window):
    
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
        try:
            self.file_manager_pane_pos = self.config['book_reader_window'].getint('file_manager_pane_pos') 
            self.file_manager_pane.set_position(int(self.file_manager_pane_pos))
        except Exception as e:
            print(e)
        # book_reader_pane
        self.book_reader_pane = builder.get_object("book_reader_pane")
        try:
            self.book_reader_pane_pos = self.config['book_reader_window'].getint('book_reader_pane_pos') 
            self.book_reader_pane.set_position(int(self.book_reader_pane_pos))
        except Exception as e:
            print(e)
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

    
    def on_delete_event(self, widget, val, window=None):
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


    def on_destroy(self, *args):
        Gtk.main_quit()

    def on_visibility_switch_changed(self, sw, state, user_data=None):
        if sw.get_name() == 'show_files_switch1':
            if state:
                self.file_manager1.show()
            else:
                self.file_manager1.hide()
        elif sw.get_name() == 'show_files_switch2':
            if state:
                self.file_manager2.show()
            else:
                self.file_manager2.hide()
        elif sw.get_name() == 'show_playlist_switch':
            if state:
                self.book_reader_view.show()
            else:
                self.book_reader_view.hide()
        elif sw.get_name() == 'show_image_switch':
            if state:
                self.image_view.show()
            else:
                self.image_view.hide()
        
        # deal with the parent panes needing to be hidden
        if (not self.image_view.get_visible() and not self.book_reader_view.get_visible()) and self.book_reader_pane.get_visible():
            self.book_reader_pane.hide()
        elif (self.image_view.get_visible() or self.book_reader_view.get_visible()) and not self.book_reader_pane.get_visible():
            self.book_reader_pane.show()
        elif (not self.file_manager1.get_visible() and not self.file_manager2.get_visible()) and self.file_manager_pane.get_visible():
            self.file_manager_pane.hide()
        elif (self.file_manager1.get_visible() or self.file_manager2.get_visible()) and not self.file_manager_pane.get_visible():
            self.file_manager_pane.show()
        
def main(args):
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
    files_view_1 = Files_View(builder.get_object("files_1"),
                              files,
                              config)    
    # left side bookmarks
    bookmark_view_1 = BookMark(builder.get_object("bookmarks_1"), 
                               files_view_1,
                               files,
                               config)      
    # image pane
    image_view_1 = Image_View(builder.get_object("image_view"), 
                              files,
                              config,
                              builder)     
    # vlc interface
    player = media_player(config)
    # bookreader backend
    book_reader = BookReader_(files, config, builder)

    # main window 
    window = MainWindow(builder.get_object("window1"),
                        builder.get_object("window_1_pane"),
                        config,
                        builder)
        
    Gtk.main()
    # write any changes to the config
    with open(config_file, 'w') as configfile:
        config.write(configfile)

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
