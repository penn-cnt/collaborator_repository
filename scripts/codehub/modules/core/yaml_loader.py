import ast
import yaml
import numpy as np

class yaml_loader:
    """
    Class devoted to reading in, cleaning up, and preparing yaml scripts for preprocessing and feature pipelines.
    """

    def __init__(self,yaml_file):
        
        # Read in and typecast the yaml file
        config = yaml.safe_load(open(yaml_file,'r'))

        # Add in any looped steps to the correct yaml input format
        self.loop_handler(config)

        for ikey in list(config.keys()):
            for jkey in config[ikey]:
                self.str_handler(config[ikey][jkey])
        self.yaml_config = config

        # Make the step sorted dictionary
        try:
            self.convert_to_step()
        except Exception as e:
            raise KeyError("Unable to parse input configuration file. Please check configs and try again.")

    def return_handler(self):
        return self.yaml_config,self.yaml_step

    def loop_handler(self,config):
        """
        Parse logic in the YAML file that allows for looping over parameters. Good for fine grain searches.

        Args:
            config (dict): Raw yaml data.
        """

        # Loop over the method names
        for imethod in list(config.keys()):

            # Loop over the configuration for the method
            for method_arg,method_values in config[imethod].items():
                
                # Check the values of each method call to see if we need to add a loop
                for method_value_index, method_value_current in enumerate(method_values):

                    # Check the typing
                    if isinstance(method_value_current,dict):
                        
                        # Get the length of the entry so we know if it is a tile or a range
                        dict_key    = list(method_value_current.keys())[0]
                        dict_values = list(method_value_current.values())[0]
                        if len(dict_values) == 1:
                            new_range = np.tile(dict_key,dict_values[0])
                        else:
                            new_range = list(range(dict_key, dict_values[0], dict_values[1]))

                        # Pop the old dictionary out
                        method_values.pop(method_value_index)
                        method_values               = list(np.concatenate((method_values,new_range)))
                        config[imethod][method_arg] = method_values

    def str_handler(self,values):
        """
        Clean up string entries to proper typing

        Args:
            Current yaml entry to convert.
        """

        for idx,ivalue in enumerate(values):
            if isinstance(ivalue, str):
                if ivalue.lower() == '-np.inf':
                    values[idx] = -np.inf
                elif ivalue.lower() == 'np.inf':
                    values[idx] = np.inf
                elif ivalue.lower() == 'none' or ivalue.lower() == '':
                    values[idx] = None
                elif ivalue[0] == '[':
                    values[idx] = ast.literal_eval(ivalue)

    def convert_to_step(self):
        """
        Modify the human readable yaml to a more machine friendly step sorted dictionary.
        """
        
        # Convert human readable config to easier format for code
        self.yaml_step = {}
        for ikey in list(self.yaml_config.keys()):
            steps = self.yaml_config[ikey]['step_nums']
            for idx,istep in enumerate(steps):

                # Get the argument list for the current command
                args = self.yaml_config[ikey].copy()
                args.pop('step_nums')

                # Clean up the current argument list to only show current step
                for jkey in list(args.keys()):
                    args[jkey] = args[jkey][idx]

                # Make the step formatted command list
                self.yaml_step[istep] = {}
                self.yaml_step[istep]['method'] = ikey
                self.yaml_step[istep]['args']   = args