# General libraries
import numpy as np
import pandas as PD
from sys import exit
from mne.io import read_raw_edf
from pyedflib.highlevel import read_edf_header

# CNT/EEG Specific
from ieeg.auth import Session

# Import the add on classes
from modules.addons.data_loader import *
from modules.addons.channel_clean import *
from modules.addons.channel_mapping import *
from modules.addons.channel_montage import *
from modules.addons.preprocessing import *
from modules.addons.features import *

# Import the core classes
from modules.core.metadata_handler import *
from modules.core.target_loader import *
from modules.core.dataframe_manager import *
from modules.core.output_manager import *
from modules.core.data_viability import *

class data_loader_test:

    def __init__(self):
        pass

    def edf_test(self,infile):
        try:
            read_edf_header(infile)
            return (True,)
        except Exception as e:
            return (False,e)

class data_loader:
    """
    Class devoted to loading in raw data into the shared class instance.

    New functions should make use of the specific raw data handler for their dataset.
    """

    def __init__(self):
        pass

    def pipeline(self):
        """
        Method for working within the larger pipeline environment to load data.

        Args:
            filetype (str): filetype to read in (i.e. edf/mef/etc.)

        Returns:
            bool: Flag if data loaded correctly
        """
        
        # Logic gate for filetyping, returns if load succeeded
        flag = self.data_loader_logic(self.args.datatype)

        if flag:
            # Create the metadata handler
            metadata_handler.highlevel_info(self)

            # Save the channel names
            self.channels = [ichannel.upper() for ichannel in self.channels]
            metadata_handler.set_channels(self,self.channels)

            # Calculate the sample frequencies to save the information and make time cuts
            sample_frequency = np.array([self.sfreq for ichannel in self.channel_metadata])
            metadata_handler.set_sampling_frequency(self,sample_frequency)

            # Get the rawdata
            self.raw_dataslice(sample_frequency,majoraxis='column')

            return True
        else:
            return False

    def direct_inputs(self,infile,filetype):
        """
        Method for loading data directly outside of the pipeline environment.

        Args:
            infile (str): Path to the file to read in.
            filetype (str): filetype to read in (i.e. edf/mef/etc.)

        Returns:
            bool: Flag if data loaded correctly
        """

        # Define some instance variables needed to work within this pipeline
        self.infile  = infile
        self.oldfile = '' 

        # Try to load data
        flag = self.data_loader_logic(filetype)

        if flag:
            sample_frequency = np.array([self.sfreq for ichannel in self.channel_metadata])
            return PD.DataFrame(self.indata,columns=self.channels),sample_frequency[0]
        else:
            print("Unable to read in %s." %(self.infile))
            return None,None

    def raw_dataslice(self,sample_frequency,majoraxis='column'):
        """
        Logic for cutting the data up by time slices. Doing so at the beginning reduces memory load.

        Args:
            sample_frequency (int): Sampling frequency of the data
            majoraxis (str, optional): Orientation of the time vectors. Defaults to 'column'.
        """

        # Get only the time slices of interest
        self.raw_data = []
        for ii,isamp in enumerate(sample_frequency):
            
            # Calculate the index of the start
            samp_start = int(isamp*self.t_start)

            # Calculate the index of the end
            if self.t_end == -1:
                samp_end = int(len(self.indata[ii]))
            else:
                samp_end = int(isamp*self.t_end)

            if majoraxis == 'column':
                self.raw_data.append(self.indata[samp_start:samp_end,ii])
            elif majoraxis == 'row':
                self.raw_data.append(self.indata[ii][samp_start:samp_end])

        # Get the underlying data shapes
        self.ncol = len(self.raw_data)
        self.nrow = max([ival.size for ival in self.raw_data])        


    ###################################
    #### User Provided Logic Below ####
    ###################################

    def data_loader_logic(self, filetype):
        """
        Update this function for the pipeline and direct handler to find new functions.

        Args:
            filetype (str): filetype to read in (i.e. edf/mef/etc.)

        Returns:
            bool: Flag if data loaded correctly
        """
        
        if filetype.lower() == 'edf':
            flag = self.load_edf()
        return flag

    def load_edf(self):
        """
        Load EDF data directly into the pipeline.
        """
 
        # Load current edf data into memory
        if self.infile != self.oldfile:
            try:
                # Read in the data via mne backend
                raw           = read_raw_edf(self.infile,verbose=False)
                self.indata   = raw.get_data().T
                self.channels = raw.ch_names
                self.sfreq    = raw.info.get('sfreq')

                # Keep a static copy of the channels so we can just reference this when using the same input data
                self.channel_metadata = self.channels.copy()
                return True
            except OSError:
                return False
        else:
            self.channels = [ival for ival in self.channel_metadata]
            return True

    def load_iEEG(self,username,password,dataset_name):

        # Load current data into memory
        if self.infile != self.oldfile:
            with Session(username,password) as session:
                dataset     = session.open_dataset(dataset_name)
                channels    = dataset.ch_labels
                self.indata = dataset.get_data(0,np.inf,range(len(channels)))
            session.close_dataset(dataset_name)
        
        # Save the channel names to metadata
        self.channels = channels
        metadata_handler.set_channels(self,self.chanels)
        
        # Calculate the sample frequencies
        sample_frequency = [dataset.get_time_series_details(ichannel).sample_rate for ichannel in self.channels]
        metadata_handler.set_sampling_frequency(self,sample_frequency)



