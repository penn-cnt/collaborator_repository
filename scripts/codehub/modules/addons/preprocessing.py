import os
import mne
import sys
import pickle
import inspect
import contextlib
import numpy as np
import pandas as PD
from io import StringIO
from fractions import Fraction
from mne.preprocessing import ICA
from mne_icalabel import label_components
from pyedflib import EdfWriter,FILETYPE_EDFPLUS
from scipy.signal import resample_poly, butter, filtfilt

# Local imports
from modules.core.yaml_loader import *
from modules.core.error_logging import *

class mne_processing:

    def __init__(self,dataset,fs,mne_channels):
        self.dataset      = dataset
        self.ppchannels   = list(dataset.columns)
        self.mne_channels = mne_channels
        self.errors       = []
        
        # Make sure that all of the frequencies match for mne
        if len(np.unique(fs)) == 1:
            self.fs = np.unique(fs)[0]
        else:
            raise IndexError("MNE Processing requires that all sampling frequencies match. Please check input data or downsampling arguments.")

    @silence_mne_warnings
    def eyeblink_removal(self,config_path,n_components=None,max_iter=1000):

        # Set components if needed
        if n_components == None:
            n_components = len(self.ppchannels)

        # Get the channel mappings in mne compliant form
        mapping      = yaml.safe_load(open(config_path,'r'))
        mapping_keys = list(mapping.keys())
        ch_types     = []
        for ichannel in self.ppchannels:
            if ichannel in mapping_keys:
                ch_types.append(mapping[ichannel])
            else:
                ch_types.append('eeg')

        # Create the mne object
        info         = mne.create_info(self.ppchannels, self.fs, ch_types=ch_types,verbose=False)
        raw          = mne.io.RawArray(self.dataset.T, info,verbose=False)
        montage      = mne.channels.make_standard_montage("standard_1020")
        mne_chan_map = dict(zip(montage.ch_names,self.mne_channels))
        montage.rename_channels(mne_chan_map)

        # Set the montages
        raw.set_montage(montage)

        # Create the ICA object and fit
        ica = ICA(n_components=n_components, random_state=42, max_iter=max_iter,verbose=False)
        ica.fit(raw,verbose=False)

        # Get the ica labels. Have to wrap it since MNE has random print statements we cant silence easily
        with contextlib.redirect_stdout(StringIO()):
            ic_labels=label_components(raw, ica, method="iclabel")

        # Get labels as a list
        labels = ic_labels['labels']

        # Get the probability for each label
        y_pred_prob = ic_labels['y_pred_proba']

        # Get the exclusion indices
        eye_inds = []
        for idx in range(len(labels)):
            ilabel = labels[idx]
            ipred  = y_pred_prob[idx]
            if ilabel not in ["brain","other"]:
                if ilabel == "other" and ipred<0.3:
                    eye_inds.append(False)
                else:
                    eye_inds.append(True)
            else:
                eye_inds.append(False)
        labels   = np.array(labels)
        eye_inds = np.array(eye_inds) 

        # Copy the raw data
        raw_copy = raw.copy()

        # Exclude eye blinks
        ica.apply(raw_copy,exclude=np.where(eye_inds)[0],verbose=False)
        
        return PD.DataFrame(raw_copy.get_data().T,columns=self.ppchannels)

