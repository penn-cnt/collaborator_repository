import os
import json
import shutil
import argparse
import mne_bids
import numpy as np
from pathlib import Path as Pathlib

from bids import BIDSLayout
from bids.layout.writing import build_path

def wrapper(args):
    
    # Find all the files that match the top level wildcard
    searcharr  = args.dataset.split('/')
    searchpath = '/'.join(searcharr[:-1])+'/'
    
    # Loop over all the files
    run_dict = {}
    for path in Pathlib(searchpath).rglob("*edf"):
        args.dataset = path
        run_dict     = main(args,run_dict,searchpath)

def make_dataset_description(dataset_description_path):

    dataset_description = {
    'Name': 'Your Dataset Name',
    'BIDSVersion': '1.6.0',
    'Description': 'Description of your dataset',
    'License': 'License information',
    'Authors': ['Author 1', 'Author 2'],
    'Acknowledgements': 'Acknowledgements',
    'Funding': ['Funding Source 1', 'Funding Source 2'],
    'ReferencesAndLinks': ['Reference 1', 'Reference 2'],
    'DatasetDOI': 'DOI of your dataset'
    }

    # Save the dataset description as JSON
    with open(dataset_description_path, 'w') as f:
        json.dump(dataset_description, f, indent=4)

def session_fnc():
    
    # Get the session name
    print("Please select the session type for this data.")
    print("")
    print("1: implant01 (default)")
    print("2: preimplant01")
    print("3: postsurg01")
    print("4: ms01")
    print("5: Other (will be prompted)")
    print("")
    try:
        user_input = int(input("Please enter session type (default=1): "))
    except ValueError:
        user_input=1
        
    # Case statements for session
    if user_input == 1:
        session = 'implant01'
    elif user_input == 2:
        session = 'preimplant01'
    elif user_input == 3:
        session = 'postsurg01'
    elif user_input == 4:
        session = 'ms01'
    elif user_input == 5:
        session = input("Please enter session name: ")
    return session

def run_fnc():
    
    # Get the session name
    try:
        user_input = int(input("Please enter run id. (default=00): "))
    except ValueError:
        user_input = 0 
        
    # Case statements for session
    return "%02d" %(user_input)

def datatype_fnc():
    
    # Get the session name
    print("Please select the data type.")
    print("")
    print("1: iegg (default)")
    print("2: seeg")
    print("3: Other (will be prompted)")
    print("")
    try:
        user_input = int(input("Please enter data type (default=1): "))
    except ValueError:
        user_input=1
        
    # Case statements for session
    if user_input == 1:
        datatype = 'ieeg'
    elif user_input == 2:
        datatype = 'seeg'
    elif user_input == 3:
        datatype = input("Please enter data type: ")
    return datatype

def task_fnc():
    
    # Get the session name
    try:
        user_input = int(input("Please enter the task (default=''): "))
    except ValueError:
        user_input = '' 
        
    # Case statements for session
    return user_input

def main(args):
    """
    Calls series of commands for putting EDF data into BIDS.

    Returns
    -------
    None.

    """
    
    # Get the needed keywords
    session   = session_fnc()
    run       = run_fnc()
    data_type = datatype_fnc()
    task      = task_fnc()

    # Make the epochs
    event_mapping = {'NotYetImplemented':1}

    # Define entites for the pybids pathing that are shared
    entities  = {}
    entities['subject']     = '%04d' %(int(args.subject))
    entities['session']     = session
    entities['run']         = run
    entities['modality']    = ""
    entities['datatype']    = data_type
    entities['task']        = task
    entities['acquisition'] = ""
    entities['ceagent']     = ""

    # Define the patterns for pathing    
    patterns = ['sub-{subject}[/ses-{session}]/{datatype}/sub-{subject}[_ses-{session}][_acq-{acquisition}][_ce-{ceagent}][_run-{run}][_{modality}].{extension<nii|nii.gz|json|bval|bvec|json>|nii.gz}']

    try:
        
        # Set up the bids pathing
        bids_path = args.bidsroot+build_path(entities=entities, path_patterns=patterns)
        rootpath = '/'.join(bids_path.split('/')[:-1])
        Pathlib(rootpath).mkdir(parents=True, exist_ok=True)
        print("Making %s" %(bids_path))
        
        shutil.copyfile(args.dataset, bids_path)
    except FileExistsError:
        pass        

if __name__ == '__main__':
    
    # Command line options needed to obtain data.
    parser   = argparse.ArgumentParser()
    parser.add_argument('--dataset', help='Input path to the folder containing EDF files.')
    parser.add_argument('--bidsroot', help='Output path to the BIDS root directory.')
    parser.add_argument('--datefile', help='Output path of session names mapped to acquisition dates for a given patient.',default='DATE_TO_SESSION.csv')
    parser.add_argument('--subject', help='Subject ID.')
    args = parser.parse_args()
    
    # Add a dataset description
    dataset_description_path = os.path.join(args.bidsroot, 'dataset_description.json')
    make_dataset_description(dataset_description_path)

    # Wrap all the EDF files through BIDS function
    wrapper(args)
        