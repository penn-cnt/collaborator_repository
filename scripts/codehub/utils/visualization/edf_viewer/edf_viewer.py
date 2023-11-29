# Basic Python Imports
import sys
import time
import glob
import argparse
from os import path

# User interface imports
import tkinter as tk

# Matplotlib import and settings
import matplotlib.pyplot as PLT
from matplotlib.text import Text
from matplotlib.ticker import MultipleLocator

# Local imports
from modules.addons.data_loader import *
from modules.addons.channel_clean import *
from modules.addons.channel_mapping import *
from modules.addons.channel_montage import *

#################
#### Classes ####
#################

class data_handler:

    def __init__(self):
        pass

    def data_prep(self):

        # Create pointers to the relevant classes
        DL    = data_loader()
        CHCLN = channel_clean()
        CHMAP = channel_mapping()
        CHMON = channel_montage()

        # Get the raw data and pointers
        if not self.args.pickle_load:
            DF,self.fs = DL.direct_inputs(self.infile,'edf')
        else:
            DF,self.fs = pickle.load(open(self.infile,"rb"))
            self.fs    = self.fs[0]

        # Get the cleaned channel names
        clean_channels = CHCLN.direct_inputs(DF.columns)
        channel_dict   = dict(zip(DF.columns,clean_channels))
        DF.rename(columns=channel_dict,inplace=True)

        # Get the channel mapping
        channel_map = CHMAP.direct_inputs(DF.columns,"HUP1020")
        DF          = DF[channel_map]

        # Get the montage
        self.DF = CHMON.direct_inputs(DF,"HUP1020")

        # Get the time axis
        self.t_max = self.DF.shape[0]/self.fs
        if self.args.t0_frac != None:
            self.args.t0 = self.args.t0_frac*self.t_max
        if self.args.dur_frac != None:
            self.args.dur = self.args.dur_frac*self.t_max
        if self.args.t0 == None and self.args.t0_frac == None:
            self.args.t0 = 0
        if self.args.dur == None and self.args.dur_frac == None:
            self.args.dur = 10

        # Read in optional sleep wake power data if provided
        if self.args.sleep_wake_power != None:
            self.read_sleep_wake_data()
        else:
            self.t_flag = False

    def read_sleep_wake_data(self):

        # Read in the pickled data associations
        self.assoc_dict = pickle.load(open(self.args.sleep_wake_power,"rb"))

        # Get the relevant keys
        self.assoc_keys = (self.assoc_dict.keys())

        # Look to see if the current file is in the associations
        self.color_dict = {}
        for ikey in self.assoc_keys:
            fvals  = self.assoc_dict[ikey]['file'].values
            ufiles = np.unique(fvals)
            if self.fname in ufiles:
                inds = (fvals==self.fname)
                self.color_dict[ikey] = self.assoc_dict[ikey].iloc[inds]
        
        # Create a few variables to iterate through the dictionary as needed
        self.color_cnt  = 0
        self.color_keys = list(self.assoc_keys)
        self.ncolor     = len(self.color_keys)
        self.t_flag     = True
        self.t_colors   = ['r','b','g','m']

