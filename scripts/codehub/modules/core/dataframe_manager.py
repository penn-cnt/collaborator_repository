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

class dataframe_manager:
    """
    Class devoted to all things dataframe related. These dataframes will be used to populate the preprocessing, feature, tensor arrays etc.
    """

    def __init__(self):
        """
        Create the dataframe object with raw data.

        Allows for data samples without the same length.

        Row-major due to pyedflib limitations and need to work with 1-d slices for unequal lengths
        """

        ncol      = len(self.master_channel_list)
        values    = np.empty((self.nrow,ncol))
        values[:] = np.nan
        cols      = np.array(self.master_channel_list)
        for idx,icol in enumerate(self.clean_channel_map):
            ivals = self.raw_data[idx]
            try:
                column_idx                     = np.argwhere(cols==icol)[0][0]
                values[:ivals.size,column_idx] = ivals
            except IndexError:
                pass
        self.dataframe = PD.DataFrame(values, columns=self.master_channel_list)

    def column_subsection(self,keep_columns):
        """
        Return a dataframe with only the columns requested.

        Args:
            keep_columns (list of channel labels): List of columns to keep.
        """

        # Get the columns to drop
        drop_cols = np.setdiff1d(self.dataframe.columns,keep_columns)
        self.dataframe = self.dataframe.drop(drop_cols, axis=1)

    def montaged_dataframe(self,data,columns):
        """
        Create a dataframe that stores the montaged data.
        DEPRECIATE AFTER BETA PIPELINE RELEASE!

        Args:
            data (array): array of montaged data
            columns (list): List of column names
        """

        self.montaged_dataframe = PD.DataFrame(data,columns=columns)