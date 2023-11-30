# Imaging Data BIDS Converter
This code is meant to help with the creation of BIDS imaging data in Python. We've found HEUDICONV can be difficult to implement, so this is meant to be a more user-friendly option.

## Installation
Located in the envs folder, you will find a yaml file meant to create an anaconda environment that is setup to run the bids creation scripts.

For information on how to install a conda environment from a yaml file, please consult the [conda documentation](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file).
  
## Example
A sample call to this script may look like:
> DICOM_TO_BIDS.py --dataset RAW/ --datefile DICOM_DATES.csv --datalake HUP_BIDS_DATALAKE.pickle --bidsroot ./BIDSROOT/ --subject 0

where
- dataset: Is the directory (i.e. 'RAW/') containing the NIFTII data
- bidsroot: Is the output directory head for the bids dataset (i.e. BIDSROOT/)
- datefile: Is a tracking file that is created (i.e. DICOM_DATES.csv) to remember each session name for a given patient on a given date.
- subject: Is the subject number to assign this dataset. (i.e. 0)

For more help, please run:

> DICOM_TO_BIDS.py --help
