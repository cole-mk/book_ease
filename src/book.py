# -*- coding: utf-8 -*-
#
#  book.py
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
        self.db = Book_DB()
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

    def get_playlist_id(self):
        """get this book instance's unique id"""
        return self.playlist_id

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
        self.db.set_cur_pl_list_by_path(self.book_reader.cur_path, con)
        con.commit()
        con.close()
        self.track_list_sort_row_num()
        # notify any listeners that the playlist has been saved
        self.signal('book_saved')