class data_viewer(data_handler):

    def __init__(self, infile, args, tight_layout_dict):
        
        # Save the input info
        self.infile            = infile
        self.fname             = infile.split('/')[-1]
        self.args              = args
        self.tight_layout_dict = tight_layout_dict

        # Some tracking variables
        self.sleep_counter   = 0
        self.spike_counter   = 0
        self.sleep_spike_str = '|'
        self.sleep_var       = ''
        self.spike_var       = ''

        # Get the approx screen dimensions and set some plot variables
        self.supsize = 18
        root         = tk.Tk()
        self.height  = 0.9*root.winfo_screenheight()/100
        self.width   = 0.9*root.winfo_screenwidth()/100
        root.destroy()

        # Save event driven variables
        self.xlim    = []
        self.drawn_y = []

        # Prepare the data
        data_handler.data_prep(self)

    def plot_sleep_wake(self):

        x_list = {}
        y_list = {}
        c_list = {}
        for ikey in self.color_keys:
            x_list[ikey] = {}
            y_list[ikey] = {}
            c_list[ikey] = {}
            iDF          = self.color_dict[ikey]

            # Loop over the channels and plot results
            for ichan in self.DF.columns:

                x_list[ikey][ichan] = []
                y_list[ikey][ichan] = []
                c_list[ikey][ichan] = []

                # Get the data stats 
                idata,ymin,ymax = self.get_stats(ichan)
                xvals           = np.arange(idata.size)/self.fs

                # Get the list of target info to iterate over
                values  = iDF[ichan].values
                uvalues = np.unique(values)
                uvalues = uvalues[(uvalues!=-1)]
                for ii,ivalue in enumerate(uvalues):

                    # Get the different boundaries
                    inds    = (values==ivalue)
                    t0_vals = iDF['t_start'].values[inds].astype('float')
                    t1_vals = iDF['t_end'].values[inds].astype('float')

                    # Loop over the times and then plot the scatter points
                    for itr in range(t0_vals.size):
                        inds_t = (xvals>=t0_vals[itr])&(xvals<=t1_vals[itr])
                        x_list[ikey][ichan].append(xvals[inds_t])
                        y_list[ikey][ichan].append(idata[inds_t])
                        c_list[ikey][ichan].append(self.t_colors[ii])
        return x_list,y_list,c_list

    def montage_plot(self):

        # Get the number of channels to plot
        nchan = self.DF.columns.size

        # Set the label shift. 72 points equals ~1 inch in pyplot
        width_frac = (0.025*self.width)
        npnt       = int(72*width_frac)
        
        # Create the plotting environment
        self.fig        = PLT.figure(dpi=100,figsize=(self.width,self.height))
        gs              = self.fig.add_gridspec(nchan, 1, hspace=0)
        self.ax_dict    = {}
        self.lim_dict   = {}
        self.shade_dict = {}
        self.xlim_orig  = [self.args.t0,self.args.t0+self.args.dur]
        xvals           = np.arange(self.DF.shape[0])/self.fs
        for idx,ichan in enumerate(self.DF.columns):
            # Define the axes
            if idx == 0:
                self.ax_dict[ichan] = self.fig.add_subplot(gs[idx, 0])
                self.refkey         = ichan
            else:
                self.ax_dict[ichan] = self.fig.add_subplot(gs[idx, 0],sharex=self.ax_dict[self.refkey])

            # Get the data stats 
            idata,ymin,ymax = self.get_stats(ichan)

            # Plot the data
            nstride = 8
            self.ax_dict[ichan].plot(xvals[::nstride],idata[::nstride],color='k')
            self.ax_dict[ichan].set_ylim([ymin,ymax])
            self.lim_dict[ichan] = [ymin,ymax]

            # Add in shading for the original axes limits
            self.shade_dict[ichan] = self.ax_dict[ichan].axvspan(self.xlim_orig[0], self.xlim_orig[1], facecolor='orange',alpha=0.2)

            # Clean up the plot
            for label in self.ax_dict[ichan].get_xticklabels():
                label.set_alpha(0)
            self.ax_dict[ichan].set_yticklabels([])
            self.ax_dict[ichan].set_ylabel(ichan,fontsize=12,rotation=0,labelpad=npnt)
            self.ax_dict[ichan].xaxis.grid(True)
        
        # X-axis cleanup
        self.refkey2 = ichan
        self.ax_dict[ichan].set_xlim(self.xlim_orig)

        # Plot and hide target data as needed
        self.t_obj = {}
        if self.t_flag:
            if self.args.sleep_wake_power != None:
                x_list,y_list,c_list = self.plot_sleep_wake()

                for ii,ikey in enumerate(list(x_list.keys())):
                    self.t_obj[ikey] = []
                    for ichan in list(x_list[ikey].keys()):
                        ix = x_list[ikey][ichan]
                        iy = y_list[ikey][ichan]
                        ic = c_list[ikey][ichan]
                        for jj in range(len(ix)):                       
                            self.t_obj[ikey].append(self.ax_dict[ichan].scatter(ix[jj],iy[jj],s=2,c=ic[jj],visible=False))

        # Add an xlabel to the final object
        self.ax_dict[self.refkey2].xaxis.set_major_locator(MultipleLocator(1))
        self.ax_dict[self.refkey2].set_xlabel("Time (s)",fontsize=14)
        for label in self.ax_dict[self.refkey2].get_xticklabels():
            label.set_alpha(1)


        # Set the title objects
        upa        = u'\u2191'  # Up arrow
        downa      = u'\u2193'  # Down arrow
        lefta      = u'\u2190'  # Left arrow
        righta     = u'\u2192'  # Right arrow
        self.title_str  = r"z=Zoom between mouse clicks; 'r'=reset x-scale; 'x'=Show entire x-axis; '0'=reset y-scale; 't'=Toggle targets; 'q'=quit current plot; 'Q'=quit the program entirely"
        self.title_str += '\n'
        self.title_str += r"'%s'=Increase Gain; '%s'=Decrease Gain; '%s'=Shift Left; '%s'=Shift Right; 'e'=Zoom-in plot of axis the mouse is on;" %(upa, downa, lefta, righta)
        if self.args.sleep_state or self.args.spike_state:
            self.title_str += '\n'
            if self.args.sleep_state:self.title_str += r"a=Sleep State Prediction; "
            if self.args.spike_state:self.title_str += r"p=Spike Presence Prediction;"
        self.title_str += '\n'
        self.ax_dict[self.refkey].set_title(self.title_str,fontsize=10)
        
        # Title info
        PLT.suptitle(self.fname,fontsize=self.supsize)
        
        # Layout handling using previous plot layout or find it for the first time
        if self.tight_layout_dict == None:
            self.fig.tight_layout()
        else:
            self.fig.subplots_adjust(**self.tight_layout_dict)
        
        # Even associations
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('key_press_event', self.update_plot)

        # Show the results
        PLT.show()

        # Update predictions if needed
        if self.args.sleep_state or self.args.spike_state:
            self.save_sleep_spike_state()
            
        # Store and return tight layout params for faster subsequent plots
        if self.tight_layout_dict == None:
            self.tight_layout_dict = {par : getattr(self.fig.subplotpars, par) for par in ["left", "right", "bottom", "top", "wspace", "hspace"]}
        return self.tight_layout_dict

    def enlarged_plot(self,channel):
        
        # Get the data view
        idata,ymin,ymax = self.get_stats(channel)
        xvals           = np.arange(idata.size)/self.fs

        # Get the current limits of the main viewer
        xlims = self.ax_dict[self.refkey].get_xlim()
        ylims = self.ax_dict[self.refkey].get_ylim()

        # Plot the enlarged view
        fig     = PLT.figure(dpi=100,figsize=(self.width,self.height))
        self.ax_enl = fig.add_subplot(111)
        self.ax_enl.plot(xvals,idata,color='k')
        self.ax_enl.set_xlabel("Time (s)",fontsize=14)
        self.ax_enl.set_ylabel(channel,fontsize=14)
        self.ax_enl.set_xlim(xlims)
        self.ax_enl.set_ylim(ylims)
        PLT.title(self.fname,fontsize=14)
        fig.tight_layout()
        PLT.show()

    ##########################
    #### Helper functions ####
    ##########################

    def get_stats(self,ichan):

        idata  = self.DF[ichan].values
        median = np.median(idata)
        stdev  = np.std(idata)
        idata -= median
        ymin   = -5*stdev
        ymax   = 5*stdev
        return idata,ymin,ymax

    def yscaling(self,ikey,dy):

        # Get the limits of the current plot for rescaling and recreating
        xlim      = self.ax_dict[ikey].get_xlim()
        ylim      = self.ax_dict[ikey].get_ylim()

        # Get the approximate new scale
        scale     = ylim[1]-ylim[0]
        ymin      = ylim[0]+dy*scale
        ymax      = ylim[1]-dy*scale

        # Get the data and limits with a good vertical offset
        vals      = self.DF[ikey].values
        inds      = (vals>=ymin)&(vals<=ymax)
        vals      = vals[inds]
        offset    = np.median(vals)
        vals     -= offset
        ymin     -= offset
        ymax     -= offset

        # Generate new limits
        self.ax_dict[ikey].set_ylim([ymin,ymax])

    def sleep_spike_toggle(self,options,index,counter,counter2):
        
        # Handle the counter logic
        counter += 1
        if counter == 4:
            counter = 0

        # Update the substring
        sleep_spike_arr        = self.sleep_spike_str.split('|')
        sleep_spike_arr[index] = options[counter]
        self.sleep_spike_str   = '|'.join(sleep_spike_arr)
        if counter == 0 and counter2 == 0:
            PLT.suptitle(f"{self.fname}",fontsize=self.supsize)
        else:
            stitle = PLT.suptitle(f"{self.fname} ({self.sleep_spike_str})",fontsize=self.supsize)
        return counter, options[counter]

    def save_sleep_spike_state(self):

        # Create output column list
        outcols = ['filename','assigned_t0','assigned_t1','username','sleep_state','spike_state','evaluated_t0','evaluated_t1']

        # Make the temporary dataframe to concat to outputs
        xlims = self.ax_dict[self.refkey2].get_xlim()
        iDF   = PD.DataFrame([[self.infile,self.xlim_orig[0],self.xlim_orig[1],self.args.username,self.sleep_var,self.spike_var,xlims[0],xlims[1]]],columns=outcols)

        # Check for file
        if path.exists(self.args.outfile):
            out_DF = PD.read_csv(self.args.outfile)
            out_DF = PD.concat((out_DF,iDF),ignore_index=True)
        else:
            out_DF = iDF

        # Save the results
        if not self.args.debug:
            out_DF.to_csv(self.args.outfile,index=False)

    ################################
    #### Event driven functions ####
    ################################

    def on_click(self,event):
        """
        Click driven events for the plot object.

        Args:
            Matplotlib event.
        """

        # Left click defines the zoom ranges
        if event.button == 1:
            # Loop over the axes and draw the zoom ranges
            for ikey in self.ax_dict.keys():
                self.drawn_y.append(self.ax_dict[ikey].axvline(event.xdata, color='red', linestyle='--'))
            
            # Redraw the plot to update the display
            PLT.draw()

            # Update the event driven zoom object
            self.xlim.append(event.xdata)

    def update_plot(self,event):
        """
        Key driven events for the plot object.

        Args:
            Matplotlib event.
        """

        # Zoom on 'z' press and when there are two bounds
        if event.key == 'z' and len(self.xlim) == 2:
            
            # Set the xlimits
            self.ax_dict[self.refkey].set_xlim(self.xlim)
            self.xlim = []

            # Remove the vertical lines on the plot
            for iobj in self.drawn_y:
                iobj.remove()
            self.draw_y = []
        # Reset the -axes of the plot
        elif event.key == 'r':
            self.ax_dict[self.refkey].set_xlim(self.xlim_orig)
            self.xlim = []
        # Increase gain
        elif event.key == 'up':
            for ikey in self.ax_dict.keys():
                self.yscaling(ikey,0.1)
        # Decrease gain
        elif event.key == 'down':
            for ikey in self.ax_dict.keys():
                self.yscaling(ikey,-0.1)
        # Shift back in time
        elif event.key == 'left':
            current_xlim = self.ax_dict[self.refkey].get_xlim()
            current_xlim = [ival-self.args.dur for ival in current_xlim]
            for ikey in self.ax_dict.keys():
                self.ax_dict[ikey].set_xlim(current_xlim)
        # Shift forward in time
        elif event.key == 'right':
            current_xlim = self.ax_dict[self.refkey].get_xlim()
            current_xlim = [ival+self.args.dur for ival in current_xlim]
            for ikey in self.ax_dict.keys():
                self.ax_dict[ikey].set_xlim(current_xlim)
        # Show the entire x-axis
        elif event.key == 'x':
            for ikey in self.ax_dict.keys():
                self.ax_dict[ikey].set_xlim([0,self.t_max])
        # Reset gain
        elif event.key == '0':
            for ikey in self.ax_dict.keys():
                self.ax_dict[ikey].set_ylim(self.lim_dict[ikey])
        # Enlarge a singular plot
        elif event.key == 'e':
            for ikey in self.ax_dict.keys():
                if event.inaxes == self.ax_dict[ikey]:
                    self.enlarged_plot(ikey)
        # Iterate over target dictionary if available to show mapped colors
        elif event.key == 't' and hasattr(self,'color_dict'):
            for icnt in range(len(self.t_colors)):
                ikey    = self.color_keys[icnt]
                objects = self.t_obj[ikey]
                for iobj in objects:
                    if icnt == self.color_cnt:
                        # Change visibility
                        iobj.set_visible(True)

                        # Update title
                        PLT.suptitle(self.fname+" | "+str(ikey),fontsize=self.supsize)
                    else:
                        iobj.set_visible(False)

            if self.color_cnt < self.ncolor:
                self.color_cnt += 1
            else:
                self.color_cnt = 0
                PLT.suptitle(self.fname,fontsize=self.supsize)
        # Sleep/awake event mapping
        elif event.key == 'a' and self.args.sleep_state:
            self.sleep_counter,self.sleep_var = self.sleep_spike_toggle(['','awake','sleep','unknown'],0,self.sleep_counter,self.spike_counter)
        # Spike State Mapping
        elif event.key == 'p' and self.args.spike_state:
            self.spike_counter,self.spike_var = self.sleep_spike_toggle(['','spikes','spike-free','unknown'],1,self.spike_counter,self.sleep_counter)
        # Quit functionality
        elif event.key == 'Q':
            PLT.close("all")
            sys.exit()

        # Make sure the axes colorscheme is updated
        newlim = self.ax_dict[self.refkey2].get_xlim()
        if (newlim[0] == self.xlim_orig[0]) and (newlim[1] == self.xlim_orig[1]):
            ialpha = 0.2
        else:
            ialpha = 0
        for ichan in self.DF.columns:
            self.shade_dict[ichan].set_alpha(ialpha)

        PLT.draw()

