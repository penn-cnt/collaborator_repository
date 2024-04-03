CNT Code Hub
================
![version](https://img.shields.io/badge/version-0.2.1-blue)
![pip](https://img.shields.io/pypi/v/pip.svg)
![https://img.shields.io/pypi/pyversions/](https://img.shields.io/pypi/pyversions/4)

This code is designed to help with the processing of epilepsy datasets commonly used within the Center for Neuroengineering & Therapeutics (CNT) at the University of Pennsylvania. 

This code is meant to be researcher driven, allowing new code libraries to be added to modules that represent common research tasks (i.e. Channel Cleaning, Montaging, Preprocessing, etc.). The code can be accessed both as independent libraries that can be called on for a range of tasks, or as part of a large framework meant to ingest, clean, and prepare data for analysis or deep-learning tasks.

For more information on how to use our code, please see the examples folder for specific use-cases and common practices.

# Prerequisites
In order to use this repository, you must have access to Python 3+. You must also have access to conda 23.+ if building environments from yaml files.

# Installation

An environment file with all the needed packages to run this suite of code can be found at the following location:

> [CNT Codehub YAML](core_libraries/python/cnt_codehub/envs/cnt_codehub.yml)

This file can be installed using the following call to conda from the envs subdirectory:

> conda env create --file cnt_codehub.yml

or from the main directory:

> conda env create --name `<env>` --file core_libraries/python/cnt_codehub/envs/cnt_codehub.yml

which will create the `cnt_codehub' environment. If you wish to alter the environment name, you can instead run:

> conda env create --file cnt_codehub.yml -n `<env>`

where `<env>` is the name of the environment you wish to save this work under.

The environment is then activated by running:

> conda activate `<env>`

More information about creating conda environments can be found [here](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html).

You will likely need to add this package to your python path to ensure full functionality of utility scripts and the main pipeline. To do so using anaconda, you can run:

> conda develop <path-to-git-head>/scripts/codehub/

## Installation using venv

To be added soon.

# Documentation

This repository is meant to serve two main purposes.

1. Create a central repository for research code that is maintained in an easy to find/easy to update fashion.
2. Create a framework for creating pipelines to ingest, clean, and analyze variable amounts of data. We also implement tracking of how the data was analyed for reproducability.

## 1. Code Repository Usage

Within the [modules](scripts/modules/) subfolder, you can find the following subdirectories:

1. core
   - Low level functions primarily focused on enabling the pipeline.
2. addons
   - User provided addons to core data processing functions.
  
Users are invited to add new code to the addons library. They may also directly access code contained in these libraries in other scripts or interactive objects by looking for the `direct_inputs' function. This function is designed to allow users to circumvent the need to run a full pipeline, but still use properly tested and optimized code. Some examples include:

- Channel Cleaning
    - Clean up channel labels according to a variety of site/hospital/industry standards.
- Channel Montaging
    - Montage data according to user specified formats.
- Preprocessing
    - Bandpass/Bandstop/Highpass/Lowpass signal filtering
    - Frequency Downsampling
    - Eyeblink removal
- Feature Extraction
    - Spectral Energy Measurements

plus much more.

To add to the available functionality, please see the [examples](examples/) directory for more information.

## 2. Pipeline Usage

Due to the required flexibility of this code, multiple runtime options are available. We have aimed to reduce the need for extensive preparation of sidecar configuration files. Any sidecar files that are needed can be generated at runtime via a cli user-interace that queries the user for processing steps. If the sidecar files are already provided, this step is skipped. An example instantiation of this code is as follows:

> python pipeline_manager.py --input GLOB --preprocess_file ../../user_data/derivative/trial_00/configs/preprocessing.yaml --feature_file ../../user_data/derivative/trial_00/configs/features.yaml --outdir ../../user_data/derivative/trial_00/features/five_second_two_second_overlap --n_input 500 --t_window 5 --t_overlap 0.4 --ncpu 2 --multithread

**pipeline_manager.py** is the main body of this code. The additional flags are:
 * --input GLOB : Query the user for a wildcard path to files to read in via the GLOB library.
 * --preprocess_file : Path to the sidecar yaml configuration file that defines preprocessing steps.
 * --feature_file : Path to the sidecar yaml configuration file that defines feature extraction steps.
 * --outdir : Output directory for the analysis
 * --n_input : Limit how many files to read in. This is useful for testing code or data and not wanting to read in all the data found along the provided path or in the pathing file.
 * --t_window : Break the data in each file into windows of the provided size in seconds.
 * --t_overlap : Percentag of overlap between consecutive time windows
 * --ncpu : Number of cpus to use if multithreaded
 * --multithread : Enable multithreaded analysis.
 
More detailed examples can be found in the [examples][examples/) directory.

# Pipeline Options

```
%run pipeline_manager.py --help
usage: pipeline_manager.py [-h] [--input {CSV,MANUAL,GLOB}] [--n_input N_INPUT] [--n_offset N_OFFSET] [--project {SCALP_00}] [--multithread] [--ncpu NCPU] [--t_start T_START] [--t_end T_END] [--t_window T_WINDOW]
                           [--t_overlap T_OVERLAP] [--datatype {EDF}] [--channel_list {HUP1020,RAW}] [--montage {HUP1020,COMMON_AVERAGE}] [--viability {VIABLE_DATA,VIABLE_COLUMNS,None}] [--interp] [--n_interp N_INTERP]
                           [--no_preprocess_flag] [--preprocess_file PREPROCESS_FILE] [--no_feature_flag] [--feature_file FEATURE_FILE] [--targets] --outdir OUTDIR [--exclude EXCLUDE] [--silent]

Simplified data merging tool.

options:
  -h, --help            show this help message and exit

Data Merging Options:
  --input {CSV,MANUAL,GLOB}
                        Choose an option:
                        CSV            : Use a comma separated file of files to read in. (default)
                        MANUAL         : Manually enter filepaths.
                        GLOB           : Use Python glob to select all files that follow a user inputted pattern.
  --n_input N_INPUT     Limit number of files read in. Useful for testing or working in batches.
  --n_offset N_OFFSET   Offset the files read in. Useful for testing or working in batch.
  --project {SCALP_00}  Choose an option:
                        SCALP_00       : Basic scalp processing pipeline. (bjprager 10/2023)
  --multithread         Multithread flag.
  --ncpu NCPU           Number of CPUs to use if multithread.

Data Chunking Options:
  --t_start T_START     Time in seconds to start data collection.
  --t_end T_END         Time in seconds to end data collection. (-1 represents the end of the file.)
  --t_window T_WINDOW   List of window sizes, effectively setting multiple t_start and t_end for a single file.
  --t_overlap T_OVERLAP
                        If you want overlapping time windows, this is the fraction of t_window overlapping.

Input datatype Options:
  --datatype {EDF}      Choose an option:
                        EDF            : Read in EDF data.

Channel label Options:
  --channel_list {HUP1020,RAW}
                        Choose an option:
                        HUP1020        : Channels associated with a 10-20 montage performed at HUP.
                        RAW            : Use all possible channels. Warning, channels may not match across different datasets.

Montage Options:
  --montage {HUP1020,COMMON_AVERAGE}
                        Choose an option:
                        HUP1020        : Use a 10-20 montage.
                        COMMON_AVERAGE : Use a common average montage.

Data viability Options:
  --viability {VIABLE_DATA,VIABLE_COLUMNS,None}
                        Choose an option:
                        VIABLE_DATA    : Drop datasets that contain a NaN column. (default)
                        VIABLE_COLUMNS : Use the minimum cross section of columns across all datasets that contain no NaNs.
                        None           : Do not remove data with NaNs.
  --interp              Interpolate over NaN values of sequence length equal to n_interp.
  --n_interp N_INTERP   Number of contiguous NaN values that can be interpolated over should the interp option be used.

Preprocessing Options:
  --no_preprocess_flag  Do not run preprocessing on data.
  --preprocess_file PREPROCESS_FILE
                        Path to preprocessing YAML file. If not provided, code will walk user through generation of a pipeline.

Feature Extraction Options:
  --no_feature_flag     Do not run feature extraction on data.
  --feature_file FEATURE_FILE
                        Path to preprocessing YAML file. If not provided, code will walk user through generation of a pipeline.

Target Association Options:
  --targets             Join target data with the final dataframe

Output Options:
  --outdir OUTDIR       Output directory.
  --exclude EXCLUDE     Exclude file. If any of the requested data is bad, the path and error gets dumped here. Also allows for skipping on subsequent loads. Default=outdir+excluded.txt (In Dev. Just gets initial load fails.)

Misc Options:
  --silent              Silent mode.
```

# Major Features Remaining
- Preprocessing Options
    - Allow multiple preprocessing blocks. This way data can be montaged during preprocessing blocks.
- Error logs
    - Errors currently print out to stdout/stderr. This can be difficult to parse with large batches of data. modules/core/error_logging.py is in development to support better error/warning logs.
- Data Types
    - MEF: Mef 3.0+ is supported. Mef 2.0+ will be released at a later date.
    - CCEP: In Development.  

# License
This code is designed to be shared within the CNT, with collaborators, and the wider Epilepsy community. Most of the code provided is open-source and does not contain any patient health information of proprietary techniques. Due to the flexible nature of this work however, proprietary code development may occur on private branches, and is not to be shared without permission.

A more fullsome description of our licensing can be found [here](LICENSE)

# Contact Us
Any questions should be directed to the data science team. Contact information is provided below:

[Brian Prager](mailto:bjprager@seas.upenn.edu)

