# Adding Preprocessing Steps and Features

Adding preprocessing steps and features extracts is slightly differently than other addon modules. (This is due to the order in which methods are accessed when controlled by an external yaml file.)

## Preprocessing

As of 11/15/2023, we provide four classes of preprocessing.
1. Signal Processing
2. Noise Reduction
3. mne_processing
4. preprocessing_utils

### Signal Processing
Class designed to handle signal processing related tasks such as
- Downsampling
- Filtering
- etc.

Data is stored within the following objects:
- Single channel data vector: ***self.data***
- Sampling Frequency of input data: ***self.fs***

Returns:
- Output single channel data vector

### Noise Reduction
Class designed to handle signal processing related tasks such as
- Z-score Rejection/Interpolation

Data is stored within the following objects:
- Single channel data vector: ***self.data***
- Sampling Frequency of input data: ***self.fs***

Returns:
- Output single channel data vector

### mne_processing
Class designed to work with built-in functions for mne. MNE has a proprietary data format, and requires slightly unique inputs. If working with MNE, you will need to pass it the full data array. You may also encounter warnings about the data processing steps being performed outside of mne. (Basically, buyer beware.)

Data is stored within the following objects:
- Channel data matrix: self.dataset
- Single Sampling frequqnecy for all channels: self.fs
- Cleaned mne channel names for this project: self.mne_channels

Examples for how to work with this data can be found in preprocessing.py:mne_processing:eyeblink_removal

### preprocessing_utils
Class designed to provide some utility functions for preprocessing, such as saving data snapshots at different steps in the preprocessing pipeline.

Not recommended to alter this function without consulting with data team.

### New functions

If you wish to add a new function, find the class that matches your needs best, and add your function following the same rules as laid out in the documentation.

### New Classes
We recommended users emulate signal_processing or noise_reduction for new classes. The dynamic generation of method_calls requires specific inputs, and exceptions like mne_processing and preprocessing_utils need to be handled separately.

## Feature Extraction

The underlying code for this module functions similarly to preprocessing, with the exception that it is designed to return a scalar (or object that can be serialized into a dataframe object) and a potential tag. This allows the final feature dataframe to store the feature and optional tag to allow for group level statistics to be analyzed later.

### New Functions and Classes

See rules for adding to preprocessing, with the exception of the returned objects. For an example, please see features.py:signal_processing:spectral_energy_welch
