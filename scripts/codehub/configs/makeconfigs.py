import ast
import yaml
import inspect
import numpy as np

class make_config:
    """
    Class devoted to helping users create a yaml configuration file on the fly.

    At present it will look for any functions in features or preprocessing to present to the user. It requires a docstring to give much useful information.

    This does not currently support making looped values on the fly. Those must be entered by hand. This feature will be developed later.
    """
    
    def __init__(self,config_library,outfile):
        
        # Define the dictionary to be saved to YAML
        self.config_dict = {}
        
        # Logic for preprocessing versus feature extraction
        self.make_config(config_library,outfile)
            
    def print_methods(self,library):
        
        # Get all members (classes and functions) defined in the module
        members = inspect.getmembers(library)

        # Create the output dictionart for easier access
        self.argdict = {}

        # Iterate through the members
        for name, member in members:

            # Check if it's a class defined in the module
            if inspect.isclass(member) and member.__module__ == library.__name__:
                print("====================================\n")

                # Iterate through the methods of the class and print their docstrings
                for method_name, method in inspect.getmembers(member):
                    if method_name != '__init__':
                        if inspect.isfunction(method):
                            docstring = inspect.getdoc(method)
                            docstring = docstring.replace("\n","\n    ")
                            if docstring:
                                
                                # Print clean output to screen
                                print(f"Method: {method_name}\nDocstring: {docstring}\n")
                                
                                # Save arguments to dictionary for easier access
                                signature = inspect.signature(getattr(member,method_name))
                                args      = list(signature.parameters.values())
                                self.argdict[method_name] = [str(ival) for ival in args]

    def literal_to_list(self,literal_str):
        vals = ast.literal_eval(literal_str)
        if type(vals) == int:
            new_list = [vals]
        else:
            new_list = list(vals)
        return new_list            

    def query_inputs(self,method_name):
        
        # Create dictionary to turn into yaml
        self.config_dict[method_name] = {}
        
        # Ask for the step number
        while True:
            try:
                step_list = input("Enter list of which steps this method should be used: ")
                step_list = self.literal_to_list(step_list)
                self.config_dict[method_name]['step_nums'] = step_list
                break
            except ValueError:
                print("Incorrect input format. Enter list of steps.")
        
        # Loop over the actual arguments to get their inputs
        for iarg in self.argdict[method_name]:
            if iarg != 'self':
                
                # Break up on default options
                argsplit = iarg.split('=')
                if len(argsplit)==2:
                    default = argsplit[1]
                else:
                    default = ''
                    
                # Query user for entries
                while True:
                    print("Enter list of inputs for %s, one for each step in the processing pipeline. " %(argsplit[0]))
                    arg_list = input("(Default=%s): " %(default))
                    
                    # Clean up possible user inputs
                    if arg_list == '' and default == '':
                        print('Input required for this variable.')
                    else:
                        if arg_list == '' and default != '':
                            arg_list = [ast.literal_eval(default)]
                        elif arg_list[0] != '[':
                            arg_list = ast.literal_eval("["+arg_list+"]")
                        else:
                            arg_list = [arg_list]

                        # Make lists of inputs
                        if type(arg_list) == int and len(step_list) > 1:
                            arg_list = list(np.tile(arg_list,len(step_list)))
                        
                        self.config_dict[method_name][argsplit[0]] = arg_list
                        break
            
            print("Current configuration: ",self.config_dict)
        print("=============")
    
    def write_yaml_file(self, filename):

        with open(filename, 'w') as file:
            yaml.dump(self.config_dict, file, default_flow_style=False)

        import sys
        sys.exit()

        # Clean up the dictionary to be more readable
        for key, value in self.config_dict.items():
            if type(value) == dict:
                for key2,value2 in self.config_dict[key].items():
                    self.config_dict[key][key2] = str(value2)
        
        with open(filename, 'w') as file:
            yaml.dump(self.config_dict, file, default_flow_style=False)
    
    def make_config(self,config_library,outfile):
        
        # Pass the preprocessing library to a function that prints user-readable docstrings.
        self.print_methods(config_library)
        
        # Loop over user selected methods until we receive a quit signal
        while True:
            method_choice = input("\nEnter Method Name to configure. (Q/Quit to stop configuration): ")
            if method_choice.lower() in ['q','quit']:
                self.write_yaml_file(outfile)
                break
            else:
                self.query_inputs(method_choice)
