import glob
import numpy as np
import dearpygui.dearpygui as dpg
from prettytable import PrettyTable

class callback_handler:

    def __init__(self):
        pass

    ############################
    ###### Helper Functions ####
    ############################
    def height_fnc(self):
        """
        Find a suitable height for the yaml multiline text object.
        Could use a better method for figuring out a decent height.
        """

        height     = dpg.get_viewport_client_height()
        open_space = 1-self.yaml_frac
        modifier   = np.amin([open_space,np.log10(height/self.height)])
        if height>=self.height:
            scale = (self.yaml_frac+modifier)
        else:
            scale = (self.yaml_frac-modifier) 
        return height*scale
    

    ###############################
    #### File/Folder Selection ####
    ###############################
    
    def init_folder_selection(self,obj,sender,app_data):
        """
        Intialize the folder selection here. Need to send the object to populate with a path, and using a direct show_item doesn't allow this.
        """

        # Make a file and folder dialoge item
        self.current_path_obj = obj
        try:
            dpg.add_file_dialog(directory_selector=True, show=False, callback=self.path_selection_callback, tag="folder_dialog_id", height=400)
        except SystemError:
            pass
        dpg.show_item("folder_dialog_id")

    def init_file_selection(self,obj,sender,app_data):
        """
        Intialize the file selection here. Need to send the object to populate with a path, and using a direct show_item doesn't allow this.
        """

        # Make a file and folder dialoge item
        self.current_path_obj = obj
        try:
            dpg.add_file_dialog(directory_selector=False, show=False, callback=self.path_selection_callback, tag="file_dialog_id", height=400)
            dpg.add_file_extension(".*",parent="file_dialog_id")
        except SystemError:
            pass
        dpg.show_item("file_dialog_id")

    def path_selection_callback(self, sender, app_data):
        """
        Select a file/folder and update the folder path field.
        """
        # Get the selected path
        selected_path = list(app_data['selections'].values())[0]

        # Handle dpg bug about folder selection appearing twice in a string
        selected_path_arr = selected_path.split('/')
        if selected_path_arr[-2] == selected_path_arr[-1]:
            selected_path = '/'.join(selected_path_arr[:-1])

        dpg.set_value(self.current_path_obj,selected_path)

    ########################
    #### Misc Functions ####
    ########################
        
    def save_table(self, sender, app_data):

        # Get the output path widget text
        outpath = dpg.get_value(self.output_path_widget_text)
        
        try:
            # Empty widget frame
            dpg.delete_item(self.text_frame)

            # Save the results
            fp = open(outpath,'w')
            fp.write(self.table.get_csv_string())
            fp.close()

            # Let user know of save
            outtext = f"Output written to {outpath}"
        except AttributeError:
            outtext = "No datalake generated. Please confirm inputs."
        with dpg.child_window(parent=self.tag_frame) as self.text_frame:
            dpg.add_text(outtext)
            pass

    def radio_button_callback(self, sender, app_data):
        """
        Get the selected value from a radio button widget.
        """
        self.selected_item = dpg.get_value(sender)

    def custom_listbox_callback(self, sender):
        
        alias_id = dpg.get_alias_id(sender)
        if sender in self.selected_files.keys():
            dpg.bind_item_theme(alias_id, self.button_normal_theme)
            del self.selected_files[sender]
        else:
            dpg.bind_item_theme(sender, self.button_selected_theme)
            self.selected_files[sender] = {}

    def show_files(self, sender, app_data):

        # Get the parent folder
        self.root_dir = dpg.get_value(self.input_path_widget_text)
        if self.root_dir[-1] != '/': self.root_dir += '/'

        # Get the list of all child files
        self.file_list         = glob.glob(f"{self.root_dir}**", recursive=True)
        self.file_list_display = [ifile.replace(self.root_dir,'') for ifile in self.file_list]
        
        # Get the approximate number of lines to display
        widget_height = self.height_fnc()
        height_lines  = int(np.floor(widget_height/12)) # Found by approximation and just random tests

        # Set the selection list
        with dpg.child_window(width=self.selected_window_width,parent=self.imaging_frame) as self.custom_listbox:
            for item in self.file_list_display:
                if item != '':
                    dpg.add_button(label=item, width=-1, callback=self.custom_listbox_callback, parent=self.custom_listbox, tag=item)

    def remove_tags(self, sender, app_data):

        for ifile in list(self.selected_files.keys()):
            del self.bids_keys[ifile]
            del self.selected_files[ifile]
            alias_id = dpg.get_alias_id(ifile)
            dpg.bind_item_theme(alias_id, self.button_normal_theme)
        self.show_tags('','')

    def show_tags(self, sender, app_data):
        
        # Make the updated output dictionary of bids keywords
        self.bids_keys = {**self.bids_keys,**self.selected_files}

        for ifile in list(self.selected_files.keys()):
            session   = dpg.get_value(self.session_widget_text)
            scan_type = dpg.get_value(self.scan_type_widget)
            data_type = dpg.get_value(self.data_type_widget)
            modality  = dpg.get_value(self.modality_widget)
            task      = dpg.get_value(self.task_widget)
            ce        = dpg.get_value(self.ce_widget)
            acq       = dpg.get_value(self.acq_widget)
            if scan_type == 'Other': scan_type = dpg.get_value(self.scan_type_widget_other)
            if data_type == 'Other': data_type = dpg.get_value(self.data_type_widget_other)
            if modality  == 'Other': modality  = dpg.get_value(self.modality_widget_other)
            if task      == 'Other': task      = dpg.get_value(self.task_widget_other)
            if ce        == 'Other': ce        = dpg.get_value(self.ce_widget_other)
            if acq       == 'Other': acq       = dpg.get_value(self.acq_widget_other)
            self.bids_keys[ifile]['session']   = session
            self.bids_keys[ifile]['scan_type'] = scan_type
            self.bids_keys[ifile]['data_type'] = data_type
            self.bids_keys[ifile]['modality']  = modality
            self.bids_keys[ifile]['task']      = task
            self.bids_keys[ifile]['ce']        = ce
            self.bids_keys[ifile]['acq']       = acq

        # Initialize a pretty table for easy reading
        self.table = PrettyTable()
        self.table.field_names = ['file','session','scan_type','data_type','modality','task','ce','acq']

        # Step through the data and populate the pretty table with the current dataslice
        for ifile in list(self.bids_keys.keys()):
            idict = self.bids_keys[ifile]
            self.table.add_row([ifile,idict['session'],idict['scan_type'],idict['data_type'],idict['modality'],idict['task'],idict['ce'],idict['acq']])

        # Display pretty table
        try:
            dpg.delete_item(self.text_frame)
        except AttributeError:
            pass
        with dpg.child_window(parent=self.tag_frame) as self.text_frame:
            dpg.add_text(self.table)
            with dpg.group(horizontal=True):
                dpg.add_button(label="Save Table",callback=self.save_table)