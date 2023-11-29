# Directly accessing the core libraries

There are two methods for using the core libraries kept within this framework. We recommend the first method, but a brief description of the second is provided for edification.

## Direct Inputs Method

Each addon module includes a direct_inputs method to pass each module data and obtain its relevant output. An example for the montage class is as follows:
```
    def direct_inputs(self,DF,montage):
        """
        Method for getting channel montages directly outside of the pipeline environment.

        Args:
            DF (datafram): Dataframe to get montage for.
            montage (str): Montage to perform

        Returns:
            dataframe: New dataframe with montage data and channel names
        """
        
        # Save the user provided dataframe
        self.dataframe_to_montage = DF

        # Apply montage logic
        montage_data = self.channel_montage_logic(montage)

        return PD.DataFrame(montage_data,columns=self.montage_channels)
```

For example, I could call on this method in the following way (assuming I have the scripts/codehub/ in my PythonPath):

```
from modules.addons.channel_montage import channel_montage

# Dataframe generation
DF = **Your datafrme here**

# Montage choice
montage = "hup1020"

CM     = channel_montage()
new_df = CM.direct_inputs(DF,montage)
```

And you would have a new dataframe that is montaged and labeled accordingly.
