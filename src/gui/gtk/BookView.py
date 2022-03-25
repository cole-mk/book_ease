import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
import playlist

class Edit_Row_Dialog:

    def __init__(self, row, g_col, book_view, track_edit_list, model):
        self.row = row
        self.selected_col = None
        for i in book_view.display_cols:
            if i['name'] == g_col.get_title():
                self.selected_col = i
                break
        self.book_view = book_view
        self.track_edit_list = track_edit_list
        self.track_edit_list_tmp = []
        self.model = model
        itr = self.model.get_iter(row)
        self.pl_row_id = self.model.get_value(itr, self.book_view.book.pl_row_id['col'])

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
        val_list = []
        for i in self.col_tv_model:
            val_list.append(i[0])
        if len(val_list) > 0:
            # get existing entry or create now one and 
            # add it to the track_edit_list_tmp
            existing_edit = False
            for edt in self.track_edit_list_tmp:
                if self.pl_row_id in edt.get_entries(self.book_view.book.pl_row_id['key']):
                    edit = edt
                    existing_edit = True
                    break

            if not existing_edit:
                edit = playlist.Track_Edit(self.selected_col)
                self.track_edit_list_tmp.append(edit)

            edit.set_entry(edit.col_info['key'], val_list)
            edit.set_entry(self.book_view.book.pl_row_id['key'], [self.pl_row_id])

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
        new_values = self.book_view.book.get_track_entries(self.pl_row_id, self.selected_col)
        for i in self.book_view.book.get_track_alt_entries(self.pl_row_id, self.selected_col):
            if not i in new_values:
                new_values.append(i)
        for i in new_values:
            self.new_value_model.append([i])

        # load treeview with entries
        self.col_tv_model.clear()
        itr = self.model.get_iter(self.row)
        row_id = self.model.get_value(itr, self.book_view.book.pl_row_id['col'])
        # look for unsaved changes from this dialog first
        unsaved_changes = False
        for i in self.track_edit_list_tmp:
            if i.col_info == self.selected_col:
                unsaved_changes = True
                for x in i.get_entries(self.selected_col['key']):
                    self.col_tv_model.append([x])
                break
        # look for unsaved changes from previous dialog
        if not unsaved_changes:
            for i in self.track_edit_list:
                i_id = i.get_entries(self.book_view.book.pl_row_id['key'])[0]
                if i_id == row_id and i.col_info == self.selected_col:
                    unsaved_changes = True
                    for x in i.get_entries(self.selected_col['key']):
                        self.col_tv_model.append([x])
                    break
        # load saved entries from book track
        if not unsaved_changes:
            for i in self.book_view.book.get_track_entries(row_id, self.selected_col):
                self.col_tv_model.append([i])
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
            self.set_selected_col(combo.get_active_text())
            self.set_active_column(combo.get_active_text())
        

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

    def __init__(self, book):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.book = book
        self.notebook = self.book.book_reader.book_reader_view.book_reader_notebook
        self.book_reader = self.book.book_reader
        self.editing = None
        # store playlist edits until user saves playlist
        self.track_edit_list = self.book.track_edit_list
        self.playlist = self.get_playlist_new()
        self.playlist_old = self.get_playlist_new()
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
        self.pinned_button = Gtk.CheckButton(label='pin')
        self.pinned_button.connect('toggled', self.on_button_toggled)
        self.header_box.pack_start(self.pinned_button, expand=False, fill=False, padding=0)
        self.title_label = Gtk.Label(label=self.book.title)
        self.title_label.set_no_show_all(True)
        self.title_label.set_halign(Gtk.Align.END)
        self.header_box.pack_start(self.title_label, expand=True, fill=True, padding=0)
        title_store = Gtk.ListStore(self.book.pl_title['g_typ'])
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


        self.display_cols = [self.book.pl_track,
                        self.book.pl_title,
                        self.book.pl_author,
                        self.book.pl_read_by,
                        self.book.pl_length,
                        self.book.pl_file]

        self.col_to_renderer_map = {}   
        for i in self.display_cols:
            rend = Gtk.CellRendererCombo()
            rend.set_property("text-column",0 ) #0 i['col']
            rend.set_property("editable", True)
            rend.set_property("has-entry", False)
            rend.set_property("model", Gtk.ListStore(i['g_typ']))
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
        self.default_sort_col =  (self.playlist_tree_view.get_column(self.display_cols.index(self.book.pl_track)),
                                  self.book.pl_track['col'])
        self.default_sort_col[0].set_sort_order(Gtk.SortType.DESCENDING)
        self.old_sort_order = Gtk.SortType.DESCENDING

    def get_playlist(self):
        return self.playlist
        
    def get_playlist_new(self):
        return Gtk.ListStore(self.book.pl_title   ['g_typ'], 
                             self.book.pl_author  ['g_typ'], 
                             self.book.pl_read_by ['g_typ'], 
                             self.book.pl_length  ['g_typ'],
                             self.book.pl_track   ['g_typ'],
                             self.book.pl_file    ['g_typ'],
                             self.book.pl_row_id  ['g_typ'],
                             self.book.pl_path    ['g_typ'])

    def on_button_toggled(self,btn):
        if btn.get_active():
            self.book_reader.pinned_list_add(self.book.title, self.book.path)
        else:
            self.book_reader.pinned_list_remove(self.book.title, self.book.path)
    
    def on_editing_cancelled(self, renderer):
        m = renderer.get_property('model')
        m.clear()
    
    def on_editing_started(self, renderer, editable, path, col):
        # build the dropdown menu with suggestions
        m = editable.get_model()
        itr = self.playlist.get_iter(path)
        pl_row_id = self.playlist.get_value(itr, self.book.pl_row_id['col'])
        # the list of combo entries
        titles = []
        # check first for pending changes to add
        pending_changes = False
        for entry in self.track_edit_list:
            if entry.get_entries('pl_row_id')[0] == pl_row_id and col['key'] in entry.get_key_list():
                for val in entry.get_entries(col['key']):
                    titles.append(val)
                    pending_changes = True
                    break
        if not pending_changes:     
            # append track entries to list
            for x in self.book.get_track_entries(pl_row_id, col):
                if x:
                    titles.append(x)
        # append the list to the combo model
        for x in titles:
            if x:
                m.append([x])
            
    def on_edited(self, renderer, path, text, col):
        # propagate changes to self.playlist and end editing
        self.playlist[path][col['col']] = text
        model = renderer.get_property('model')
        if self.editing == True :
            val_list = []
            val_list.append(text)
            # move selected text to front of list, skip once selected text in list, but do add duplicates
            matched = False
            for i in model:
                if matched == False and i[0] == text:
                    matched = True
                    continue
                val_list.append(i[0])
            if len(val_list) > 0:
                row_id = self.playlist[path][self.book.pl_row_id['col']]
                edit = playlist.Track_Edit(col)
                edit.set_entry(col['key'], val_list)
                edit.set_entry(self.book.pl_row_id['key'], [row_id]) 
                self.book.track_edit_list_append(edit)
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
                        dialog = Edit_Row_Dialog(pth, col, self, self.track_edit_list, self.playlist)
                        response = dialog.run()
                        if response == Gtk.ResponseType.OK:
                            # load the changes from the dialog into the books edit list
                            for edit in dialog.track_edit_list_tmp:
                                self.book.track_edit_list_append(edit)
                                # set value in tree view to pirmary entry
                                for j, row in enumerate(self.playlist):
                                    if edit.get_entries(self.book.pl_row_id['key'])[0] == row[self.book.pl_row_id['col']]:
                                        itr = self.playlist.get_iter((j,))
                                        self.playlist.set_value(itr, edit.col_info['col'], edit.get_entries(edit.col_info['key'])[0])
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
        sorted_model.set_sort_func(self.book.pl_track['col'], self.cmp_str_as_num, None)

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
        
    def playlist_restore(self):
        self.playlist.clear()
        for i in self.playlist_old:
            self.playlist.append(tuple(i))
                    
    def playlist_save(self):
        # apply pending changes
        old_t = self.book.title
        old_p = self.book.path
        # new book title
        entry = self.title_combo.get_child()
        title = entry.get_text()
        self.title_label.set_text(title)
        self.book.on_playlist_save(title)
        # check for changes that need to be applied to the pinned list
        if(self.book_reader.pinned_list_get(old_t, old_p) is not None):
            self.book_reader.pinned_list_remove(old_t, old_p)
            self.book_reader.pinned_list_add(self.book.title, self.book.path)
        
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
            p_val = tv_model.get_value(itr, self.book.pl_title['col'])
            # make sure selected_val isnt a duplicate
            match = False
            for i in title_store:
                if i[0] == p_val:
                    match = True
                    break
            if not match:
                title_store.append([p_val])
            
            # append to title_store each val in metadata value list for each p
            pl_row_id = tv_model.get_value(itr, self.book.pl_row_id['col'])
            for meta_val in self.book.get_track_entries(pl_row_id, self.book.pl_title):
                match = False
                # make sure meta_val isnt a duplicate
                for i in title_store:
                    if i[0] == meta_val:
                        match = True
                        break
                if not match:
                    title_store.append([meta_val])
    
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
                self.playlist_restore()
                self.track_edit_list.clear()
            elif btn == self.edit_button:
                self.playlist_backup()
                self.playlist_set_edit(True)
    
    def on_row_deleted(self, a, b):
        cols = self.playlist_tree_view.get_columns()
        for i in cols:
            i.set_sort_indicator(False)
        
    def remove_all_children(self):
        widgits = self.get_children()
        for i in widgits:
            self.remove(i)
        
    def on_book_data_ready(self):
        playlist = self.book.get_track_list()
        if playlist:
            if len(playlist) > 0:

                # do the appending
                self.playlist.clear()
                playlist = self.book.get_track_list()
                for i, track in enumerate(playlist):
                    cur_row = self.playlist.append()
                    # append entries for each in list of displayed columns
                    for col in self.display_cols:
                        # get first primary entry
                        val = self.book.get_track_entries(i, col)[0]
                        self.playlist.set_value(cur_row, col['col'], val)

                    # the utility collumns always have a primary entry
                    self.playlist.set_value(cur_row, self.book.pl_row_id['col'],
                                   track.get_entries(self.book.pl_row_id['key'])[0])
                    
                    self.playlist.set_value(cur_row, self.book.pl_path['col'],
                                   track.get_entries('path')[0])

                # load the new gui
                self.remove_all_children()
                self.pack_start(self.header_box, expand=False, fill=False, padding=0)
                self.pack_start(self.scrolled_playlist_view, expand=True, fill=True, padding=0)
                #set default sort order for the playlist
                self.sort_by_column(self.default_sort_col[0], self.default_sort_col[1]) 
                #self.title_entry.set_text(self.book.title)
                self.title_label.set_label(self.book.title)
                self.show_all()
                self.notebook.set_tab_label_text(self, self.book.title[0:8])
                # show editing buttons
                #self.edit_playlist_box.set_no_show_all(False)
                self.playlist_backup()
                self.playlist_set_edit(True)
                self.edit_playlist_box.show()
                #self.edit_playlist_box.set_no_show_all(True)
                #self.cancel_button.show()
