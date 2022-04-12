import unittest
from playlist import Track


class Track_Set_Entry(unittest.TestCase):

    def setUp(self):
        self.tr = Track()
        
    def tearDown(self):
        del self.tr

    def test_key_not_list(self):
        # assert that set_entry raises exception when entries is not a list
        self.assertRaises(TypeError, self.tr.set_entry,'artist', 'test_data')

    def test_new_key(self):
        # assert that set_entry is able to create a new entry
        self.tr.set_entry('artist', ['test_data1', 'test_data2'])
        self.assertIn('test_data1', self.tr.get_entries('artist'))

    def test_replace_key(self):
        # assert that set_entry replaces old data with new when key already exists
        self.tr.set_entry('artist', ['test_data1', 'test_data2'])
        self.tr.set_entry('artist', ['test_data3', 'test_data4'])
        self.assertNotIn('test_data1', self.tr.get_entries('artist'))
        self.assertNotIn('test_data2', self.tr.get_entries('artist'))
        self.assertIn('test_data3', self.tr.get_entries('artist'))
        self.assertIn('test_data4', self.tr.get_entries('artist'))


class Track_Load_Metadata_From_File(unittest.TestCase):

    def setUp(self):
        self.tr = Track(file_path='test/test_track.mp3')

    def tearDown(self):
        del self.tr

    def test_file_has_metadata(self):
        # assert that load_metadata_from_file correctly copies data from mp3 to the track
        # depends on other functions in track working correctly
        self.tr.load_metadata_from_file()
        key_l = self.tr.get_key_list()
        self.assertIn('artist', self.tr.get_key_list())
        self.assertEqual(self.tr.get_entries('artist'), ['test name'])
        self.assertIn('title', self.tr.get_key_list())
        self.assertEqual(self.tr.get_entries('title'), ['test title'])
        self.assertIn('tracknumber', self.tr.get_key_list())
        self.assertEqual(self.tr.get_entries('tracknumber'), ['1'])


class Track_Get_Key_List(unittest.TestCase):

    def setUp(self):
        self.tr = Track()

    def tearDown(self):
        del self.tr

    def test_keys_found(self):
        # assert that get_key_list() returns correct list of keys as strings
        self.tr.track_data['test1'] = ['test one', 'test two']
        self.tr.track_data['test2'] = ['test three', 'test four']
        key_l = self.tr.get_key_list()
        self.assertIsInstance(key_l, list) 
        self.assertIsInstance(key_l[0], str)        
        self.assertIn('test1', self.tr.get_key_list())
        self.assertIn('test2', self.tr.get_key_list())

    def test_keys_not_found(self):
        # asserrt that get_key_list() returns empty list when no key is found
        key_l = self.tr.get_key_list()
        self.assertIsInstance(key_l, list)
        self.assertEqual(len(key_l), 0) 


class Track_Format_Track_Num(unittest.TestCase):

    def setUp(self):
        self.tr = Track()
    
    def tearDown(self):
        del self.tr

    def test_None(self):
        # assert that format_track_num raises an exception when given
        # input not of type that supports python split method
        self.assertRaises(AttributeError, self.tr.format_track_num, None)

    def test_track_num_in_numerator(self):
        # assert that format_track_num returns correct track number
        # when track number input is string and number is in numerator  
        num = '2/3/15'
        self.assertEqual(self.tr.format_track_num(num), '2')
        

class Track_Get_Entries(unittest.TestCase):

    ## method that runs once for this class
    #@classmethod
    #def setUpClass(cls):
    #    pass
    #
    ## method that runs once for this class
    #@classmethod
    #def tearDownClass(cls):
    #    pass

    def setUp(self):
        self.tr = Track()
        
    def tearDown(self):
        del self.tr

    def test_None_key(self):
        # assert that Track.get_entries returns empty list
        # when method is passed a key of None type
        response = self.tr.get_entries(None)
        self.assertIsInstance(response, list)
        self.assertEqual(len(response), 0)
        
    def test_entry_exists(self):
        # test track.get_entries under what are presumed to be normal conditions
        # where passed key is not None and entry exists  as a list in the track_data map
        self.tr.set_entry('test', ['test one', 'test two'])
        response = self.tr.get_entries('test')
        self.assertIsInstance(response, list)
        self.assertEqual(response[0], 'test one')
        self.assertEqual(response[1], 'test two')

    def test_entry_does_not_exist(self):
        # test track.get_entries returns an empty list
        # when the passed key is not None and entry does not exist 
        # in the track_data map
        response = self.tr.get_entries('test')
        self.assertIsInstance(response, list)
        self.assertEqual(len(response), 0)	


if __name__ == '__main__':
    unittest.main()

