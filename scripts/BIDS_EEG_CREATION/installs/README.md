CNT Code Hub - EEG to BIDS
================
![version](https://img.shields.io/badge/version-0.2.1-blue)
![pip](https://img.shields.io/pypi/v/pip.svg)
![https://img.shields.io/pypi/pyversions/](https://img.shields.io/pypi/pyversions/4)

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
