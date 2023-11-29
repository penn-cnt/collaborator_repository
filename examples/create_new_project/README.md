# Creating a new pipeline workflow

If you wish to create your own workflow, you will need to add the logic to [project_handler.py](../../scripts/codehub/modules/addons/project_handler.py). You will also need to add the project workflow keyword to [allowed_arguments.yaml](scripts/codehub/allowed_arguments.yaml).

More information on how to do this can be found in [add new code](examples/add_new_code/) and [add pipeline arguments](examples/add_pipeline_arguments/) respectively.

## Sample project workflow
A benefit to working within the pipeline is that you can create a pipeline very quickly, which can be useful for data exploration and analysis. For example, a pipeline to just clean the data and do basic preprocessing and montaging can be instantiatied with the following seven lines of code:
```
if data_loader.pipeline(self):
    channel_clean.pipeline(self)
    channel_mapping.pipeline(self)
    dataframe_manager.__init__(self)
    dataframe_manager.column_subsection(self,self.channel_map_out)  
    df = preprocessing.__init__(self, self.dataframe, self.metadata[self.file_cntr]['fs'])
    self.montaged_dataframe = channel_montage.pipeline(self,df)
```
Obviously, a more robust code would include various documentation and data quality checks, but this is meant to show how much of the processing pipeline can be wrapped up in a simple code block.

The project handlers class comes with a template workflow that has been designed to work for most use cases, including some basic logic gates than can be applied for better control of what data is allowed through. The template is shown below:
```
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
```
Generally speaking, the pipeline above attempts to:

1. Read data into memory
2. Clean the channel labels
3. Find the channels needed for this analysis and which are present in the data.
4. Creates a dataframe of the data and cleaned channels
5. Preprocesses the data
6. Montages the data
7. Saves the data for feature extraction

Other steps can be added to this pipeline as needed. Care should be taken however to read the rules for what data is expected to be passed in and out of each class. Information for which can be found in the documentation strings for each class.