class signal_processing:
    
    def __init__(self, data, fs):
        self.data = data
        self.fs   = fs
    
    def butterworth_filter(self, freq_filter_array, filter_type='bandpass', butterorder=3):
        """
        Adopted from Akash Pattnaik code in CNT Research tools.

        Parameters
        ----------
        freq_filter_array : array of integers
            Array of endpoints for frequency filter
        fs : integer
            Sampling frequency.
        filter_type : string, optional, default='bandpass'
            Type of filter to apply. [bandpass,bandstop,lowpass,highpass]
        butterorder: integer, optional, default=3
            Order of the butterworth filter.

        Returns
        -------
            Returns the filtered data.

        """

        if filter_type in ["bandpass","bandstop"]:
            bandpass_b, bandpass_a = butter(butterorder,freq_filter_array, btype=filter_type, fs=self.fs)
        elif filter_type in ["lowpass","highpass"]:
            bandpass_b, bandpass_a = butter(butterorder,freq_filter_array, btype=filter_type, fs=self.fs)
            
        return filtfilt(bandpass_b, bandpass_a, self.data, axis=0)

    def frequency_downsample(self,output_hz,input_hz=None):
        """
        Adopted from Akash Pattnaik code in CNT Research tools.

        Parameters
        ----------
        output_hz : Integer
            Output dataset frequency.
        input_hz : Integer, optional
            Input frequency. If None, convert all input sampling frequencies to output. If provided, only downsample frequencies that match this value.
            
        Returns
        -------
        Creates new downsampled dataset in instance.

        """

        if input_hz == None and self.fs != output_hz:
            frac                 = Fraction(output_hz, int(self.fs))
            return resample_poly(self.data, up=frac.numerator, down=frac.denominator)
        elif input_hz != None and input_hz == self.fs:
            frac                 = Fraction(output_hz, int(self.fs))
            return resample_poly(self.data, up=frac.numerator, down=frac.denominator)
        else:
            return self.data

class noise_reduction:
    
    def __init__(self, data, fs):
        self.data = data
        self.fs   = fs
    
    def z_score_rejection(self, window_size, z_threshold=5, method="interp"):
        """
        Reject outliers based on the Chebychev theorem. Defaults to <95%/5-sigma.

        Parameters
        ----------
            window_size : integer
                Number of data points before/after current sample to calculate mean/stdev over. Must be odd and 3+. (rounds down if even)
            z_threshold : int, optional
                Number of standard deviation for threshold. Defaults to 5.
            method : str, optional
                Whether to 'mask' (i.e. set to NaN) or 'interp' (i.e. Interpolate over) bad data. Defaults to "interp".
        
        Returns
        -------
        Updates data object in instance.
        """

        # Check parity of window size
        if window_size < 3:
            window_size = 3
        elif window_size%2 == 0:
            window_size -= 1
        
        # Calculate the z values based on sliding window +/- window_size from data point
        pad_size = int(window_size/2)
        pad_data = np.pad(self.data,(pad_size,pad_size), mode='constant', constant_values=np.nan)

        # Calculate the Z-score
        strided_data = np.lib.stride_tricks.sliding_window_view(pad_data, (window_size,))
        stride_inds  = ~np.isnan(strided_data)
        mean         = np.mean(strided_data, axis=1, where=stride_inds)
        variance     = np.mean((strided_data - mean[:, np.newaxis]) ** 2, axis=1, where=stride_inds)
        stdev        = np.sqrt(variance)
        z_vals       = np.zeros(mean.shape)
        inds         = (stdev>0)
        z_vals[inds] = np.fabs(self.data[inds]-mean[inds])/stdev[inds]

        # Replace values   
        mask = (z_vals>=z_threshold)
        if method=="mask" and any(mask):
            self.data[mask] = np.nan
        elif method=="interp" and any(mask):
            x_vals          = np.arange(self.data.size)
            x_vals_interp   = x_vals[~mask]
            y_vals_interp   = np.interp(x_vals,x_vals_interp,self.data[~mask])
            self.data[mask] = y_vals_interp[mask]
        return self.data

