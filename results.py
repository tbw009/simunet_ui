"""Results plotting UI for simulation output with interactive chart configuration."""

import ttkbootstrap as ttk
import ttkbootstrap.constants as tk
from ttkbootstrap import utils
from tkinter import messagebox
from project import Project
from pytexit import py2tex
from propertygrid import PropertyGrid
from propertydescriptor import PropertyDescriptor
from resultconfig import ResultConfig
from cycler import cycler
from toolbar import Toolbar
from images import Images
import matplotlib
import matplotlib.style
import mplcursors
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib import colormaps
from cycler import cycler

matplotlib.use("TkAgg")
matplotlib.style.use("fast")


class Results(ttk.Frame):
    """Frame that renders simulation results, chart controls, and configuration."""

    def __init__(self, master, **kwargs):
        """Initialize the results view, chart canvas, toolbar, and state."""
        super().__init__(master, **kwargs)
        
        # Create toolbar images
        self.images = Images().ribbon

        # Create result config
        self.config_list = [ResultConfig()]
        self.config = self.config_list[0]

        # Create a figure
        self.figure = Figure(figsize=(12,9), tight_layout=True)

        # Create FigureCanvasTkAgg object
        self.figure_canvas = FigureCanvasTkAgg(figure=self.figure, master=self)
        self.figure_canvas._update_device_pixel_ratio()

        # Pack wrapper widget into the host frame
        self.figure_canvas_widget=self.figure_canvas.get_tk_widget()
        self.figure_canvas_widget.grid(row=1, column=0, sticky=tk.NSEW)

        # Create a NavigationToolbar2Tk an override the set_history_buttons function
        # Don't pack the toolbar because we use our ribbon to host our own buttons
        self.mpl_tb = NavigationToolbar2Tk(self.figure_canvas, self.figure_canvas_widget, pack_toolbar=False)
        
        # Set interactive cursor to None
        self.cursor = None
        
        # Create toolbar
        self.create_toolbar()
        self.toolbar.grid(row=0, column=0, sticky=tk.NSEW)
        self.toolbar_visible = True

        # Bind the selction changed event of the chart combo
        self.cmb_chart.bind("<<ComboboxSelected>>", self.on_cmb_chart_selected)
        self.figure.canvas.mpl_connect("pick_event", self.on_pick)
 
        # Configure grid rows and columns
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # The project
        self.project = None
        
        # Frame border visibility
        self.frames_border_visible = True
        
        # Update the toolbar
        self.update_ui()

    def create_toolbar(self):
        """Create the ribbon toolbar and chart selection controls."""
        tb_items=[
            ("Refresh", "Refresh", "Refresh", "Refresh the drawing area", self.on_refresh),
            "---",
            ("ChartAdd", "ChartAdd", "Add", "Add a new config to the list of configurations", self.on_add_config),
            ("ChartRemove", "ChartRemove", "Remove", "Remove the current config from the list of configurations", self.on_remove_config),
            ("Eraser", "Eraser", "Reset", "Reset the current chart config to default", self.on_reset),
            "---",
            ("Reset", "Reset", "Reset view", "Reset the view to default", self.on_home),
            ("Back", "Back", "Back", "Go to the previous view", self.on_back),
            ("Forward", "Forward", "Forward", "Go to the next view", self.on_forward),
            "---",
            ("Pan", "Pan", "Pan", "Pan the view", self.on_pan),
            ("Zoom", "Zoom", "Zoom", "Zoom to rectangle", self.on_zoom),
            "---",
        ]

        # Create the toolbar
        self.toolbar = Toolbar(self, self.images, tb_items, show_text=True)

        # Add config frame
        frame = ttk.Frame(self.toolbar)
        frame.pack(before=self.toolbar.tb_widgets["ChartAdd"], side=tk.LEFT, padx=10)

        # Add a label
        self.lbl_chart = ttk.Label(
            frame, text="Charts: ")
        self.lbl_chart.pack(side=tk.LEFT, fill=tk.Y) 

        # Add the chart combobox
        self.cmb_chart = ttk.Combobox(frame, state=tk.READONLY)
        self.cmb_chart.pack(side=tk.LEFT)

        # Create a separator
        sep = ttk.Separator(self.toolbar, orient=tk.VERTICAL)
        sep.pack(after=frame, side=tk.LEFT, fill=tk.Y)

        # Set history buttons of the matplotlib toolbar of the result widget
        # to ensure a correct ui updating by the NavigationToolbar2Tk
        self.mpl_tb._buttons["Home"] = self.toolbar.tb_widgets["Reset"]
        self.mpl_tb._buttons["Back"] = self.toolbar.tb_widgets["Back"]
        self.mpl_tb._buttons["Forward"] = self.toolbar.tb_widgets["Forward"]
    
    def on_toggle_toolbar(self):
        """Show or hide the results toolbar."""
        if self.toolbar_visible:
            self.toolbar.grid_remove()
            self.toolbar_visible = False
        else:
            self.toolbar.grid()
            self.toolbar_visible = True

    def on_pick(self, event):
        """Toggle visibility of the picked legend entry in the result plot."""
        legend_line = event.artist
        if legend_line in self.line_map:
            orig_line = self.line_map[legend_line]
            visible = not orig_line.get_visible()
            orig_line.set_visible(visible)

            # Change the alpha on the line in the legend, so we can see what lines
            # have been toggled.
            legend_line.set_alpha(1.0 if visible else 0.2)
        self.figure.canvas.draw()

    def create_plot(self):
        """Recreate the matplotlib plot using the current project and config."""
        self.figure.clear()
        self.figure.set_facecolor(self.config.face_color)

        # get font color
        text_color = utils.contrast_color(self.config.face_color, model=utils.HEX)

        # Create axes
        axis_y1 = self.figure.add_subplot()
        axis_y1.spines['bottom'].set_color(text_color)
        axis_y1.spines['top'].set_color(text_color) 
        axis_y1.spines['right'].set_color(text_color)
        axis_y1.spines['left'].set_color(text_color)        
        axis_y2 = None

        # Set face color
        axis_y1.set_facecolor(self.config.face_color)
        lines = []
        markersize = self.config.markersize

        # Ensure we have a valid project
        if self.project:
            if len(self.project.result) > 0:
                # Create prop cycler for colors and markers
                colors = cycler(color=list(colormaps.get_cmap(self.config.colormap).colors))()
                markers = cycler(marker=["o", "s", "D", "v", "^", "<", ">", "x", "+", "." ])()
                # Create a list for the axis labels
                y_labels = []

                if self.config.show_frame_limits:
                    # Retrieve the finished, reastarted an canceled frames from the data
                    frame_limits = [(row[3], row[4]) for row in self.project.statistics if row[2] == "Finished"]
                    
                    # Draw frame borders
                    for entry in frame_limits:
                        axis_y1.axvline(x=entry[0], color=self.config.frame_limits_color, 
                                        linestyle=self.config.frame_limits_style, 
                                        linewidth=self.config.frame_limits_line_width)
                    if len(frame_limits) > 0:
                        axis_y1.axvline(x=frame_limits[-1][-1], color=self.config.frame_limits_color, 
                                        linestyle=self.config.frame_limits_style, 
                                        linewidth=self.config.frame_limits_line_width)

                # Plot the lines for the left y axis
                for model_id, var_id in self.config.y1_var_ids:
                    if model_id not in self.project.result:
                        continue
                    if var_id not in self.project.result[model_id]["vars"]:
                        continue

                    # Get the model data
                    model_data = self.project.result[model_id]

                    # Get time frame and values
                    t_frame = model_data["t"]
                    values = model_data["vars"][var_id]["value"]
                    
                    # Create an axis label
                    axis_label ="{} ({} of {} in [{}])".format(
                        py2tex(var_id, print_latex=False, print_formula=False, tex_enclosure="$"),
                        model_data["vars"][var_id]["description"],
                        model_data["name"],
                        model_data["vars"][var_id]["unit"]
                    )
                    
                    # Get the next color and marker from the cycler
                    col = next(colors)["color"]
                    sym = next(markers)["marker"] if self.config.y1_show_markers else None

                    # Plot data and use time frame if len of lists are 
                    # identical, otherwise plot only the points
                    if len(t_frame) == len(values):
                        mark = int(len(t_frame)/10)
                        line = axis_y1.plot(
                            t_frame, values, color=col, marker=sym, 
                            markevery=mark, markersize=markersize, label=axis_label, 
                            linewidth=self.config.y1_line_width)
                    else:
                        mark = int(len(values)/10)
                        line = axis_y1.plot(
                            values, color=col, marker=sym, 
                            markevery=mark, markersize=markersize, label=axis_label, 
                            linewidth=self.config.y1_line_width)
                    
                    # Apppend the line
                    lines+=line
                    
                    # Append the axis label
                    y_labels.append("{} ({})".format(
                        py2tex(var_id, print_latex=False, print_formula=False, 
                        tex_enclosure="$"), model_data["name"])) 
                    
                # Create axes labels
                labels = ", ".join(y_labels)
                axis_y1.set_ylabel(labels, color=text_color)

                # If we have vars configured for the right y-axis...
                if len(self.config.y2_var_ids) > 0:
                    # Create second y axis on the right with the same x-axis
                    axis_y2 = axis_y1.twinx()
                    axis_y2.spines['bottom'].set_color(text_color)
                    axis_y2.spines['top'].set_color(text_color) 
                    axis_y2.spines['right'].set_color(text_color)
                    axis_y2.spines['left'].set_color(text_color)                            

                    # Create a list for the axis labels
                    y2_labels = []
                    
                    # Plot the lines
                    for model_id, var_id in self.config.y2_var_ids:
                        if model_id not in self.project.result:
                            continue
                        if var_id not in self.project.result[model_id]["vars"]:
                            continue
                        # Get the model data
                        model_data = self.project.result[model_id]

                        # Get time frame an values
                        t_frame = model_data["t"]
                        values = model_data["vars"][var_id]["value"]
                        
                        # Create an axis label
                        axis_label ="{} ({} of {} in [{}])".format(
                            py2tex(var_id, print_latex=False, print_formula=False, tex_enclosure="$"),
                            model_data["vars"][var_id]["description"],
                            model_data["name"],
                            model_data["vars"][var_id]["unit"]
                        )
                        
                        # Get the next color and marker from the cycler
                        col = next(colors)["color"]
                        sym = next(markers)["marker"] if self.config.y2_show_markers else None

                        # Plot data and use time frame if len of lists are 
                        # identical, otherwise plot only the points
                        if len(t_frame) == len(values):
                            mark = int(len(t_frame)/10)
                            line = axis_y2.plot(
                                t_frame, values, color=col, marker=sym, 
                                markevery=mark, markersize=markersize, label=axis_label, 
                                linewidth=self.config.y2_line_width)
                        else:
                            mark = int(len(values)/10)
                            line = axis_y2.plot(
                                values, color=col, marker=sym, 
                                markevery=mark, markersize=markersize, label=axis_label, 
                                linewidth=self.config.y2_line_width)

                        # Apppend the line
                        lines+=line

                        # Append the axis label
                        y2_labels.append("{} ({})".format(
                            py2tex(var_id, print_latex=False, print_formula=False, 
                            tex_enclosure="$"), model_data["name"])) 

                    # Create labels for the right y-axis
                    labels = ", ".join(y2_labels)
                    axis_y2.set_ylabel(labels, color=text_color)

                # Update legend
                if self.config.show_legend and len(lines) > 0:
                    legend = None
                    if axis_y2:
                        # Get handles and labels
                        handles1, labels1 = axis_y1.get_legend_handles_labels()
                        handles2, labels2 = axis_y2.get_legend_handles_labels()

                        # Add legend
                        legend = axis_y2.legend(
                            handles1+handles2, 
                            labels1+labels2, 
                            loc=self.config.legend_position,
                            facecolor=self.config.face_color,
                            labelcolor=text_color)
                    elif len(self.config.y1_var_ids) > 0:
                        legend = axis_y1.legend(
                            loc=self.config.legend_position, 
                            labelcolor=text_color)
                    
                    # Map legend lines to original lines
                    if legend:
                        self.line_map = {} 
                        for legend_line, orig_line in zip(legend.get_lines(), lines):
                            self.line_map[legend_line] = orig_line
                            # Enable picking on the legend line
                            legend_line.set_picker(5)  

        # Create x.axis labels
        axis_y1.set_xlabel(self.config.x_axis_label, color=text_color)

        # Set axis scale
        axis_y1.set_xscale(self.config.x_scale)
        if self.config.x_scale == "linear":
            axis_y1.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
        
        # Update the x-grid 
        if self.config.show_x_grid:
            axis_y1.xaxis.grid(
                visible=True, 
                which=self.config.x_grid_which,
                color=self.config.x_grid_color,
                linestyle= self.config.x_grid_style)
        else:
            axis_y1.xaxis.grid(visible=False)

        # Chart title
        if self.config.show_chart_title:
            axis_y1.set_title(
                self.config.chart_title, 
                loc=self.config.chart_title_position, 
                color=text_color)

        # Set y1-axis scale
        axis_y1.set_yscale(self.config.y1_scale)
        if self.config.y1_scale == "linear":
            axis_y1.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
        
        # Update the y1-axis grid 
        if self.config.show_y1_grid:
            axis_y1.yaxis.grid(
                visible=True, 
                which=self.config.y1_grid_which,
                color=self.config.y1_grid_color,
                linestyle= self.config.y1_grid_style)
        else:
            axis_y1.yaxis.grid(visible=False)

        # Change tick label colors too
        axis_y1.tick_params(axis='x', colors=text_color)
        axis_y1.tick_params(axis='y', colors=text_color)

        if axis_y2:
            # Set y2-axis scale
            axis_y2.set_yscale(self.config.y2_scale)
            if self.config.y2_scale == "linear":
                axis_y2.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
            
            # Update the y2-axis-grid 
            if self.config.show_y2_grid:
                axis_y2.yaxis.grid(
                    visible=True, 
                    which=self.config.y2_grid_which,
                    color=self.config.y2_grid_color,
                    linestyle= self.config.y2_grid_style)
            else:
                axis_y2.yaxis.grid(visible=False)

            # Change tick label colors too
            axis_y2.tick_params(axis='x', colors=text_color)
            axis_y2.tick_params(axis='y', colors=text_color)

        # Enable interactive cursor with tooltip
        if self.cursor:
            self.cursor.remove()
        self.cursor = mplcursors.Cursor(
            artists=lines,
            #multiple=True,
            annotation_kwargs={
                "color": ttk.Style().colors.inputfg,
                "bbox":{
                    "facecolor": ttk.Style().colors.inputbg,
                    "edgecolor": ttk.Style().colors.dark,                   
                    "alpha": 0.8, 
                    "pad": 2
                },
                "arrowprops": {
                    "connectionstyle": "arc3",
                    "arrowstyle": "-|>"
                }
            }, 
            hover=False)
    
        # Redraw canvas
        self.figure_canvas.draw_idle()
   
    def set_project(self, project):
        """Set the current project and load its stored result chart configurations."""
        if project is self.project:
            self.create_plot()
        else:
            self.project = project

            # Deserialize configs
            self.config_list = []
            for item in project.configs:
                self.config_list.append(ResultConfig.from_data(item))

            # Create a default config
            if len(self.config_list) == 0:
                self.on_add_config()

            # Select the first config
            self.set_config(0)
            # Update the combobox
            self.update_cmb_chart()

        self.update_ui()

    def update_project(self):
        """Save the current chart configurations back into the project model."""
        self.project.configs = []
        # Append the attributes of each config 
        # in the the config list of this instance
        for config in self.config_list:
            self.project.configs.append(config.__dict__)

    def set_config(self, index):
        """Select a chart config by index and replot the results."""
        if index < len(self.config_list):
            # Retrive config
            self.config = self.config_list[index]
            # Recreate polt
            self.create_plot()
            # Generate <<ConfigChanged>> event
            self.event_generate("<<ConfigSelected>>")

    def update_cmb_chart(self):
        """Refresh the chart selection combobox with the current config list."""
        self.cmb_chart["values"] = self.config_list
        # Set the current selection to the selected config index
        self.cmb_chart.current(self.config_list.index(self.config))

    def on_cmb_chart_selected(self, event):
        """Handle selection changes from the chart configuration dropdown."""
        index = self.cmb_chart.current()
        # Activate the config
        self.set_config(index)

    def on_refresh(self):
        """Redraw the chart using the current configuration."""
        self.create_plot()

    def on_reset(self):
        """Reset the current chart configuration to the defaults after confirmation."""
        res = messagebox.askyesnocancel(
            message="Do you really want to reset the current chart configuration?", 
            title="Reset configuration '{}'".format(self.config.chart_title), 
            parent=self)
        if res == True:

            # Reset the current config
            self.config.default()
            # Update the combobox
            self.update_cmb_chart()
            # Recreate polt
            self.create_plot()
            # Generate the <<ConfigAdded>> event
            self.event_generate("<<ConfigChanged>>")      

    def on_add_config(self):
        """Add a new result chart configuration and select it."""
        self.config_list.append(ResultConfig())
        # Get the index of the newly aded config
        index = len(self.config_list)-1
        # Activate the config
        self.set_config(index)
        # Update the combobox
        self.update_cmb_chart()
        # Generate the <<ConfigAdded>> event
        self.event_generate("<<ConfigAdded>>")      
        # Finally update the toolbar
        self.update_ui()

    def on_remove_config(self):
        """Remove the currently selected chart configuration after confirmation."""
        if len(self.config_list) > 1:
            # Commit deleting
            res = messagebox.askyesnocancel(
                message="Do you really want to delete the current chart configuration?", 
                title="Delete configuration '{}'".format(self.config.chart_title), 
                parent=self)
            if res == True:
                # Delete active config
                index = self.config_list.index(self.config)
                self.config_list.remove(self.config)
                index = min(index, len(self.config_list)-1)
                self.set_config(index)
                self.update_cmb_chart()
                self.event_generate("<<ConfigDeleted>>")      
                self.update_ui()

    def on_home(self):
        """Reset the view to the default chart navigation state."""
        self.mpl_tb.home()
        self.update_ui()

    def on_back(self):
        """Navigate to the previous view in the matplotlib navigation stack."""
        self.mpl_tb.back()
        self.update_ui()

    def on_forward(self):
        """Navigate to the next view in the matplotlib navigation stack."""
        self.mpl_tb.forward()
        self.update_ui()

    def on_pan(self):
        """Enable panning mode for the chart."""
        self.mpl_tb.pan()
        self.update_ui()
        
    def on_zoom(self):
        """Enable rectangular zoom mode for the chart."""
        self.mpl_tb.zoom()
        self.update_ui()
    
    def on_save(self):
        """Save the current figure using the matplotlib toolbar save dialog."""
        self.mpl_tb.save_figure()

    def update_ui(self):
        """Update toolbar state based on navigation and configuration availability."""
        can_back = self.mpl_tb._nav_stack._pos > 0
        self.toolbar.set_enabled("Back", can_back)
        can_forward = self.mpl_tb._nav_stack._pos < len(self.mpl_tb._nav_stack._elements) - 1
        self.toolbar.set_enabled("Forward", can_forward)

        self.toolbar.set_enabled("ChartRemove", len(self.config_list)>1) 
        self.toolbar.set_enabled("Eraser", len(self.config.y1_var_ids) or len(self.config.y2_var_ids))
        self.toolbar.set_checked("Zoom", self.mpl_tb.mode == "zoom rect")
        self.toolbar.set_checked("Pan", self.mpl_tb.mode == "pan/zoom")

    def fill_propertygrid(self, propertygrid: PropertyGrid):
        """Populate the property grid with the current configuration options."""
        self.config.fill_propertygrid(propertygrid, self.project.result)

    def update_value(self, propertygrid: PropertyGrid):
        """Apply edited configuration values and refresh the chart."""
        self.config.update_value(propertygrid)
        # Update the combobox 
        self.update_cmb_chart()
        # Recreate plot
        self.create_plot()

