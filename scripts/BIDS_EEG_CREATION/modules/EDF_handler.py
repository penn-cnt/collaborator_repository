from sys import exit
from mne.io import read_raw_edf
from pyedflib.highlevel import read_edf_header

# Local imports
from modules.BIDS_handler import BIDS_handler

class EDF_handler(BIDS_handler):

    def __init__(self,args,map_data,input_files):
        self.args         = args
        self.map_data     = map_data
        self.input_files  = input_files
        self.subject_path = args.bidsroot+args.subject_file
    
    def save_data(self):
        for ii,self.current_file in enumerate(self.input_files):
            self.uid    = self.map_data['uid'].values[ii]
            self.target = self.map_data['target'].values[ii] 
            flag        = self.edf_test()
            if flag:
                BIDS_handler.__init__(self)
                self.read_edf()
                BIDS_handler.get_channel_type(self)
                BIDS_handler.make_info(self)
                BIDS_handler.add_raw(self)

        # Save the bids files if we have any data
        BIDS_handler.save_bids(self)

    def edf_test(self):
        try:
            read_edf_header(self.current_file)
            return True
        except Exception as e:
            return False

    def read_edf(self):

        # Read in the data via mne backend
        raw           = read_raw_edf(self.current_file,verbose=False)
        self.data     = raw.get_data().T
        self.channels = raw.ch_names
        self.fs       = raw.info.get('sfreq')