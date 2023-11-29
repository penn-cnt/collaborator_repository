import sys
import pickle
import argparse
import itertools
import numpy as np
import pandas as PD
from glob import glob
from tqdm import tqdm
from scipy.signal import find_peaks

class sleep_state_power:

    def __init__(self):
        pass

    def peaks(self, vals, prominence=1, width=3, height=None):

        if height == None:
            height = 0.1*max(vals)

        return find_peaks(vals, prominence=prominence, width=width, height=height)
    
    def histogram_data(self,values):

        # Make a better plotting baseline
        self.logbins = np.logspace(7,12,50)
        self.log_x   = (0.5*(self.logbins[1:]+self.logbins[:-1]))

        # Get the histogram counts
        cnts = np.histogram(values,bins=self.logbins)[0]

        # Get the peak information
        peaks, properties = self.peaks(cnts)

        # Convert peaks into the right units for plotting
        peaks_x = self.log_x[peaks]
        peaks_y = cnts[peaks]

        properties["left_ips"]  = [self.log_x[int(np.floor(ival))] for ival in properties["left_ips"]]
        properties["right_ips"] = [self.log_x[int(np.ceil(ival))] for ival in properties["right_ips"]]

        return cnts,peaks_x,peaks_y,properties

    def get_state(self):
        """
        Parse the annotations for sleep state
        """

        # Get list of annotations to parse
        annots = self.rawdata.annotation.values
        uannot = self.rawdata.annotation.unique()
        
        # Create sleep awake masks
        sleep  = np.zeros(annots.size)
        awake  = sleep.copy()

        # Loop over annotations
        for iannot in uannot:
            if iannot != None:
                ann = iannot.lower()
                if 'wake' in ann or 'awake' in ann or 'pdr' in ann:
                    inds = (annots==iannot)
                    awake[inds]=1
                if 'sleep' in ann or 'spindle' in ann or 'k complex' in ann or 'sws' in ann:
                    inds = (annots==iannot)
                    sleep[inds]=1

        # Use sleep awake masks to get data splits
        try:
            self.sleep_list.append(self.rawdata.iloc[sleep.astype('bool')])
        except AttributeError:
            self.sleep_list = [self.rawdata.iloc[sleep.astype('bool')]]

        try:
            self.awake_list.append(self.rawdata.iloc[awake.astype('bool')])
        except AttributeError:
            self.awake_list = [self.rawdata.iloc[awake.astype('bool')]]

    def model_compile(self):

        # Merge the datasets together
        if len(self.awake_list) == 1:
            self.awake_df = self.awake_list[0]
            self.sleep_df = self.sleep_list[0]
        else:
            self.awake_df = PD.concat(self.awake_list)
            self.sleep_df = PD.concat(self.sleep_list)

        # Get the unique patient ids
        self.uids = self.rawdata['uid'].unique()

        # Create the output object
        id_cols     = ['file','t_start','t_end']
        self.output = {}

        # Get the histogram data for awake and asleep in alpha and delta
        alpha_delta_tags = ['[8.0,12.0]','[1.0,4.0]']
        awake_sleep_tags = ['awake','sleep']
        tag_combinations = list(itertools.product(awake_sleep_tags,alpha_delta_tags))
        for itag in tag_combinations:
            print("Working on %s data in the %s band." %(itag[0],itag[1]))

            # Make the data cuts
            if itag[0] == 'awake':
                iDF    = self.awake_df.loc[(self.awake_df['tag']==itag[1])]
            elif itag[1] == 'sleep':
                iDF    = self.sleep_df.loc[(self.sleep_df['tag']==itag[1])]

            # Create the outputs for this combo
            self.output[itag] = iDF[id_cols].copy().reset_index(drop=True)
            for ichan in self.channels:
                self.output[itag][ichan] = -1
            file_ref   = self.output[itag]['file'].values
            tstart_ref = self.output[itag]['t_start'].values
            range_ref  = np.arange(file_ref.size)

            # Create a numpy array to reference for searcing (faster than pandas dataframe lookup)
            lookup_array = iDF[id_cols].values

            for ichannel in tqdm(self.channels, desc='Channel searches:', total=len(self.channels), leave=False):
                values  = iDF[ichannel].values.astype('float')
                outvals = self.output[itag][ichannel].values
                cnts,peaks_x,peaks_y,properties = self.histogram_data(values)

                # Loop over the peaks to associate it with original dataframe
                for idx,ipeak in enumerate(peaks_x):
                    
                    # get the boundaries
                    lo_bound = properties['left_ips'][idx]
                    hi_bound = properties['right_ips'][idx]
                    
                    # Get the indices in bounds
                    jinds = (values>=lo_bound)&(values<=hi_bound)
                    jarr  = lookup_array[jinds]
                    
                    # Loop over the results (yes again ;_;) to populate the reference dict )
                    for irow in jarr:
                        #inds          = (file_ref==irow[0])&(tstart_ref==irow[1])
                        finds         = np.zeros(file_ref.size).astype('bool')
                        inds          = (tstart_ref==irow[1])
                        finds_numeric = [i for i in range_ref[inds] if file_ref[i] == irow[0]] 
                        finds[finds_numeric] = True
                        outvals[inds&finds] = ipeak 
                self.output[itag][ichannel] = outvals
            pickle.dump(self.output,open(self.args.outfile,"wb"))

class data_manager(sleep_state_power):

    def __init__(self,args):
        self.args        = args
        self.output_list = []

    def load_data(self,infile):
        
        # Read in and clean up the data a bit
        self.rawdata = PD.read_pickle(infile)
        files        = self.rawdata['file']
        files        = [ifile.split('/')[-1] for ifile in files]
        self.rawdata['file'] = files

        # Get the relevant channels
        black_list    = ['file','t_start','t_end','dt','method','tag','uid','target','annotation']
        self.channels = []
        for icol in self.rawdata.columns:
            if icol not in black_list:
                self.channels.append(icol) 

    def model_handler(self):

        if self.args.sleep_awake_power:
            sleep_state_power.get_state(self)

    def model_compile(self):
        if self.args.sleep_awake_power:
            sleep_state_power.model_compile(self)


def parse_list(input_str):
    """
    Helper function to allow list inputs to argparse using a space or comma

    Args:
        input_str (str): Users inputted string

    Returns:
        list: Input argument list as python list
    """

    # Split the input using either spaces or commas as separators
    values = input_str.replace(',', ' ').split()
    try:
        return [int(value) for value in values]
    except:
        return [str(value) for value in values]

if __name__ == '__main__':

    # Command line options needed to obtain data.
    parser = argparse.ArgumentParser(description="Simplified data merging tool.")

    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--file", type=str, help="Input pickle file to read in.")
    input_group.add_argument("--wildcard", type=str, help="Wildcard enabled path to pickle files to read in.")

    datachunk_group = parser.add_argument_group('Data Chunking Options')
    datachunk_group.add_argument("--group_cols", required=True, type=parse_list, help="List of columns to group by.")

    model_group = parser.add_argument_group('Type of models to associate with timeseries.')
    model_group.add_argument("--sleep_awake_power", default=True, action='store_true', help="List of columns to group by.")
    model_group.add_argument("--outfile", required=True, type=str, help="Output file path.")
    args = parser.parse_args()

    # Create the file list to read in
    if args.file != None:
        files = [args.file]
    else:
        files = glob(args.wildcard)

    # Iterate over the data and create the relevant plots
    DM = data_manager(args)
    for ifile in files:
        DM.load_data(ifile)
        DM.model_handler()
    DM.model_compile()

