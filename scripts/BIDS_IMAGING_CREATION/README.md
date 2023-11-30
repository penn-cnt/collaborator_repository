# Imaging Data BIDS Converter
This code is meant to help with the creation of BIDS imaging data in Python. We've found HEUDICONV can be difficult to implement, so this is meant to be a more user-friendly option.

## Installation
Located in the envs folder, you will find a yaml file meant to create an anaconda environment that is setup to run the bids creation scripts.

For information on how to install a conda environment from a yaml file, please consult the [conda documentation](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file).
  

Example instantiation.
> DICOM_TO_BIDS.py --dataset RAW/ --datefile DICOM_DATES.csv --datalake HUP_BIDS_DATALAKE.pickle --bidsroot ./BIDSROOT/ --subject 0

would convert all the NIFTII data within the 'RAW' directory to BIDS format. The output directory is './BIDSROOT', and it creates a file called 'DICOM_DATES.csv' to remember each session name for a given subject on a given date. In this case, 
subject '0'.

For more help, type:

> DICOM_TO_BIDS.py --help

You will need nibable and pybids to run this package.