if __name__ == "__main__":
    # Create app window
    app = ttk.Window(hdpi=True)

    project = Project()
    project.load("./projects/controller_2L.sim")

    # Create splitter pane
    pane = ttk.Panedwindow(app, orient=tk.HORIZONTAL, width=800)
    pane.pack(fill=tk.BOTH, expand=tk.YES)

    # Create result frame
    res = Results(pane)
    res.set_project(project)
    pane.add(res, weight=1)
  
    # Create right splitter pane
    pane_right = ttk.Panedwindow(app, orient=tk.VERTICAL, width=400)
    pane.add(pane_right, weight=0)

    # Create Property Grid
    propertygrid = PropertyGrid(pane_right, height=600)
    pane_right.add(propertygrid, weight=1)

    # Create poperty description
    prop_descriptor = PropertyDescriptor(pane_right, height=200)
    propertygrid.prop_descriptor = prop_descriptor
    pane_right.add(prop_descriptor, weight=0)

    # Bind a simple lambda expression to the ConfigSelected event
    # This lambda simply reselects the result instance in the property grid.
    # It's necessary for updating the configurations and is typically done by the app
    res.bind("<<ConfigSelected>>", lambda _: propertygrid.set_selected_object(res))

    # Set selected object
    propertygrid.set_selected_object(res)

    app.geometry("1200x800+100+100")
    res.create_plot()
    app.mainloop()