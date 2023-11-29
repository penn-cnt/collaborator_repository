# Libraries to help path complete raw inputs
from pathlib import Path
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter

# General libraries
import os
import sys
import glob
import uuid
import yaml
import time
import argparse
import datetime
import numpy as np
import pandas as PD
from tqdm import tqdm
import multiprocessing
from pyedflib.highlevel import read_edf_header

# Import the add on classes
from modules.addons.project_handler import *
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

from configs.makeconfigs import *

class data_manager(project_handlers, metadata_handler, data_loader, channel_mapping, dataframe_manager, channel_clean, channel_montage, output_manager, data_viability, target_loader):

    def __init__(self, input_params, args, worker_number, barrier):
        """
        Initialize parent class for data loading.
        Store pathing for different data type loads.

        Args:
            infile (str): path to datafile that needs to be loaded
        """

        # Make args visible across inheritance
        self.infiles       = input_params[:,0]
        self.start_times   = input_params[:,1].astype('float')
        self.end_times     = input_params[:,2].astype('float')
        self.args          = args
        self.unique_id     = uuid.uuid4()
        self.bar_frmt      = '{l_bar}{bar}| {n_fmt}/{total_fmt}|'
        self.worker_number = worker_number
        self.barrier       = barrier

        # Create the metalevel container
        metadata_handler.__init__(self)
 
        # Initialize the output list so it can be updated with each file
        output_manager.__init__(self)
        
        # File management
        project_handlers.file_manager(self)

        # Select valid data slices
        data_viability.__init__(self)

        # Pass to feature selection managers
        self.feature_manager()

        # Associate targets if requested
        self.target_manager()

        # Save the results
        output_manager.save_features(self)

    def feature_manager(self):

        if not self.args.no_feature_flag:
            if self.args.multithread:
                self.barrier.wait()

                # Add a wait for proper progress bars
                time.sleep(self.worker_number)

                # Clean up the screen
                if self.worker_number == 0:
                    sys.stdout.write("\033[H")
                    sys.stdout.flush()
            features.__init__(self)

    def target_manager(self):

        if self.args.targets:
            for ikey in self.metadata.keys():
                ifile   = self.metadata[ikey]['file']
                target_loader.load_targets(self,ifile,'bids','target')

class CustomFormatter(argparse.HelpFormatter):
    """
    Custom formatting class to get a better argument parser help output.
    """

    def _split_lines(self, text, width):
        if text.startswith("R|"):
            return text[2:].splitlines()
        return super()._split_lines(text, width)

############################
##### Helper Functions #####
############################

def test_input_data(args,files,start_times,end_times):
    
    # Get the pathing to the excluded data
    if args.exclude == None:
        exclude_path = args.outdir+"excluded.txt"
    else:
        exclude_path = args.exclude

    # Get the files to use and which to save
    good_index = []
    bad_index  = []
    if os.path.exists(exclude_path):
        excluded_files = PD.read_csv(exclude_path)['file'].values
        for idx,ifile in enumerate(files):
            if ifile not in excluded_files:
                good_index.append(idx)
    else:
        # Confirm that data can be read in properly
        excluded_files = []
        for idx,ifile in enumerate(files):
            DLT  = data_loader_test()
            flag = DLT.edf_test(ifile)
            if flag[0]:
                good_index.append(idx)
            else:
                excluded_files.append([ifile,flag[1]])
        excluded_df = PD.DataFrame(excluded_files,columns=['file','error'])
        if not args.debug:
            excluded_df.to_csv(exclude_path,index=False)
    return files[good_index],start_times[good_index],end_times[good_index]

def overlapping_start_times(start, end, step, overlap_frac):

    # Define tracking variables
    current_time = start
    start_times  = []
    end_times    = []

    # Sanity check on step and overlap sizes
    if overlap_frac >= 1:
        raise ValueError("--t_overlap must be smaller than --t_window.")
    else:
        overlap = overlap_frac*step

    # Loop over the time range using the start, end, and step values. But then backup by windowed overlap as need
    while current_time <= end:
        start_times.append(current_time)
        if (current_time + step) < end:
            end_times.append(current_time+step)
        else:
            end_times.append(end)
        current_time = current_time + step - overlap
    start_times = np.array(start_times)
    end_times   = np.array(end_times)

    # Find edge cases where taking large steps with small offsets means multiple slices that reach the end time
    limiting_index = np.argwhere(end_times>=end).min()+1

    return start_times[:limiting_index],end_times[:limiting_index]

def make_help_str(idict):
    """
    Make a well-formated help string for the possible keyword mappings

    Args:
        idict (dict): Dictionary containing the allowed keywords values and their explanation.

    Returns:
        str: Formatted help string
    """

    return "\n".join([f"{key:15}: {value}" for key, value in idict.items()])

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
    return [int(value) for value in values]

def start_analysis(data_chunk,args,worker_id,barrier):
    """
    Helper function to allow for easy multiprocessing initialization.
    """

    DM = data_manager(data_chunk,args,worker_id,barrier)

