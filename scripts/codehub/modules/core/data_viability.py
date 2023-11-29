# General libraries
import numpy as np
import pandas as PD
from sys import exit

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

class data_viability:
    """
    Handles different ways of rejecting bad data.

    Will be updated to have cleaner object definitions for new functions. At present, viable data is the only fully tested option.
    """

    def __init__(self):
        """
        Logic gating for interpolation of small patches of data and how to slice out large swaths of bad data.
        """

        # Interpolate over small subsets of NaN if requested
        if self.args.interp:
            for idx,data_array in self.output_list:
                self.output_list[idx] = self.interpolate_data(data_array)

        # Find minimum viable datasets
        if self.args.viability == "VIABLE_DATA":

            # Loop over each dataset and find the ones that have no NaNs
            flags = []
            for idx,data_array in enumerate(self.output_list):
                flags.append(self.viable_dataset(data_array))

            # Output list
            viable_data = []
            viable_meta = {}
            for idx,iarr in enumerate(self.output_list):
                if flags[idx]:
                    viable_data.append(iarr)
                    viable_meta[idx] = self.metadata[self.output_meta[idx]]
            
            # Copying results. Kept as two variables for possible disambiguation later.
            self.output_list = viable_data.copy()
            metadata_handler.update_metadata(self,viable_meta)

        elif self.args.viability == 'VIABLE_COLUMNS':
            
            # Loop over each array and get the valid columns as boolean flag
            flags = []
            for idx,data_array in self.output_list:
                flags.append(self.viable_columns(data_array))
            
            # Find the intersection of viable columns across all datasets
            flags = np.prod(flags,axis=0)

            # If no columns are viable, alert user and raise exception
            if ~flags.all():
                Exception("No channels are valid across all datasets.")

            # Update the montage channel list
            self.montage_channels = self.montage_channels[flags]

            self.viable_data = [iarr[:,flags] for iarr in self.output_list]

            # Copying results. Kept as two variables for possible disambiguation later.
            self.output_list = self.viable_data.copy()

    def viable_dataset(self,data_array):
        """
        Flag if the !dataset! has any bad data and exclude the dataset.

        Args:
            data_array (array): Data array.

        Returns:
            Single boolean flag. True=Keep. False=Drop.
        """
        
        # Loop over the index associated with the datasets and keep only datasets without NaNs
        return ~np.isnan(data_array).any()


    def viable_columns(self,data_array):
        """
        Flag if a !channel! has any bad data and exclude the channel.

        Args:
            data_array (array): Data array.

        Returns:
            Boolean mask for column array.
        """

        # Loop over the index associated with the columns and only return columns without NaNs
        keep_index = []
        for i_index in range(data_array.shape[1]):
            idata = data_array[:,i_index]
            if ~np.isnan(idata).any():
                keep_index.append(True)
            else:
                keep_index.append(False)

        return keep_index
    
    def consecutive_counter(self,iarr,ival):
        """
        Counts the number of consecutive instances of a value in an array. Returns a mask for trains less than argument set number.

        Args:
            iarr (1-d array): Array to look across for a particular value. 
            ival (float): Value to look for in the array

        Returns:
            boolean array: Mask of entries that match the criteria
        """

        # Add padding to the array to get an accurate difference between elements that includes first and last
        if ~np.isnan(ival):
            diffs = np.diff(np.concatenate(([False], iarr == ival, [False])).astype(int))
        else:
            diffs = np.diff(np.concatenate(([False], np.isnan(iarr), [False])).astype(int))

        # Get the indices that denote where the array changes to/from expected value
        left_ind  = np.flatnonzero(diffs == 1)
        right_ind = np.flatnonzero(diffs == -1)

        # Get the counts of values that match the criteria
        counts = right_ind-left_ind

        # Create a mask and iterate over counts and change mask to true for consecutive values equal to or less than the allowed threshold
        mask = np.zeros(iarr.size).astype('bool')
        for ival in counts:
            if ival <= self.args.n_interp:
                for ii in range(self.args.n_interp):
                    mask[left_ind+ii] = True
        return mask

    def interpolate_data(self,data_array):
        """
        Interpolate over specific train of a select value in an array, column wise.

        Args:
            data_array (array): Data array to interpolate out bad data.

        Returns:
            array: data array with interpolated entries.
        """

        # Loop over the columns
        for icol in range(data_array.shape[1]):
            
            # Get the current timeseries and calculate the mask
            vals = data_array[:,icol]
            mask = self.consecutive_counter(vals,np.nan)

            # Ensure that the first and last indices are false. This is to a avoid extrapolation.
            mask[0]  = False
            mask[-1] = False

            # Interpolate where appropriate
            x_vals          = np.arange(vals.size)
            x_interpretable = x_vals[~mask]
            y_interpretable = vals[~mask]
            interp_vals     = np.interp(x_vals,x_interpretable,y_interpretable)
            vals[mask]      = interp_vals[mask]
            
            # Insert new values into the original data array
            data_array[:,icol] = vals
        return data_array
