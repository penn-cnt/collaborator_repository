import ast
import sys
import inspect
import numpy as np
import pandas as PD
from tqdm import tqdm
from scipy.signal import welch

# Local imports
from modules.core.yaml_loader import *

class signal_processing:
    
    def __init__(self, data, fs):
        self.data = data
        self.fs   = fs
    
    def spectral_energy_welch(self, low_freq=-np.inf, hi_freq=np.inf, win_size=2., win_stride=1.):
        """
        Returns the spectral energy using the Welch method.

        Args:
            low_freq (float, optional): Low frequency cutoff. Defaults to -np.inf.
            hi_freq (float, optional): High frequency cutoff. Defaults to np.inf.
            win_size (float, optional): Window size in units of sampling frequency. Defaults to 2.
            win_stride (float, optional): Window overlap in units of sampling frequency. Defaults to 1.

        Returns:
            float: Spectral energy
        """

        # Get the number of samples in each window for welch average and the overlap
        nperseg = int(float(win_size) * self.fs)
        noverlap = int(float(win_stride) * self.fs)

        # Calculate the welch periodogram
        frequencies, psd = welch(x=self.data.reshape((-1,1)), fs=self.fs, nperseg=nperseg, noverlap=noverlap, axis=0)
        psd              = psd.flatten()

        # Calculate the spectral energy
        mask            = (frequencies >= low_freq) & (frequencies <= hi_freq)
        spectral_energy = np.trapz(psd[mask], frequencies[mask])

        # Add in the optional tagging to denote frequency range of this step
        low_freq_str = str(np.floor(low_freq))
        hi_freq_str  = str(np.floor(hi_freq))
        optional_tag = '['+low_freq_str+','+hi_freq_str+']'

        return spectral_energy,optional_tag

class features:
    """
    This class invokes the various features that can be calculated. This should not be altered without good reason.

    New feature extraction tasks should go into other classes in this script.

    Each feature should return either the scalar feature value, or a tuple with the scalar and some optional tagging for additional group distinctions.

    If you need vector returned, you can create an instance level variable and return the required elements as scalars so the resulting dataframe properly sorts values.
    """

    def __init__(self):
        """
        Use the feature extraction configuration file to step through the preprocessing pipeline on each data array
        in the output data container.
        """

        # Initialize some variables
        dummy_key       = list(self.metadata.keys())[0]
        channels        = self.metadata[dummy_key]['montage_channels']
        self.feature_df = PD.DataFrame(columns=['file','t_start','t_end','dt','method','tag']+channels)
        
        # Read in the feature configuration
        YL = yaml_loader(self.args.feature_file)
        config,self.feature_commands = YL.return_handler()

        # Get the current module (i.e., the script itself)
        current_module = sys.modules[__name__]

        # Use the inspect module to get a list of classes in the current module
        classes = [cls for name, cls in inspect.getmembers(current_module, inspect.isclass)]

        # Make a dummy list so we can append files to the dataframe in a staggered fashion (performance improvement)
        df_values = []

        # Iterate over steps, find the corresponding function, then invoke it.
        steps = np.sort(list(self.feature_commands.keys()))
        desc  = "Feature extraction with id %s:" %(self.unique_id)
        for istep in tqdm(steps, desc=desc, total=len(steps), bar_format=self.bar_frmt, position=self.worker_number, leave=False, disable=self.args.silent):

            # Get information about the method
            method_name = self.feature_commands[istep]['method']
            method_args = self.feature_commands[istep]['args']

            for cls in classes:
                if hasattr(cls,method_name):

                    # Loop over the datasets and the channels in each
                    for idx,dataset in enumerate(self.output_list):
                        
                        # Get the input frequencies
                        fs = self.metadata[idx]['fs']

                        # Loop over the channels and get the updated values
                        output = [] 
                        for ichannel in range(dataset.shape[1]):

                            for key, value in method_args.items():
                                try:
                                    method_args[key] = ast.literal_eval(value)
                                except:
                                    pass

                            # Perform preprocessing step
                            namespace           = cls(dataset[:,ichannel],fs[ichannel])
                            method_call         = getattr(namespace,method_name)
                            result_a, result_b  = method_call(**method_args)
                            output.append(result_a)

                        # Use metadata to allow proper feature grouping
                        imeta    = self.metadata[idx]
                        meta_arr = [imeta['file'],imeta['t_start'],imeta['t_end'],imeta['dt'],method_name,result_b]
                        df_values.append(np.concatenate((meta_arr,output),axis=0))

                        # Stagger condition for pandas concat
                        if (idx%5000==0):

                            # Dataframe creations
                            iDF             = PD.DataFrame(df_values,columns=self.feature_df.columns)
                            self.feature_df = PD.concat((self.feature_df,iDF))

                            # Clean up the dummy list
                            df_values = []

                    # Dataframe creations
                    iDF             = PD.DataFrame(df_values,columns=self.feature_df.columns)
                    self.feature_df = PD.concat((self.feature_df,iDF))

                    # Downcast feature array to take up less space in physical and virtual memory. Use downcast first in case its a feature that cannot be made numeric
                    for ichannel in channels:
                        try:
                            self.feature_df[ichannel]=PD.to_numeric(self.feature_df[ichannel], downcast='integer')
                            self.feature_df[ichannel]=self.feature_df[ichannel].astype('float32')
                        except ValueError:
                            pass



    def feature_aggregation(self):

        pass