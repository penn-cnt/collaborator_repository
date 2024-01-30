import dearpygui.dearpygui as dpg

class imaging_handler:

    def __init__(self):
        pass

    def showImaging(self, main_window_width = 1280):

        # Child Window Geometry
        self.child_window_width    = int(0.65*main_window_width)
        self.selected_window_width = int(0.32*main_window_width) 

        # Hard coded variables
        default = 'Ignore'

        # Define the file selection themes
        self.selected_files = {}
        with dpg.theme() as self.button_selected_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (0,119,200,153))
        with dpg.theme() as self.button_normal_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (51, 51, 55, 255))

        # Show the imaging keyword widgets
        with dpg.group(horizontal=True) as self.imaging_frame:
            with dpg.child_window(width=self.child_window_width,parent=self.imaging_frame):

                ######################### 
                ###### Input Block ######
                #########################

                # Input pathing
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{'Input Path':20}")
                    self.input_path_widget_text = dpg.add_input_text(width=int(0.5*self.child_window_width))
                    self.input_path_widget      = dpg.add_button(label="Select Folder", width=int(0.15*self.child_window_width), callback=lambda sender,
                                                                 app_data:self.init_folder_selection(self.input_path_widget_text, sender, app_data))
                    dpg.add_button(label="Show", callback=self.show_files, width=int(0.1*self.child_window_width))
                # Output pathing
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{'Output Path':20}")
                    self.output_path_widget_text = dpg.add_input_text(width=int(0.5*self.child_window_width),default_value='./datalake.csv')

                ########################### 
                ###### BIDS Keywords ######
                ###########################
                
                dpg.add_spacer(height=10)
                dpg.add_separator()
                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{'Session':20}")
                    self.session_widget_text = dpg.add_input_text(width=int(0.5*self.child_window_width), default_value='ses-preimplant001')

                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{'Scan Type':20}")
                    self.scan_type_widget = dpg.add_combo(items=self.scan_type_list, width=int(0.5*self.child_window_width))
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{'':20}")
                    dpg.add_text(f"{'If other:':10}")
                    self.scan_type_widget_other = dpg.add_input_text(width=int(0.41*self.child_window_width))

                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{'Data Type':20}")
                    self.data_type_widget = dpg.add_combo(items=self.data_type_list, width=int(0.5*self.child_window_width))
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{'':20}")
                    dpg.add_text(f"{'If other:':10}")
                    self.data_type_widget_other = dpg.add_input_text(width=int(0.41*self.child_window_width))

                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{'Modality':20}")
                    self.modality_widget = dpg.add_combo(items=self.modality_list, width=int(0.5*self.child_window_width))
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{'':20}")
                    dpg.add_text(f"{'If other:':10}")
                    self.modality_widget_other = dpg.add_input_text(width=int(0.41*self.child_window_width))

                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{'Task':20}")
                    self.task_widget = dpg.add_combo(items=self.task_list, default_value=default, width=int(0.5*self.child_window_width))
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{'':20}")
                    dpg.add_text(f"{'If other:':10}")
                    self.task_widget_other = dpg.add_input_text(width=int(0.41*self.child_window_width))

                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{'ce':20}")
                    self.ce_widget = dpg.add_combo(items=self.ce_list, default_value=default, width=int(0.5*self.child_window_width))
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{'':20}")
                    dpg.add_text(f"{'If other:':10}")
                    self.ce_widget_other = dpg.add_input_text(width=int(0.41*self.child_window_width))

                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{'Acquisition':20}")
                    self.acq_widget = dpg.add_combo(items=self.acq_list, default_value=default, width=int(0.5*self.child_window_width))
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{'':20}")
                    dpg.add_text(f"{'If other:':10}")
                    self.ce_widget_other = dpg.add_input_text(width=int(0.41*self.child_window_width))

                dpg.add_spacer(height=10)
                dpg.add_separator()
                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Create Tags", callback=self.show_tags)
                    dpg.add_button(label="Remove Tags", callback=self.remove_tags)