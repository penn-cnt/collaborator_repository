import os
import os
import yaml
import numpy as np
import dearpygui.dearpygui as dpg

# Interface imports
from modules.theme import applyTheme
from modules.tags import tag_handler
from modules.imaging import imaging_handler
from modules.callbacks import callback_handler

class Interface(callback_handler, imaging_handler, tag_handler):

    def __init__(self):
        """
        Initialize the interface class. Convert passed arguments to instance variables

        Args:
            args (dict): Command line arguments for the lab pipeline.
            metadata (tuple): Metadata about the cli arguments (defaults,help strings, etc.)
        """
        # Set some hardcoded values for the GUI dimensions
        self.yaml_frac = 0.45
        self.height    = 720
        self.width     = 1280

        # Load the BIDS keywords
        script_directory    = os.path.dirname(os.path.abspath(__file__))
        bids_dict           = yaml.safe_load(open("configs/bids_keywords.yaml","r"))
        prepend             = ['Ignore','Other']
        self.scan_type_list = prepend+list(np.sort(bids_dict['scan_type']))
        self.data_type_list = prepend+list(np.sort(bids_dict['data_type']))
        self.modality_list  = prepend+list(np.sort(bids_dict['modality']))
        self.task_list      = prepend+list(np.sort(bids_dict['task']))
        self.ce_list        = prepend+list(np.sort(bids_dict['ce']))
        self.acq_list       = prepend+list(np.sort(bids_dict['acq']))
        self.bids_keys      = {}

        # Make the GUI
        self.show()
        
    def show(self):

        # Create the window object dpg will populate and define some starting parametwers
        dpg.create_context()
        dpg.create_viewport(title='BIDS GUI: Python Tool to help automate BIDS generation', width=self.width, height=self.height, min_height=600, min_width=900)

        # Set the theme for the window
        with dpg.window(tag="Main"):
            applyTheme()
            self.showTabBar()
            pass
        
        # Prepare the window for interactive use
        dpg.setup_dearpygui()

        # Render the window
        dpg.show_viewport()

        # Set the window as the primary viewport (meaning it will remain behind other windows, be the one called by default, etc.)
        dpg.set_primary_window("Main", True)

        # Start the interactive loop for dpg
        dpg.start_dearpygui()

        # On exit of the main window, clear dpg resources and exit interactive use
        dpg.destroy_context()
        pass

    def showTabBar(self):
        with dpg.tab_bar():
            self.showTabs()
        pass

    def showTabs(self):
        """
        Define what tabs the user will see in the main window.
        """

        # Honestly, not sure what it does exactly. Makes the tabs look nicer, but not sure how. This is boilerplate code,.
        dpg.add_texture_registry(show=False, tag='textureRegistry')
        
        # Define the different tabs. Associate with classes that handle the different pages of the gui to show.
        with dpg.tab(label='Imaging',tag="imagetab"):
            imaging_handler.showImaging(self)
            pass
        with dpg.tab(label='View Tags',tag="tagtab"):
            tag_handler.showTag(self)
            pass


class App:
    """
    Application handling class for DPG.
    Boilerplate code. Unsure why most examples call DPG via an intermediate class.
    """

    def __init__(self):
        self.interface = Interface()
        pass


if __name__ == '__main__':
    
    # Run the dearpygui app
    app = App()