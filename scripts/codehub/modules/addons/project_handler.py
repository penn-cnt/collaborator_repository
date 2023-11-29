from sys import exit

# Import the add on classes
from modules.addons.data_loader import *
from modules.addons.channel_clean import *
from modules.addons.channel_mapping import *
from modules.addons.channel_montage import *
from modules.addons.preprocessing import *
from modules.addons.features import *

# Import the core classes
from modules.core.metadata_handler import *
from modules.core.target_loader import *
from modules.core.dataframe_manager import *
from modules.core.output_manager import *
from modules.core.data_viability import *

class project_handlers:
    """
    Class devoted the specific pipeline used to load data according to project needs. This is meant to provide a clean reproducable pipeline.

    New functions should follow all the data processing steps up to preprocessing and feature extraction that are relevant to their data type and data set.
    """

    def __init__(self):
        pass

    def file_manager(self):
        """
        Loop over the input files and send them to the correct data handler.

        Args:
            infiles (str list): Path to each dataset
            start_times (float list): Start times in seconds to start sampling
            end_times (float list): End times in seconds to end sampling
        """

        # Intialize a variable that stores the previous filepath. This allows us to cache data and only read in as needed. (i.e. new path != old path)
        self.oldfile = None  

        # Loop over files to read and store each ones data
        nfile = len(self.infiles)
        desc  = "Initial load with id %s:" %(self.unique_id)
        for ii,ifile in tqdm(enumerate(self.infiles), desc=desc, total=nfile, bar_format=self.bar_frmt, position=self.worker_number, leave=False, disable=self.args.silent):            
        
            # Save current file info
            self.infile    = ifile
            self.t_start   = self.start_times[ii]
            self.t_end     = self.end_times[ii]

            # Initialize the metadata container
            self.file_cntr = ii

            # Apply project specific pipeline
            self.project_logic()
            
            # Update file strings for cached read in
            self.oldfile = self.infile

    ##########################
    #### Template Project ####
    ##########################

    def template(self):

        # Import data into memory
        load_flag = data_loader.pipeline(self)      # Load flag is a boolean that lets us know if the current data loaded correctly

        # If data loaded, begin the processing portion
        if load_flag:
            # Clean the channel names
            channel_clean.pipeline(self)

            # Get the correct channels for this merger
            channel_mapping.pipeline(self)

            # Once we have the cleaned channel names, and the appropriate column slices, make a dataframe.
            # Dataframes are formed from the self.raw_data object and self.master_channel_list.
            # Data up to this point is kept as a raw array due to variable input formats and because dataframes
            # tend to take up more memory and have slower operations. 
            dataframe_manager.__init__(self)
            dataframe_manager.column_subsection(self,self.channel_map_out)  

            # We can use the dataframe to set criteria for continued analysis.
            # In this example, the data must have at least the sampling frequency worth of values
            if self.dataframe.shape[0] > int(max(self.metadata[self.file_cntr]['fs'])):
                
                # You can either montage first, then preprocess, or vice versa.
                # At present you cannot mix these steps. But later updates will allow
                # to provide the ability to define multiple preprocessing blocks that
                # can be ordered independently.
                df = preprocessing.__init__(self, self.dataframe, self.metadata[self.file_cntr]['fs'])

                # Montage the data
                self.montaged_dataframe = channel_montage.pipeline(self,df)

                # Store the data to the output handler so we can pass everything to the feature extractor
                # Returning to a list of arrays so it can be passed to different modeling back-ends like PyTorch.
                output_manager.update_output_list(self,df.values)

    ###################################
    #### User Provided Logic Below ####
    ###################################

    def project_logic(self):
        """
        Update this function for the pipeline to find new pipelines.
        """

        # Case statement the workflow
        if self.args.project.lower() == 'scalp_00':
            project_handlers.scalp_00(self)

    def scalp_00(self):
        """
        Run pipeline to load EDF data for a scalp project.
        """

        # Import data into memory
        load_flag = data_loader.pipeline(self) 

        if load_flag:
            # Clean the channel names
            channel_clean.pipeline(self)

            # Get the correct channels for this merger
            channel_mapping.pipeline(self)

            # Create the dataframe for the object with the cleaned labels
            dataframe_manager.__init__(self)
            dataframe_manager.column_subsection(self,self.channel_map_out)

            # Perform next steps only if we have a viable dataset
            if self.dataframe.shape[0] > int(max(self.metadata[self.file_cntr]['fs'])):

                # Make the cleaned mne channel map
                mne_channels      = mne.channels.make_standard_montage("standard_1020").ch_names
                self.mne_channels = channel_clean.direct_inputs(self,mne_channels)

                # Preprocess the data
                df = preprocessing.__init__(self, self.dataframe, self.metadata[self.file_cntr]['fs'])

                # Put the data into a specific montage
                self.montaged_dataframe = channel_montage.pipeline(self,df)

                # Update the output list
                output_manager.update_output_list(self,self.montaged_dataframe.values)