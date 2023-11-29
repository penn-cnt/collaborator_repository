# Adding new arguments to the pipeline

This example shows how to add new code to the libraries.

## Writing new code

New code should be written using functions. To make the burden to writing new code as small as possible, we do not require any specific coding standards, though a few basic rules must be followed for the code to be useable by the pipeline and direct_input methods.

An example of where to find the rules for adding new code is shown below:

```
class channel_clean:
    """
    Class devoted to cleaning different channel naming conventions.

    New functions should look for the self.channels object which stores the raw channel names.

    Output should be a new list of channel names called self.clean_channel_map.
    """

    def __init__(self):
        pass
```

in most cases, the rules are limited to what object the function should ingest data from, and what the result should be saved as.

Rules for how to use each class will always be available as a document string under the generation of the relevant class.

### NOTE: Preprocessing and Feature Extraction

Preprocessing and feature extraction are handled slightly differently in order to be allow for flexible pipeline generation by yaml files. For more information on how to work with these libraries, please see the [Adding to Preprocessing and Feature Extraction](../adding_preprocessing_and_features/) example.

## Where to place your code

Within each addon module, you will find a comment block denoting where the user may begin to enter their own logic. An example of what to look for is shown below:

```
    ###################################
    #### User Provided Logic Below ####
    ###################################

    def channel_clean_logic(self,clean_method):
        """
        Update this function for the pipeline and direct handler to find new functions.

        Args:
            filetype (str): cleaning method to use
        """

        # Logic gates for different cleaning methods
        if clean_method.lower() == 'hup':
            self.HUP_clean()

    def HUP_clean(self):
        """
        Return the channel names according to HUP standards.
        Adapted from Akash Pattnaik code.
        Updated to handle labels not typically generated at HUP (All leters, no numbers.)
        """

        self.clean_channel_map = []
        for ichannel in self.channels:
            regex_match = re.match(r"(\D+)(\d+)", ichannel)
            if regex_match != None:
                lead        = regex_match.group(1).replace("EEG", "").strip()
                contact     = int(regex_match.group(2))
                new_name    = f"{lead}{contact:02d}"
            else:
                new_name = ichannel.replace("EEG","").replace("-REF","").strip()
            self.clean_channel_map.append(new_name.upper())
```

You can place your function anywhere below this code block. 
