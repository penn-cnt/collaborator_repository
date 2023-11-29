import os
import mne
import json
import shutil
import pickle
import pydicom
import argparse
import mne_bids
import numpy as np
import pandas as PD
from os import path
from sys import exit
import nibabel as nib
from pathlib import Path as Pathlib

from bids import BIDSLayout
from bids.layout.writing import build_path

def make_dataset_description(dataset_description_path):

    dataset_description = {
    'Name': 'Your Dataset Name',
    'BIDSVersion': '1.6.0',
    'Description': 'Description of your dataset',
    'License': 'License information'
    }

    # Save the dataset description as JSON
    with open(dataset_description_path, 'w') as f:
        json.dump(dataset_description, f, indent=4)

def write_ignore(root,ifile):

    ignore_root = root+".bidsignore"
    bidsignore  = ignore_root+"skippedfiles.txt"
    if not path.exists(bidsignore):
        Pathlib(root).mkdir(parents=True, exist_ok=True)
        

    print("Ignoring %s" %(ifile))
    fp = open(bidsignore,"a")
    fp.write(str(ifile)+"\n")
    fp.close()
    

def wrapper(args):
    
    # Find all the files that match the top level wildcard
    searcharr  = args.dataset.split('/')
    searchpath = '/'.join(searcharr[:-1])+'/'
    fname      = searcharr[-1]+"*"
    
    # Loop over all the files
    run_dict = {}
    for path in Pathlib(searchpath).rglob("*json"):
        args.dataset = path
        run_dict     = main(args,run_dict,searchpath)

