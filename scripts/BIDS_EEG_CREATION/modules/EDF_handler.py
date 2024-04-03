from sys import exit
from mne.io import read_raw_edf
from pyedflib.highlevel import read_edf_header

# Local imports
from modules.BIDS_handler import BIDS_handler

class EDF_handler(BIDS_handler):

    def __init__(self,args,input_data):
        self.args              = args
        self.input_data        = input_data
        self.input_files       = input_data['orig_filename'].values
        self.all_proposed_subs = input_data['proposed_subnum']
        self.subject_path      = args.bidsroot+args.subject_file
        self.old_uid           = -999
        self.write_lock        = None
    
    def save_data(self):
        for ii,self.current_file in enumerate(self.input_files):
            self.file_idx     = ii
            self.uid          = self.input_data['uid'].values[ii]
            self.target       = self.input_data['target'].values[ii]
            self.proposed_sub = self.all_proposed_subs[ii]
            flag        = self.edf_test()
            if self.uid != self.old_uid:
                BIDS_handler.__init__(self)
                self.old_uid = self.uid
            if flag:
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