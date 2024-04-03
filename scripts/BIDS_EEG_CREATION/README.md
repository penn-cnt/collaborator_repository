# BIDS Data Generation

BIDS data is a means of organizing and naming epilepsy datasets in a cross-platform multi-institute manner that removes confusion from differing naming schema.

## EEG Data to BIDS

When possible, we should aim to download data into a BIDS compliant format. The underlying data can still be accessed using direct invocation via your preferred language,  This code will create a bids dataset from
- Local files
- iEEG.org datasets.

## Some notation

We are iterating on the best notation for some extra fields that go into this software. A quick reference follows:

- uid : A unique identifier. We anticipate use cases where someone needs to map a subject number to identifying information. This unique id is associated with each subject number and can be mapped to a private id behind a relevant firewall. This can also be the subject number, but for our institution we use a variety of ids for different projects, so mapping subject numbers directly is not ideal.
- targets : A target vector, diagnosis, etc, that can be mapped to the same basename as an edf file for easy ingestion in other scripts. Automatically added to the .bidsignore file.

### iEEG.org

This section gives some examples on how to obtain data from iEEG.org.

#### Download all annotation layers

```
python EEG_BIDS.py --ieeg --username BJPrager --password ****** --bidsroot ../../user_data/BIDS/ --session preimplant --inputs_file samples/targets.csv --annotations --multithread --ncpu 2
```

Where
- ieeg : Selects ieeg.org as the source data
- username : iEEG.org Username
- password : iEEG.ord Password
- bidsroot : Output BIDS top level directory to save to
- session : Session label for the dataset (i.e. preimplant, postsurg, etc.)
- inputs_file : File with iEEG.org filenames, unique patient identifiers, and any targets you wish to associate with each dataset
- annotations : Download by annotations
- multithread : Download and prepare BIDS data using multiple cpus
- ncpu : Number of cpus to use if multithread is selected

#### Download a list of select start times

```
python utils/acquisition/BIDS/EEG_BIDS.py --ieeg --username bjprager --password ********* --bidsroot ../../user_data/BIDS --session preimplant --inputs_file utils/acquisition/BIDS/samples/input_file.csv --cli
```

Where
- cli : Download by start times and durations found either in the inputs_file or in the cli


#### Download a single file

```
python utils/acquisition/BIDS/EEG_BIDS.py --ieeg --username bjprager --password ********* --bidsroot ../../user_data/BIDS --session preimplant --cli --start=8832031250 --duration=1e6 --dataset=EMU1144_Day01_1
```

### Direct EDF to BIDS

#### Convert a list of files to BIDS
```
python utils/acquisition/BIDS/EEG_BIDS.py --edf --inputs_file utils/acquisition/BIDS/samples/local_input_file.csv --bidsroot ../../user_data/BIDS --session preimplant
```