def main(args,run_dict,searchpath):

    # Make sure all command line options filled
    argsdict = vars(args)
    for ikey in argsdict.keys():
        if not argsdict[ikey]:
            print("Please specify --%s. Quitting." %(ikey))
            exit()
    
    # Get the associated files and paths
    localroot   = str(args.dataset).split('/')[-1].strip(".json")+"*"
    ifile_paths = [str(ifile) for ifile in Pathlib(searchpath).rglob(localroot)]
    ifile_exts  = ['.'.join(ifile.split('/')[-1].split('.')[1:]) for ifile in ifile_paths]
    
    # Read in the dicom data
    with open(args.dataset, 'r') as f:
        metadata = json.load(f)
    
    # Read in the datalake
    datalake = pickle.load(open(args.datalake,"rb"))
    
    # Get the acquisition date
    acq_date = metadata["AcquisitionTime"]
    
    # Get the series value
    series         = metadata["ProtocolName"].lower()
    
    # Check to see if the date file exists, if not, create it
    if path.exists(args.datefile):
        DF = PD.read_csv(args.datefile)
    else:
        DF = PD.DataFrame(columns=['SUBJECT','DATES','SESSION_TYPE'])

    # Save the data tpying info
    try:
        keyinfo   = datalake['HUP'][series]
        scan_type = keyinfo['scan_type']
        data_type = keyinfo['data_type']
        modality  = keyinfo['modality']
        task      = keyinfo['task']
        acq       = keyinfo['acq']
        ce        = keyinfo['ce']
    except KeyError:
        write_ignore(args.bidsroot,args.dataset)
        return run_dict
        
    # Check for required keys missing and put in bids ignore
    try:
        if np.isnan(data_type):
            write_ignore(args.bidsroot,args.dataset)
            return run_dict
    except TypeError:
        pass
    try:
        if np.isnan(modality):
            write_ignore(args.bidsroot,args.dataset)
            return run_dict
    except TypeError:
        pass
    
    # Clean up the optional keys
    try:
        if np.isnan(task):
            task = ''
    except TypeError:
        pass

    try:
        if np.isnan(acq):
            acq = ''
    except TypeError:
        pass

    try:
        if np.isnan(ce):
            ce = ''
    except TypeError:
        pass

    if task[:5]=='task-':task=task[5:]
    if acq[:4]=='acq-':acq=acq[4:]
    if ce[:3]=='ce-':ce=task[3:]
    
    # Check to see if the date is in the known list
    dataslice = DF.loc[(DF.SUBJECT.values==int(args.subject))&(DF.DATES.values==acq_date)]
    if (dataslice.shape[0]==1):
        session = dataslice['SESSION_TYPE'].values[0]
    else:
        print("\n")
        print("Series Description: %s" %(series))
        print("Scan Type: %s" %(scan_type))
        print("Data Type: %s" %(data_type))
        print("Modality: %s" %(modality))
        print("Task: %s" %(task))
        print("Acquisition: %s" %(acq))
        print("CE: %s" %(ce))
        print("Acquisition time of the current data file is: %s" %(acq_date))
        print("====")
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

        # Update the dataframe for future entries that match            
        iarr = np.array([args.subject,acq_date,session]).reshape((1,3))
        DF   = DF.append(PD.DataFrame(iarr,columns=DF.columns))
        DF.to_csv(args.datefile,index=False)

    # Maintain the run counter
    try:
        run_dict[int(args.subject)][acq_date][data_type]["_"+task]["_"+acq]["_"+ce][modality] += 1
        run = run_dict[int(args.subject)][acq_date][data_type]["_"+task]["_"+acq]["_"+ce][modality]        
    except KeyError:
        
        if int(args.subject) not in run_dict.keys():
            run_dict[int(args.subject)] = {}
        
        if acq_date not in run_dict[int(args.subject)].keys():
            run_dict[int(args.subject)][acq_date] = {}
        
        if data_type not in run_dict[int(args.subject)][acq_date].keys():
            run_dict[int(args.subject)][acq_date][data_type] = {}
            
        if task not in run_dict[int(args.subject)][acq_date][data_type].keys():
            run_dict[int(args.subject)][acq_date][data_type]["_"+task] = {}
            
        if acq not in run_dict[int(args.subject)][acq_date][data_type]["_"+task].keys():
            run_dict[int(args.subject)][acq_date][data_type]["_"+task]["_"+acq] = {}
            
        if ce not in run_dict[int(args.subject)][acq_date][data_type]["_"+task]["_"+acq].keys():
            run_dict[int(args.subject)][acq_date][data_type]["_"+task]["_"+acq]["_"+ce] = {}
            
        if modality not in run_dict[int(args.subject)][acq_date][data_type]["_"+task]["_"+acq]["_"+ce].keys():
            run_dict[int(args.subject)][acq_date][data_type]["_"+task]["_"+acq]["_"+ce][modality] = 1
        run = 1

    # Define entites for the pybids pathing that are shared
    entities  = {}
    entities['subject']     = '%04d' %(int(args.subject))
    entities['session']     = session
    entities['run']         = '%02d' %(run)
    entities['modality']    = modality
    entities['datatype']    = data_type
    entities['task']        = task
    entities['acquisition'] = acq
    entities['ceagent']     = ce

    # Define the patterns for pathing    
    patterns = ['sub-{subject}[/ses-{session}]/{datatype}/sub-{subject}[_ses-{session}][_acq-{acquisition}][_ce-{ceagent}][_run-{run}][_{modality}].{extension<nii|nii.gz|json|bval|bvec|json>|nii.gz}']

    # Loop over the current files
    for idx,ifile in enumerate(ifile_paths):
        entities['extension']   = ifile_exts[idx]
    
        # Set up the bids pathing
        bids_path = args.bidsroot+build_path(entities=entities, path_patterns=patterns)
        rootpath = '/'.join(bids_path.split('/')[:-1])
        Pathlib(rootpath).mkdir(parents=True, exist_ok=True)
        print("Making %s" %(bids_path))

        # Save the nifti to its new home
        #nifti_img.to_filename(bids_path)
        shutil.copyfile(ifile, bids_path)

        # Create a new BIDSLayout object
        layout = BIDSLayout(args.bidsroot)
        
        # Save the bids layout
        output_path = os.path.join(args.bidsroot, 'dataset_description.json')
        with open(output_path, 'r') as f:
            existing_data = json.load(f)
        json_output = layout.to_df().to_dict()
        merged_data = {**existing_data, **json_output}
    
        # Save the updated data back to the JSON file
        with open(output_path, 'w') as f:
            json.dump(merged_data, f, indent=4)
    
    return run_dict
    
if __name__ == '__main__':
    
    # Command line options needed to obtain data.
    parser   = argparse.ArgumentParser()
    parser.add_argument('--dataset', help='Input path to the folder containing niftii files.')
    parser.add_argument('--bidsroot', help='Output path to the BIDS root directory.')
    parser.add_argument('--datalake', help='Output path to the bids datalake for image naming.',default="./HUP_BIDS_DATALAKE.pickle")
    parser.add_argument('--datefile', help='Output path of session names mapped to acquisition dates for a given patient.',default='DATE_TO_SESSION.csv')
    parser.add_argument('--subject', help='Subject ID.')
    args = parser.parse_args()
    
    # Add a dataset description
    dataset_description_path = os.path.join(args.bidsroot, 'dataset_description.json')
    make_dataset_description(dataset_description_path)

    # Loop over json data and work file by file
    wrapper(args)
        
        
        
        
        