class CustomFormatter(argparse.HelpFormatter):
    """
    Custom formatting class to get a better argument parser help output.
    """

    def _split_lines(self, text, width):
        if text.startswith("R|"):
            return text[2:].splitlines()
        return super()._split_lines(text, width)

#####################
#### Helper Fncs ####
#####################

def make_help_str(idict):
    """
    Make a well-formated help string for the possible keyword mappings

    Args:
        idict (dict): Dictionary containing the allowed keywords values and their explanation.

    Returns:
        str: Formatted help string
    """

    return "\n".join([f"{key:15}: {value}" for key, value in idict.items()])

if __name__ == '__main__':

    # Argument option creation
    allowed_channel_args    = {'HUP1020': "Channels associated with a 10-20 montage performed at HUP.",
                               'RAW': "Use all possible channels. Warning, channels may not match across different datasets."}
    allowed_montage_args    = {'HUP1020': "Use a 10-20 montage.",
                               'COMMON_AVERAGE': "Use a common average montage."}
    
    # Pretty argument string creation
    allowed_channel_help   = make_help_str(allowed_channel_args)
    allowed_montage_help   = make_help_str(allowed_montage_args)

    # Command line options needed to obtain data.
    parser = argparse.ArgumentParser(description="Simplified data merging tool.", formatter_class=CustomFormatter)

    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--file", type=str, help="Input file to plot.")
    input_group.add_argument("--wildcard", type=str, help="Wildcard enabled path to plot multiple datasets.")

    output_group = parser.add_argument_group('Output options')
    output_group.add_argument("--outfile", type=str, help="Output filepath if predicting sleep/spikes/etc.")
    output_group.add_argument("--username", type=str, help="Username to tag any outputs with.")

    prep_group = parser.add_argument_group('Data preparation options')
    prep_group.add_argument("--channel_list", choices=list(allowed_channel_args.keys()), default="HUP1020", help=f"R|Choose an option:\n{allowed_channel_help}")

    time_group = parser.add_mutually_exclusive_group()
    time_group.add_argument("--t0", type=float, help="Start time to plot from in seconds.")
    time_group.add_argument("--t0_frac", type=float, help="Start time to plot from in fraction of total data.")

    duration_group = parser.add_mutually_exclusive_group()
    duration_group.add_argument("--dur", type=float, help="Duration to plot in seconds.")
    duration_group.add_argument("--dur_frac", type=float, help="Duration to plot in fraction of total data.")

    misc_group = parser.add_argument_group('Misc options')
    misc_group.add_argument("--debug", action='store_true', default=False, help="Debug mode. Save no outputs.")
    misc_group.add_argument("--sleep_wake_power", type=str, help="Optional file with identified groups in alpha/delta for sleep/wake patients")
    misc_group.add_argument("--pickle_load", action='store_true', default=False, help="Load from pickled tuple of dataframe,fs.")
    misc_group.add_argument("--sleep_state", action='store_true', default=False, help="Query user for sleep state.")
    misc_group.add_argument("--spike_state", action='store_true', default=False, help="Query user for spike freedom.")
    args = parser.parse_args()

    # Get username and output path if needed
    if args.sleep_state or args.spike_state:
        if args.username == None:
            args.username = input("Please enter a username for tagging data: ")
        if args.outfile == None:
            args.outfile = './edf_annotations.csv'
    else:
        args.outfile = ''

    # Create the file list to read in
    if args.file != None:
        files = [args.file]
    else:
        files = glob.glob(args.wildcard)

    # Use the output file to skip already reviewed files for state analysis
    if path.exists(args.outfile):
        ref_DF = PD.read_csv(args.outfile)
    else:
        ref_DF = PD.DataFrame(columns=['filename','username'])

    # Iterate over the data and create the relevant plots
    tight_layout_dict = None
    for ifile in files:
        
        # Check if this user has already reviewed this data
        iDF   = ref_DF.loc[(ref_DF.username==args.username)&(ref_DF.filename==ifile)]
        if iDF.shape[0] == 0:
            try:
                DV = data_viewer(ifile,args,tight_layout_dict)
                tight_layout_dict = DV.montage_plot()
                PLT.close("all")
            except:
                pass
            

