# General libraries
import numpy as np
import pandas as PD

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

class channel_mapping:
    """
    Class devoted to the different channel mappings of interest. 

    New functions should look for the cross section of their mapping to the self.clean_channel_map data.

    Output should be a new list of channels called self.channel_map_out. Also required are the indices of intersection. (This is to update the metadata properly)
    """

    def __init__(self):
        """
        Logic gates for which channel mapping methodology to use.

        Args:
            clean_method (str, optional): Mapping method to use, see --help for complete list.
        """

    def pipeline(self):
        """
        Method for working within the larger pipeline environment to get channel mappings.

        Args:
            channel_mapping (str): String that defines the logic for which mapping to use.
        """

        # Cleaning up naming between argument list and internal logic
        self.channel_mapping = self.args.channel_list

        # Apply mapping logic
        self.channel_mapping_logic()

        # Update the metadata
        metadata_handler.set_channels(self,self.channel_map_out)
        metadata_handler.set_sampling_frequency(self,self.metadata[self.file_cntr]['fs'][self.channel_map_out_inds])

    def direct_inputs(self,channels,channel_mapping):
        """
        Method for getting channel mappings directly outside of the pipeline environment.

        Args:
            channels (list): List of channel names to perform mapping on.
            channel_mapping (str): String that defines the logic for which mapping to use.
        """

        # Store the argument of chanel mapping to class instance
        self.clean_channel_map = channels
        self.channel_mapping   = channel_mapping

        # Apply mapping logic
        self.channel_mapping_logic()

        return self.channel_map_out

    ###################################
    #### User Provided Logic Below ####
    ###################################

    def channel_mapping_logic(self):
        """
        Update this function for the pipeline and direct handler to find new functions.
        """

        # Logic for different mappings
        if self.channel_mapping.lower() == "hup1020":
            self.mapping_HUP_1020()

    def mapping_HUP_1020(self):
        """
        Mapping used to eventually build a 1020 model using HUP data.
        """

        self.master_channel_list  = ['C03', 'C04', 'CZ', 'F03', 'F04', 'F07', 'F08', 'FZ', 'FP01', 'FP02', 'O01',
                                    'O02', 'P03', 'P04', 'T03', 'T04', 'T05', 'T06']
        self.channel_map_out      = np.intersect1d(self.clean_channel_map,self.master_channel_list)
        self.channel_map_out_inds = np.where(np.isin(self.clean_channel_map, self.channel_map_out))[0]