class preprocessing_utils:

    def __init__(self,dataset,filename,t_start,t_end,step_num,fs,outdir,debug):
        self.dataset  = dataset
        self.filename = filename
        self.t_start  = t_start
        self.t_end    = t_end
        self.step_num = step_num
        self.fs       = fs
        self.outdir   = outdir
        self.debug    = debug

    def data_snapshot_pickle(self,outpath=None):
        """
        Save a snapshot of the data in pickle format.
        (Useful for testing changes across steps.)
        """

        # Handle default pathing if needed
        self.filename = self.filename.split('/')[-1].split('.')[0]+f"_{self.t_start}_{self.t_end}_preprocess.pickle"
        if outpath == None:
            outpath = self.outdir+f"/preprocessing_snapshot/pickle/{self.step_num:02}/"
        outfile = outpath+self.filename

        # Debug flag
        if not self.debug:
            # Make sure path exists
            if not os.path.exists(outpath):
                os.system(f"mkdir -p {outpath}")

            # Write data to file
            pickle.dump((self.dataset,self.fs),open(outfile,"wb"))

    def data_snapshot_edf(self,outpath=None):
        """
        Save a snapshot of the data in edf format.
        (Useful for testing changes across steps.)

        Still in production. Digital min/max is not working correctly as of 11/12/23.
        """

        # Handle default pathing if needed
        self.filename = self.filename.split('/')[-1].split('.')[0]+f"_{self.t_start}_{self.t_end}_preprocess.edf"
        if outpath == None:
            outpath = self.outdir+f"/preprocessing_snapshot/edf/{self.step_num:02}/"
        outfile = outpath+self.filename

        # Make sure path exists
        if not os.path.exists(outpath):
            os.system(f"mkdir -p {outpath}")

        # Write data to file
        f = EdfWriter(outfile, len(self.dataset.columns), file_type=FILETYPE_EDFPLUS)
        for ii in range(self.dataset.columns.size):
            f.setSamplefrequency(ii, self.fs[ii])
        for icol in self.dataset.columns:
            signal = self.dataset[icol].values
            f.writePhysicalSamples(signal)
        f.close()
        
class preprocessing:
    """
    This class invokes the various preprocessing steps

    New preprocessing tasks should go into other classes in this script.

    Functions should return the new vector array for each channel/montage channel to be propagated forward.
    """
    
    def __init__(self,dataset,fs):
        """
        Use the preprocessing configuration file to step through the preprocessing pipeline on each data array
        in the output data container.
        """
        
        # Read in the preprocessing configuration
        YL = yaml_loader(self.args.preprocess_file)
        config,self.preprocess_commands = YL.return_handler()

        # Get the current module (i.e., the script itself)
        current_module = sys.modules[__name__]

        # Use the inspect module to get a list of classes in the current module
        classes = [cls for name, cls in inspect.getmembers(current_module, inspect.isclass)]

        # Iterate over steps, find the corresponding function, then invoke it.
        steps = np.sort(list(self.preprocess_commands.keys()))
        for istep in steps:

            # Get information about the method
            method_name = self.preprocess_commands[istep]['method']
            method_args = self.preprocess_commands[istep]['args']

            # Clean up any optional arguments set to a null input
            for key, value in method_args.items():
                if type(value) == str:
                    if value.lower() in ['','none']:
                        method_args[key]=None

            # Search the available classes for the user requested method
            for cls in classes:
                if hasattr(cls,method_name):
                    if cls.__name__ not in ['preprocessing_utils','mne_processing']:

                        # Loop over the channels and get the updated values
                        output = [] 
                        for ichannel in range(dataset.shape[1]):

                            # Perform preprocessing step
                            namespace           = cls(dataset.values[:,ichannel],fs[ichannel])
                            method_call         = getattr(namespace,method_name)
                            output.append(method_call(**method_args))

                            # Store the new frequencies if downsampling
                            if method_name == 'frequency_downsample':
                                input_fs  = method_args['input_hz']
                                output_fs = method_args['output_hz']
                                if input_fs == None or input_fs == output_fs:
                                    self.metadata[self.file_cntr]['fs'][ichannel] = output_fs

                        # Recreate the dataframe
                        dataset = PD.DataFrame(np.column_stack(output),columns=dataset.columns)
                    elif cls.__name__ == 'preprocessing_utils':
                        filename    = self.metadata[self.file_cntr]['file']
                        PU          = preprocessing_utils(dataset,filename,self.t_start,self.t_end,istep,fs,self.args.outdir,self.args.debug)
                        method_call = getattr(PU,method_name)
                        method_call(**method_args)
                    elif cls.__name__ == 'mne_processing':
                        MP = mne_processing(dataset,fs,self.mne_channels)
                        method_call = getattr(MP,method_name)
                        dataset     = method_call(**method_args)
        return dataset

