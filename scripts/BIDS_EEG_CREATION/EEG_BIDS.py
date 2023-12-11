import argparse
import numpy as np
import pandas as PD
from os import path
from time import sleep

# Locate import
from modules.EDF_handler import EDF_handler
from modules.iEEG_handler import ieeg_handler

# For testing, mute mne future warning
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=RuntimeWarning)

if __name__ == '__main__':

    # Command line options needed to obtain data.
    parser = argparse.ArgumentParser(description="iEEG to bids conversion tool.")

    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--ieeg", action='store_true', default=False, help="Obtain data from iEEG.org.")
    source_group.add_argument("--edf", action='store_true', default=False, help="Convert local EDF data.")

    edf_group = parser.add_argument_group('EDF input options')
    edf_group.add_argument("--edf_path", type=str, help="Path to the EDF file.")

    ieeg_group = parser.add_argument_group('iEEG connection options')
    ieeg_group.add_argument("--username", type=str, help="Username for iEEG.org.")
    ieeg_group.add_argument("--password", type=str, help="Password for iEEG.org.")
    ieeg_group.add_argument("--dataset", type=str, help="iEEG.org Dataset name")
    ieeg_group.add_argument("--start", type=float, help="Start time of clip")
    ieeg_group.add_argument("--duration", type=float, help="Duration of clip")
    ieeg_group.add_argument("--failure_file", default='./failed_ieeg_calls.csv', type=str, help="CSV containing failed iEEG calls.")

    bids_group = parser.add_argument_group('BIDS options')
    bids_group.add_argument("--bidsroot", type=str, required=True, help="Bids Root Directory.")
    bids_group.add_argument("--session", type=str, required=True, help="Base string session keyword for BIDS. (i.e. 'preimplant')")

    other_group = parser.add_argument_group('Other options')
    other_group.add_argument("--inputs_file", type=str, help="File of input datasets to (download and) turn into BIDS.")
    other_group.add_argument("--subject_file", type=str, default='subject_map.csv', help="File mapping subject id to ieeg file. (Defaults to bidroot+'subject_map.csv)")
    other_group.add_argument("--uid", default=0, type=str, help="Unique patient identifier for single ieeg calls. This is to map patients across different admissions. See sample subject_map.csv file for an example.")
    other_group.add_argument("--target", default=None, type=str, help="Target value to associate with the subject. (i.e. epilepsy vs. pnes)")

    selection_group = parser.add_mutually_exclusive_group()
    selection_group.add_argument("--cli", action='store_true', default=False, help="Use start and duration from this CLI.")
    selection_group.add_argument("--annotations", action='store_true', default=False, help="CSV file with de-identified unique patient id, ieeg filename, and targets (optional). Format:[uid,ieeg_filename,target]")
    args = parser.parse_args()

    # Clean up directory structure
    if args.bidsroot[-1] != '/':
        args.bidsroot += '/'

    # Selection criteria
    if args.ieeg:    
        if args.cli:
            start_time  = args.start
            duration    = args.duration
            map_data    = PD.DataFrame([[args.uid,args.dataset,args.target]],columns=['uid','orig_filename','target'])
        elif args.annotations:
            if args.inputs_file == None:
                input_files = [args.dataset]
                map_data    = PD.DataFrame([[args.uid,args.dataset,args.target]],columns=['uid','orig_filename','target'])
            else:
                # Read in the mapping file
                map_data = PD.read_csv(args.inputs_file)
    elif args.edf:
        if args.inputs_file == None:
            input_files = [args.dataset]
            map_data    = PD.DataFrame([[args.uid,args.dataset,args.target]],columns=['uid','orig_filename','target'])
        else:
            # Read in the mapping file
            map_data = PD.read_csv(args.inputs_file)

    # Store files to query
    input_files = map_data['orig_filename'].values

    # If iEEG.org, pass inputs to that handler to get the data
    if args.ieeg:
        IH = ieeg_handler(args,map_data,input_files)
        IH.pull_data()
    elif args.edf:
        EH = EDF_handler(args,map_data,input_files)
        EH.save_data()





                    


    