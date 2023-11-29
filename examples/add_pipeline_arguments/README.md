# Adding new arguments to the pipeline

This example shows how to add new arguments to the pipeline and enable them within the pipeline and direct inputs.

## Adding arguments to the pipeline argument parser

Before you can use a new argument within the pipeline, you will need to add it to [allowed_arguments.yaml](../../scripts/codehub/allowed_arguments.yaml) (located within the same directory as pipeline_manager.py) .

### Example argument configuration file

An example configuration file for the argument parser is as follows:
```
# These should be updated in adding new functionality to the addon modules.
allowed_project_args:
    SCALP_00: Basic scalp processing pipeline. (bjprager 10/2023)
allowed_datatypes:
    EDF: Read in EDF data.
allowed_channel_args:
    HUP1020: Channels associated with a 10-20 montage performed at HUP.
    RAW: Use all possible channels. Warning, channels may not match across different datasets.
allowed_montage_args:
    HUP1020: Use a 10-20 montage.
    COMMON_AVERAGE: Use a common average montage.

# These should only be modified if changing core functionality of the pipeline
allowed_input_args:
    CSV: Use a comma separated file of files to read in. (default)
    MANUAL: Manually enter filepaths.
    GLOB: Use Python glob to select all files that follow a user inputted pattern.
allowed_viability_args:
    VIABLE_DATA: Drop datasets that contain a NaN column. (default)
    VIABLE_COLUMNS: Use the minimum cross section of columns across all datasets that contain no NaNs.
    None: Do not remove data with NaNs.
```

You can add new projects, datatypes, channel mappings, and montages by adding them to the indented list below each argument. Please enter a descriptive help string so the argument parser can show a user how to use your new function.

If you wish to add an entirely new argument to the pipeline, you will need to add it to the pipeline_manager.py:main inside the argument parser call. If you need help with this, please feel free to reach out to the data team.

The current configuration is meant to cover as many generic use cases as possible, and is not meant to be an exhaustive list.

## Enabling your code in the addon library

Within each addon library, you will find a function similar to the following example:

```
    def channel_montage_logic(self, montage):
        """
        Update this function for the pipeline and direct handler to find new functions.

        Args:
            montage (str): User provided string for type of montage to perform.

        Returns:
            array: array of montage data
        """

        # Logic for different montages
        if montage.lower() == "hup1020":
            return self.montage_HUP_1020()
        elif montage.lower() == "common_average":
            return self.montage_common_average() 
```

By adding the keyword you entered into allowed_arguments.yml to this case statement, the code will now be able to find your new function.

**Note** The exact namespace for these case statements will vary to avoid conflicts. Each case statement should be found at the beginning of the user inputted function section, and will generally be named using the following logic: \<class name\>\_logic.