if __name__ == "__main__":

    # Read in the allowed arguments
    raw_args = yaml.safe_load(open("allowed_arguments.yaml","r"))
    for ikey in raw_args.keys():
        exec("%s=%s" %(ikey,raw_args[ikey]))
    
    # Make a useful help string for each keyword
    allowed_project_help   = make_help_str(allowed_project_args)
    allowed_datatype_help  = make_help_str(allowed_datatypes)
    allowed_channel_help   = make_help_str(allowed_channel_args)
    allowed_montage_help   = make_help_str(allowed_montage_args)
    allowed_input_help     = make_help_str(allowed_input_args)
    allowed_viability_help = make_help_str(allowed_viability_args)

    # Command line options needed to obtain data.
    parser = argparse.ArgumentParser(description="Simplified data merging tool.", formatter_class=CustomFormatter)

    datamerge_group = parser.add_argument_group('Data Merging Options')
    datamerge_group.add_argument("--input", choices=list(allowed_input_args.keys()), default="GLOB", help=f"R|Choose an option:\n{allowed_input_help}")
    datamerge_group.add_argument("--n_input", type=int, help=f"Limit number of files read in. Useful for testing or working in batches.")
    datamerge_group.add_argument("--n_offset", type=int, default=0, help=f"Offset the files read in. Useful for testing or working in batch.")
    datamerge_group.add_argument("--project", choices=list(allowed_project_args.keys()), default="SCALP_00", help=f"R|Choose an option:\n{allowed_project_help}")
    datamerge_group.add_argument("--multithread", action='store_true', default=False, help="Multithread flag.")
    datamerge_group.add_argument("--ncpu", type=int, default=2, help="Number of CPUs to use if multithread.")

    datachunk_group = parser.add_argument_group('Data Chunking Options')
    datachunk_group.add_argument("--t_start", default=0, help="Time in seconds to start data collection.")
    datachunk_group.add_argument("--t_end", default=-1, help="Time in seconds to end data collection. (-1 represents the end of the file.)")
    datachunk_group.add_argument("--t_window", type=parse_list, help="List of window sizes, effectively setting multiple t_start and t_end for a single file.")
    datachunk_group.add_argument("--t_overlap", default=0, type=float, help="If you want overlapping time windows, this is the fraction of t_window overlapping.")

    datatype_group = parser.add_argument_group('Input datatype Options')
    datatype_group.add_argument("--datatype", default='EDF', choices=list(allowed_datatypes.keys()), help=f"R|Choose an option:\n{allowed_datatype_help}")

    channel_group = parser.add_argument_group('Channel label Options')
    channel_group.add_argument("--channel_list", choices=list(allowed_channel_args.keys()), default="HUP1020", help=f"R|Choose an option:\n{allowed_channel_help}")

    montage_group = parser.add_argument_group('Montage Options')
    montage_group.add_argument("--montage", choices=list(allowed_montage_args.keys()), default="HUP1020", help=f"R|Choose an option:\n{allowed_montage_help}")

    viability_group = parser.add_argument_group('Data viability Options')
    viability_group.add_argument("--viability", choices=list(allowed_viability_args.keys()), default="VIABLE_DATA", help=f"R|Choose an option:\n{allowed_viability_help}")
    viability_group.add_argument("--interp", action='store_true', default=False, help="Interpolate over NaN values of sequence length equal to n_interp.")
    viability_group.add_argument("--n_interp", default=1, help="Number of contiguous NaN values that can be interpolated over should the interp option be used.")

    preprocessing_group = parser.add_argument_group('Preprocessing Options')
    preprocessing_group.add_argument("--no_preprocess_flag", action='store_true', default=False, help="Do not run preprocessing on data.")
    preprocessing_group.add_argument("--preprocess_file", help="Path to preprocessing YAML file. If not provided, code will walk user through generation of a pipeline.")

    feature_group = parser.add_argument_group('Feature Extraction Options')
    feature_group.add_argument("--no_feature_flag", action='store_true', default=False, help="Do not run feature extraction on data.")
    feature_group.add_argument("--feature_file", help="Path to preprocessing YAML file. If not provided, code will walk user through generation of a pipeline.")

    target_group = parser.add_argument_group('Target Association Options')
    target_group.add_argument("--targets", action='store_true', default=False, help="Join target data with the final dataframe")

    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument("--outdir", required=True, default="../../user_data/derivative/", help="Output directory.") 
    output_group.add_argument("--exclude", help="Exclude file. If any of the requested data is bad, the path and error gets dumped here. \
                              Also allows for skipping on subsequent loads. Default=outdir+excluded.txt (In Dev. Just gets initial load fails.)") 

    misc_group = parser.add_argument_group('Misc Options')
    misc_group.add_argument("--silent", action='store_true', default=False, help="Silent mode.")
    misc_group.add_argument("--debug", action='store_true', default=False, help="Debug mode. If set, does not save results. Useful for testing code.")
    args = parser.parse_args()

    # Make the output directory as needed
    if not os.path.exists(args.outdir) and not args.debug:
        print("Output directory does not exist. Make directory at %s (Y/y)?" %(args.outdir))
        user_input = input("Response: ")
        if user_input.lower() == 'y':
            os.system("mkdir -p %s" %(args.outdir))

    # Set the input file list
    if args.input == 'CSV':
        
        # Tab completion enabled input
        completer = PathCompleter()
        print("Using CSV input. Enter a three column csv file with filepath,starttime,endtime.")
        print("If not starttime or endtime provided, defaults to argument inputs. Use --help for more information.")
        file_path = prompt("Please enter path to input file csv: ", completer=completer)

        # Read in csv file
        input_csv   = PD.read_csv(file_path)
        files       = input_csv['filepath'].values
        start_times = input_csv['start_time'].values
        end_times   = input_csv['end_time'].values

        # Replace NaNs with appropriate times as needed
        start_times = np.nan_to_num(start_times,nan=args.t_start)
        end_times   = np.nan_to_num(end_times,nan=args.t_end)
    elif args.input == 'GLOB':

        # Tab completion enabled input
        completer = PathCompleter()
        file_path = prompt("Please enter (wildcard enabled) path to input files: ", completer=completer)
        files     = glob.glob(file_path)

        # Make sure we were handed a good filepath
        if len(files) == 0:
            raise IndexError("No data found with that search. Cannot iterate over a null file list.")

        # Create start and end times array
        start_times = args.t_start*np.ones(len(files))
        end_times   = args.t_end*np.ones(len(files))
    else:
        # Tab completion enabled input
        completer = PathCompleter()
        file_path = prompt("Please enter path to input file: ", completer=completer)
        files     = [file_path]

        # Create start and end times array
        start_times = args.t_start*np.ones(len(files))
        end_times   = args.t_end*np.ones(len(files))

    # Cast the inputs as arrays
    files       = np.array(files)
    start_times = np.array(start_times)
    end_times   = np.array(end_times)

    # Get the useable files from the request
    files, start_times, end_times = test_input_data(args,files,start_times,end_times)

    # Apply any file offset as needed
    files       = files[args.n_offset:]
    start_times = start_times[args.n_offset:]
    end_times   = end_times[args.n_offset:]

    # Limit file length as needed
    if args.n_input != None:
        files       = files[:args.n_input]
        start_times = start_times[:args.n_input]
        end_times   = end_times[:args.n_input]

    # If using a sliding time window, duplicate inputs with the correct inputs
    if args.t_window != None:
        new_files = []
        new_start = []
        new_end   = []
        for ifile in files:

            # Read in just the header to get duration
            if args.t_end == -1:
                t_end = read_edf_header(ifile)['Duration']
            else:
                t_end = args.t_end

            # Get the start time for the windows
            if args.t_start == None:
                t_start = 0
            else:
                t_start = args.t_start

            for iwindow in args.t_window:
                
                # Get the list of windows start and end times
                windowed_start, windowed_end = overlapping_start_times(t_start,t_end,iwindow,args.t_overlap)

                # Loop over the new entries and tile the input lists as needed
                for idx,istart in enumerate(windowed_start):
                    new_files.append(ifile)
                    new_start.append(istart)
                    new_end.append(windowed_end[idx])
        files       = new_files
        start_times = new_start
        end_times   = new_end 

    # Make configuration files as needed
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    if args.preprocess_file == None and not args.no_preprocess_flag:
        from modules import preprocessing
        dirpath              = args.outdir+"configs/"
        os.system("mkdir -p %s" %(dirpath))
        args.preprocess_file = dirpath+"preprocessing_"+timestamp+".yaml"
        config_handler       = make_config(preprocessing,args.preprocess_file)
    if args.feature_file == None:
        from modules import features
        dirpath           = args.outdir+"configs/"
        os.system("mkdir -p %s" %(dirpath))
        args.feature_file = dirpath+"features_"+timestamp+".yaml"
        config_handler    = make_config(features,args.feature_file)

    # Multithread options
    input_parameters = np.column_stack((files, start_times, end_times))
    if args.multithread:

        # Calculate the size of each subset based on the number of processes
        subset_size  = input_parameters.shape[0] // args.ncpu
        list_subsets = [input_parameters[i:i + subset_size] for i in range(0, input_parameters.shape[0], subset_size)]

        # Handle leftovers
        if len(list_subsets) > args.ncpu:
            arr_ncpu  = list_subsets[args.ncpu-1]
            arr_ncpu1 = list_subsets[args.ncpu]

            list_subsets[args.ncpu-1] = np.concatenate((arr_ncpu,arr_ncpu1), axis=0)
            list_subsets.pop(-1)

        # Create a barrier for synchronization
        barrier = multiprocessing.Barrier(args.ncpu)

        # Create processes and start workers
        processes = []
        for worker_id, data_chunk in enumerate(list_subsets):
            process = multiprocessing.Process(target=start_analysis, args=(data_chunk,args,worker_id,barrier))
            processes.append(process)
            process.start()
        
        # Wait for all processes to complete
        for process in processes:
            process.join()
    else:
        start_analysis(input_parameters, args, 0, None)