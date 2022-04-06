import mutagen


class Track:
    def __init__(self, file_path=None, row_num=None, is_saved=False):
        self.track_data = {}
        if file_path is not None:
            self.file_path = file_path
            self._file = file_path.rsplit('/', maxsplit=1)[1]
            self.track_data['file'] = [self._file]
            self.track_data['path'] = [file_path]
        self.row_num = row_num
        self.saved = is_saved
        #self.load_metadata_from_file(self.track_data)

    def is_saved(self):
        return self.saved

    def set_saved(self, is_saved):
        self.saved = is_saved

    def set_row_num(self, row_num):
        self.row_num = row_num

    def get_row_num(self):
        return self.row_num
    
    def get_key_list(self):
        key_list = []
        for key in self.track_data:
            key_list.append(key)
        if len(key_list) <= 0:
            key_list.append(None)
        return key_list
    
    def get_primary_entry(self, key):
        primary_entry = None
        if key in self.track_data:
            #primary_entry = self.track_data[key][0]
            primary_entry = 0
        return primary_entry
    
    def load_metadata_from_file(self):
        metadata = mutagen.File(self.file_path, easy=True)
        for key in metadata:
            if key == 'tracknumber':
                entry_list_f = []
                for entry in metadata[key]:
                    entry_list_f.append(self.format_track_num(entry))
                self.track_data[key] = entry_list_f
            else:
                self.track_data[key] = metadata[key]     

    def set_entry(self, key, entries):
        if type(entries) is not list:
            raise TypeError ( entries, 'is not a list' )
        self.track_data[key] = entries
        
            
    def get_entries(self, key):
        # return a list of all the entries in trackdata[key]
        entries = []
        if key is not None:
            if key in self.track_data:
                for entry in self.track_data[key]:
                    entries.append(entry)
        if len(entries) <= 0:
            entries.append(None)
        return entries
        
    def get_file_name(self):
        return self._file

    def get_file_path(self):
        return self.file_path

    def format_track_num(self, track):
        return track.split('/')[0]


class Playlist():
    
    def __init__(self):
        print('Playlist():')
        self.track_list = []
        self.saved_playlist = False

    def clear_track_list(self):
        self.track_list.clear()

    def is_saved(self):
        return self.saved_playlist

    def set_saved(self, _bool):
        self.saved_playlist = _bool

    def get_track_list(self):
        return self.track_list

    def get_track_entries(self, row, col):
        track = None
        for tr in self.track_list:
            if tr.get_entries(self.pl_row_id['key'])[0] == row:
               track = tr
               break
        if track != None:
            return track.get_entries(col['key'])
        return [None]

    def get_track_alt_entries(self, row, col):
        lst = []
        track = None
        for tr in self.track_list:
            if tr.get_entries(self.pl_row_id['key'])[0] == row:
               track = tr
               break
        if track != None:
            for key in col['alt_keys']:
                for entry in track.get_entries(key):
                    if entry is not None:
                        lst.append(entry)
        return lst

    def track_list_sort_row_num(self):
        self.track_list.sort(key=lambda row: row.row_num)

class Track_Edit(Track):
    
    def __init__(self, col_info):
        super().__init__()
        # The description column(python map obj) created in the book obj
        self.col_info = col_info





