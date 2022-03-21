import mutagen


class Track_Edit:
    
    def __init__(self, col_info, pl_row_id=None, val_list=None):
        #TODO: refactor self.col_info to a more fitting name
        # The description column(python map obj) created in the book obj
        self.col_info = col_info
        # unique id for a track
        self.pl_row_id = pl_row_id
        # list of maps containing track data
        if type(val_list) == list:
            self.val_list = val_list
        else:
            raise TypeError ('type(val_list) == type(self.val_list)')


class Track:
    def __init__(self, file_path):
        self.file_path = file_path
        self._file = file_path.rsplit('/', maxsplit=1)[1]
        self.track_data = {'file':[self._file], 'path':[file_path]}
        #self.load_metadata_from_file(self.track_data)

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
        self.track_edit_list = []
        self.track_list = []

    def track_edit_list_append(self, track_edit):
        # remove old entry
        for j in self.track_edit_list:
            if j.col_info == track_edit.col_info:
                self.track_edit_list.remove(j)
                break
        # add new entry
        self.track_edit_list.append(track_edit)
        for x in self.track_edit_list:
            print('x in self.track_edit_list:', x.val_list)

    def get_track_list(self):
        return self.track_list

    def get_track_entries(self, row, col):
        track = self.track_list[row]
        return track.get_entries(col['key'])

    def get_track_alt_entries(self, row, col):
        lst = []
        track = self.track_list[row]
        for key in col['alt_keys']:
            for entry in track.get_entries(key):
                if entry is not None:
                    lst.append(entry)
        return lst






