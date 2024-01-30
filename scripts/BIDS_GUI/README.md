# BIDS Imaging Creation Assistant

This GUI package is meant to help remote sites create BIDS imaging datasets. 

## Purpose

Due to the discrepancies in file systems between different sites, a unified approach to creating a BIDS dataset can encounter numerous issues.

The CNT has created a toolkit meant to create BIDS data by creating a database of keywords for different imaging projects that is fed into pyBIDS. 

To ensure compatibility with remote sites, this tool helps the user identify data on their file system and tag the data with the relevant BIDS keywords. This output can then be used to generater BIDS data with existing tools.

## Installation

In order to run this code, all you need to do is install dearpygui and prettytable. This can be accomplished via the pip command:

> pip install dearpygui

and

> pip install prettytable

## Running the GUI

To run the GUI, all you need to do is call the main body of the script via your python interpreter. An example is:

> python BIDS_GUI.py

