import os
import re
import matplotlib.pyplot as plt
import webbrowser

from shiny import App, render, ui, reactive

import nest_asyncio
nest_asyncio.apply()

from .preprocess_signals import emg_to_psd
from .access_files import *

#
# =============================================================================
#

"""
A collection of functions for plotting data.
"""

#
# =============================================================================
#

def plot_dashboard(path_names:dict, col:str, units:str, file_ext:str='csv', use_mask:bool=False, auto_run:bool=True):
    """
    Generate a Shiny dashboard of different processing stages for a given
    column of signal data.
    
    'CTRL + C' can be entered in the terminal to end the display of the
    dashboard and resume code execution.

    Parameters
    ----------
    path_names : dict-str
        A dictionary of file locations with keys for stage in the processing
        pipeline. The function will generate graphs for as many paths are
        provided in the dictionary. The dictionary can be created with the
        'make_paths' function.
    col : str
        The column of the signals to display in the visualization.
    units : str
        Units to use for the y axis of the plot, should be the same units used
        for the values in 'col'.
    file_ext : str, optional
        File extension for files to read. Only visualizes files with this
        extension. The default is 'csv'.
    use_mask : bool, optional
        An option to visualize the NaN mask If True, it will set values to NaN
        based on the NaN mask. If False, it will use the unaltered values of
        the column ignoring the NaN mask. The default is False.
    auto_run : bool, optional
        An option to automatically see the visualization. If True, it will run
        the visual and open it in the default browser. If False, it will return
        the visualization object. The default is True.

    Raises
    ------
    Exception
        An exception is raised if 'col' is not a column of a signal file.
    
    Exception
        An exception is raised if a file contained in the first file directory
        (path_names[0]) is not found in the other file directories.
    
    Exception
        An exception is raised if a file could not be read.
    Exception
        An exception is raised if an unsupported file format was provided for
        'file_ext'.

    Returns
    -------
    app : None, shiny.App
        If 'auto_run' is True, returns None. If False, returns a shiny.App
        instance.

    """
    
    # Remove feature path, and convert dictionary to lists
    path_names = path_names.copy()
    path_names.pop("Feature", None)
    
    # Try to load from each available file location
    names = list(path_names.keys())
    file_dirs = []
    for name in names:
        if not bool(os.listdir(path_names[name])):
            path_names.pop(name, None)
    
    in_paths = list(path_names.values())
    names = list(path_names.keys())
    file_dirs = []
    
    for path in in_paths:
        file_dirs.append(map_files(path))
    
    df = map_files_fuse(file_dirs, names)
    
    # Set style
    plt.style.use('fivethirtyeight')
    
    # Get colours based on number of paths being plotted
    n = len(path_names)
    cmap = plt.cm.get_cmap('viridis', n)
    colours = [cmap(i) for i in reversed(range(n))]
    
    # Create shiny dashboard
    
    # =============
    # UI definition
    # =============
    app_ui = ui.page_fluid(
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_select('sig_type', 'Signal Displayed:', choices=['All']+names),
                ui.input_select('file_type', 'File:', choices=df['File']),
                ui.input_slider('x_range', 'X-Axis Range:', min=0, max=1, value=[0, 1]),
                ui.input_slider('y_range', 'Y-Axis Range:', min=0, max=1, value=[0, 1])
            ),
            ui.card(
                ui.output_plot('plt_signal'),
            ),
        ),
    )
    
    # Create legend names and order label
    legnames = names.copy()
    for i in range(len(legnames)):
        legnames[i] = str(i+1) + ': ' + legnames[i]
    
    # =================
    # Server definition
    # =================
    def server(input, output, session):
        @reactive.effect
        def update_x_slider():
            filename = input.file_type()
            column = input.sig_type()
        
            if column == 'All':
                min_x = float('inf')
                max_x = float('-inf')
                min_y = float('inf')
                max_y = float('-inf')
                
                for file_loc in list(df.loc[filename])[1:]:
                    data = read_file_type(file_loc, file_ext)
                    
                    min_x = min(min_x, data['Time'].min())
                    max_x = max(max_x, data['Time'].max())
                    min_y = min(min_y, data[col].min())
                    max_y = max(max_y, data[col].max())
                    
            else:
                file_location = df.loc[filename][column]
                data = read_file_type(file_location, file_ext)
                max_x = data['Time'].max()
                min_x = data['Time'].min()
                max_y = data[col].max()
                min_y = data[col].min()
        
            ui.update_slider("x_range", min=min_x, max=max_x, value=[min_x, max_x])
            ui.update_slider("y_range", min=min_y, max=max_y, value=[min_y, max_y])


        
        @render.plot
        def plt_signal():
            filename = input.file_type()
            column = input.sig_type()
            x_min, x_max = input.x_range()  # Get slider values
            y_min, y_max = input.y_range()

            
            # Plot data
            fig, ax = plt.subplots()
            if column == 'All':
                # Read/plot each file
                file_locs = list(df.loc[filename])[1:]
                for i in range(len(file_locs)):
                    file_loc = file_locs[i]
                    sigDF = read_file_type(file_loc, file_ext)
                    
                    # Exception for column input
                    if col not in list(sigDF.columns.values):
                        raise Exception("Column " + str(col) + " not in Signal " + str(filename))
                    
                    ax.plot(sigDF['Time'], sigDF[col], color=colours[i], alpha=0.5, linewidth=1)
                    
                # Set legend for multiple plots
                ax.legend(legnames)
            else:
                # Read/plot single file
                file_location = df.loc[filename][column]
                sigDF = read_file_type(file_location, file_ext)
                
                # Exception for column input
                if col not in list(sigDF.columns.values):
                    raise Exception("Column " + str(col) + " not in Signal " + str(filename))
                
                # Get colour data
                i = names.index(column)
                # Plot file
                ax.plot(sigDF['Time'], sigDF[col], color=colours[i], alpha=0.5, linewidth=1)
                
            ax.set_xlim(x_min, x_max)
            ax.set_ylim(y_min, y_max)
            ax.set_ylabel('Voltage (mV)')
            ax.set_xlabel('Time (s)')
            ax.set_title(column + ' filter: ' + filename)
            
            return fig
    
    app = App(app_ui, server)
    
    if auto_run:
        webbrowser.open('http://127.0.0.1:8000')
        app.run()
        return
    else:
        return app