"""Main application window for the simunet UI.

This module defines the SimunetApp class, which constructs the main
application window including project management, simulation control,
stateful toolbars, property grids, output consoles, and export features.
"""

import logging
import traceback
import ttkbootstrap as ttk
import ttkbootstrap.constants as tk
import multiprocessing
import copy
import os
from simunetcore import logger
from simunetcore import __version__ as COREVERSION
from tkinter import filedialog
from appconfig import AppConfig, AppConfigDlg
from output import Output
from diagram import Diagram
from about import AboutDlg, URLS
from repository import Repository
from project import Project
from propertygrid import PropertyGrid
from propertydescriptor import PropertyDescriptor
from ribbon import RibbonBar
from results import Results
from launcher import WaveformLauncher
from images import Images
from PIL import ImageTk
from export import export_excel
from tkinter import messagebox
from matplotlib import rcParams


class SimunetApp(ttk.Window):
    """Root window for the simunet graphical user interface."""
    
    def __init__(self, **kwargs):
        """Initialize the main application window and load configuration."""
        super().__init__(**kwargs)

        self.withdraw()
        self.suspend_update = False
     
        self.userdir = os.path.join(os.path.expanduser("~"), ".simunet")
        self.check_first_start()
        
        # Set App title and create additional styles
        self.title("simunet®")

        # Register simunet themes and the additional styles
        ttk.Theme(
            name="simunet",
            primary="#0f6ebe", secondary="#aeb8c2",
            success="#02b875", info="#17a2b8",
            warning="#f0ad4e", danger="#d9534f",
            light=dict(background="#ffffff", foreground="#343a40"),
            dark=dict(background="#343a40", foreground="#ffffff"),
        ).register()

        # Simulation process object
        self.wfr_process = None

        # Read config
        self.app_config = AppConfig.from_file(os.path.join(self.userdir, "config.json"))
        rcParams["font.sans-serif"] = self.app_config.rc_params["font.sans-serif"]
        rcParams["font.size"] =  self.app_config.rc_params["font.size"]

        # Set geometry
        self.geometry("1200x800+100+100")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        # Call update to update geometry
        self.update()

        # The simulation project
        self.project = Project()
        self.project_path = None
        self.is_dirty = False

        # Create theme var
        self.theme = ttk.StringVar()

        # Create window
        self.create_window()  

        # Hook into exceptions
        self.report_callback_exception = self.log_exception

        # Apply icon
        icon = ImageTk.PhotoImage(file="./images/app.png", master=self)
        self.iconphoto(True, icon)

        # Create new document
        self.on_new()

        # Call update to update widgets
        self.update()

        # Set slider positions
        self.after(100, lambda: self.load_pane_states({
            "pane": self.pane, 
            "pane_middle": self.pane_middle, 
            "pane_right": self.pane_right}))

        # Set the theme
        self.theme.set(self.app_config.style["themename"])

        # Everything is prepared, so deiconify the window
        self.deiconify()
 
    def check_first_start(self):
        """Create the user config folder and default config file if needed."""
        if not os.path.exists(self.userdir):
            os.mkdir(self.userdir)
            logger.info("Created config path '{}'.".format(self.userdir))

        config_file = os.path.join(self.userdir, "config.json")
        if not os.path.exists(config_file):
            AppConfig().dump(config_file)

    def log_exception(self, *args):
        """Log uncaught exceptions to the application logger."""
        print(traceback.format_exc())
        callstack = traceback.format_exception(*args)
        logger.error(callstack[-1])

    def save_pane_states(self, paned_windows):
        """
        Save sash positions for multiple PanedWindows.
        paned_windows: dict {name: PanedWindow}
        """
        states = {}
        try:
            for name, pw in paned_windows.items():
                # Store all sash positions for this PanedWindow
                sash_positions = []
                for i in range(len(pw.panes()) - 1):
                    sash_positions.append(pw.sashpos(i))
                states[name] = sash_positions
                self.app_config.pane_states = states

        except Exception as e:
            print("Error saving pane state:", e)

    def load_pane_states(self, paned_windows):
        """
        Load sash positions for multiple PanedWindows.
        paned_windows: dict {name: PanedWindow}
        """
        try:
            for name, pw in paned_windows.items():
                if name in self.app_config.pane_states:
                    for i, pos in enumerate(self.app_config.pane_states[name]):
                        pw.sashpos(i, pos)
        except Exception as e:
            print("Error loading pane state:", e)

    def create_toolbar(self):
        """Build the main ribbon toolbar and theme menu controls."""

        # id, image, text, tooltip, callback
        ribbon_items = {
            "Start": {
                "Project" : [
                    ("New", "New", "New", "New Document (Strg+N)", self.on_new),
                    ("Open", "Open", "Open", "Open existing Document", self.on_open),
                    ("Save", "Save", "Save", "Save Document", self.on_save),
                    ("SaveAs", "SaveAs", "Save as", "Save document as...", self.on_save_as),
                    "---",
                    ("Export", "Export", "Export", "Export document...", [
                        ("ExportImage", "ExportImage", "ExportImage", "Image", self.on_export_image),
                        ("ExportExcel", "ExportExcel", "ExportExcel", "Excel", self.on_export_excel),
                    ]),
                ],
                "Print" : [
                    ("Print", "Print", "Print", "Print Document", self.on_print),
                    ("PrintPreview", "PrintPreview", "Preview", "Print preview...", self.on_print),
                ],
                "Simulation" : [
                    ("Start", "Start", "Start", "Start the simulation", self.on_simulation_start),
                    ("Stop", "Stop", "Stop", "Stop the simulation", self.on_simulation_stop),
                ],
                "Options" : [
                    ("Settings", "Settings", "Settings", "Show simunet® settings", self.on_settings),
                ],
                "App" : [
                    ("Exit", "Exit", "Exit", "Close simunet®", self.on_exit),
                ]
            },
            "Edit": {
                "Clipboard": [
                    ("Cut", "Cut", "Cut", "Cut selected objects (Strg+X)", self.diagram.sheet.on_cut),
                    ("Copy", "Copy", "Copy", "Copy selected objects to clipboard (Strg+C)", self.diagram.sheet.on_copy),
                    ("Paste", "Paste", "Paste", "Paste objecs from clipboard (Strg+V)", self.diagram.sheet.on_paste),
                ],
                "Edit" : [
                    ("Undo", "Undo", "Undo", "Undo previous action (Strg+Z)", self.diagram.sheet.on_undo),
                    ("Redo", "Redo", "Redo", "Redo last action (Strg+Y)", self.diagram.sheet.on_redo),
                ]
            },
            "View": {
                "Panel" : [
                    ("PanelLeft", "PanelLeft", "Repository", "Toggle repository", self.on_toggle_repo),
                    ("PanelBottom", "PanelBottom", "Output", "Toggle output", self.on_toggle_output),
                    ("PanelRight", "PanelRight", "Properties", "Toggle property grid", self.on_toggle_propertygrid),
                ],
                "Bars" : [
                    ("Statusbar", "Statusbar", "Status", "Toggle statusbar", self.on_toggle_statusbar),
                    ("Flowsheetbar", "Flowsheetbar", "Flowsheet", "Toggle flowsheet toolbar", self.on_toggle_diagram_bar),
                    ("Resultsbar", "Resultsbar", "Results", "Toggle results toolbar", self.on_toggle_results_bar),
                ],
            },
            "Help": {
                "Help" : [
                    ("Help", "Help", "Help", "Help for simunet®", self.on_help),
                    ("GettingStarted", "GettingStarted", "Getting started", "Getting started with simunet®", self.on_getting_started),
                    ("Support", "Support", "Support", "Contact simunet® support team", self.on_support),
                    "---",
                    ("Info", "Info", "About...", "About simunet®", self.on_about),
                ]
            }
        }

        # Create the toolbar
        self.toolbar = RibbonBar(self, Images().ribbon)
        self.toolbar.add_items(ribbon_items)

        # Create theme drowpdown button
        view_ribbon = self.toolbar.ribbons["View"]
        style_group = view_ribbon.get_group("Style")
        view_ribbon.create_option_button(style_group, "Theme", "Theme", "Theme", "Select Theme", None)
        
        # Attach menu to the dropdown button
        btn = view_ribbon.tb_widgets["Theme"]
        sub_menu = ttk.Menu(btn, tearoff=1)
        btn.config(menu=sub_menu) 

        # Create theme drowpdown menu
        for key in self.style.theme_names():
            sub_menu.add_radiobutton(
                label=key, 
                image=Images().theme[key], 
                compound=tk.LEFT,
                value = key,
                variable = self.theme) 
            
        # Add trace event to theme variable
        self.theme.trace_add("write", self.on_theme_changed)

    def create_statusbar(self):
        """Create the bottom status bar with zoom and progress controls."""
        self.statusbar = ttk.Frame(self)

        # Add all items into the statusbar fame
        self.var_project = ttk.StringVar(value="Project: not named")
        self.lbl_project = ttk.Label(
            self.statusbar, 
            textvariable=self.var_project, 
            anchor=tk.W)
        self.lbl_project.grid(row=1, column=0, padx=5)

        # Create a vertical seperator
        sep = ttk.Separator(self.statusbar, orient=tk.VERTICAL)
        sep.grid(row=1, column=1, sticky=tk.NS)

        # Sheet information label
        self.var_sheet = ttk.StringVar(value="0 Shape(s), 0 Connector(s)")
        self.lbl_sheet = ttk.Label(
            self.statusbar, 
            textvariable=self.var_sheet, 
            anchor=tk.W)
        self.lbl_sheet.grid(row=1, column=2, padx=5)

        # Create a vertical seperator
        sep = ttk.Separator(self.statusbar, orient=tk.VERTICAL)
        sep.grid(row=1, column=3, sticky=tk.NS)

        # Sheet mouse coords label
        self.lbl_coords = ttk.Label(
            self.statusbar, 
            text="", 
            anchor=tk.W)
        self.lbl_coords.grid(row=1, column=4, padx=10, sticky=tk.EW)

        # Progressbar
        self.progress = ttk.Progressbar(
            self.statusbar, orient=tk.HORIZONTAL, 
            mode=tk.DETERMINATE, length=100)
        self.progress.grid(row=1, column=5, padx=10, sticky=tk.EW)
        self.progress.grid_remove()

        # Create a vertical seperator
        sep = ttk.Separator(self.statusbar, orient=tk.VERTICAL)
        sep.grid(row=1, column=6, sticky=tk.NS)

        # Zoom out button
        self.btn_zoom_out = ttk.Button(
            self.statusbar, 
            image=Images().system["Minus"], 
            bootstyle=tk.GHOST,
            takefocus=False, 
            command=self.diagram.sheet.zoom_out)
        self.btn_zoom_out.grid(row=1, column=7)

        # Zoom slider
        self.scale = ttk.Scale(
            self.statusbar, 
            bootstyle= tk.PRIMARY,
            value=self.diagram.sheet.zoom_factor, 
            from_=self.diagram.sheet.zoom_factor_min, 
            to=self.diagram.sheet.zoom_factor_max, 
            command=self.on_scale)
        self.scale.grid(row=1, column=8)

        # Zoom In button
        self.btn_zoom_in = ttk.Button(
            self.statusbar, 
            image=Images().system["Plus"], 
            bootstyle=tk.GHOST,
            takefocus=False, 
            command=self.diagram.sheet.zoom_in)
        self.btn_zoom_in.grid(row=1, column=9)
        
        # Zoom level label
        self.lbl_zoom = ttk.Label(
            self.statusbar, width=5, text="100%", 
            bootstyle=tk.DEFAULT, anchor=tk.W)
        self.lbl_zoom.grid(row=1, column=10, padx=5)

        # Add a sizer at the bottem right 
        self.sizegrip = ttk.Sizegrip(self.statusbar)
        self.sizegrip.grid(row=1, column=11, sticky=tk.SE)

        # Add horizontal separator at the top of the statusbar
        line = ttk.Separator(self.statusbar, orient=tk.HORIZONTAL)
        line.grid(row=0, column=0, columnspan=12, sticky=tk.EW)

        # Configure statusbar grid
        self.statusbar.rowconfigure(1, weight=1)
        self.statusbar.columnconfigure(4, weight=1)

    def create_window(self):
        """Assemble the main window layout, including panels and notebook."""
        pane_bootstyle = tk.PRIMARY

        # Create splitter pane
        self.pane = ttk.Panedwindow(self, orient=tk.HORIZONTAL, bootstyle=pane_bootstyle)
        self.pane.grid(row=1, column=0, sticky=tk.NSEW)

        # Create repository
        self.repo = Repository(self.pane)
        self.repo.load("./repository")
        self.pane.add(self.repo, weight=0)
       
        # Create middle splitter pane
        self.pane_middle = ttk.Panedwindow(
            self.pane, orient=tk.VERTICAL, 
            bootstyle=pane_bootstyle)
        self.pane.add(self.pane_middle, weight=1)

        # Create notebook
        self.notebook = ttk.Notebook(self.pane_middle, padding=(0,-2,0,0))
        self.pane_middle.add(self.notebook, weight=1)

        # Create Sheet
        self.diagram = Diagram(self.notebook)
        self.notebook.add(
            self.diagram, image=Images().system["Flowsheet"], 
            text="   Flowsheet   ", compound=tk.LEFT, padding=-1)
        
        # Create Resultsframe    
        self.results = Results(self.notebook)
        self.notebook.add(
            self.results, image=Images().system["Results"], 
            text="   Results   ", compound=tk.LEFT, padding=-1)

        # Create Outputbar
        self.output = Output(self.pane_middle)
        self.pane_middle.add(self.output, weight=0)

        # Create right splitter pane
        self.pane_right = ttk.Panedwindow(
            self, orient=tk.VERTICAL, 
            bootstyle=pane_bootstyle)
        self.pane.add(self.pane_right, weight=0)

        # Create property Grid
        self.propertygrid = PropertyGrid(self.pane_right)
        self.pane_right.add(self.propertygrid, weight=1)
 
        # Create property description
        self.prop_descriptor = PropertyDescriptor(self.pane_right)
        self.propertygrid.prop_descriptor = self.prop_descriptor
        self.pane_right.add(self.prop_descriptor, weight=0)
     
        # Toolbar
        self.create_toolbar()
        self.toolbar.grid(row=0, column=0, sticky=tk.NSEW)
    
        # Statusbar
        self.create_statusbar()
        self.statusbar.grid(row=2, column=0, sticky=tk.NSEW)
        self.statusbar_visible = True

        # Configure grid rows and columns
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Bind events
        # Repository
        self.repo.bind("<<SelectionChanged>>", self.on_repo_selection_changed) 
        # Ruler
        self.diagram.vr.bind('<ButtonPress-1>', self.on_ruler_click)
        self.diagram.hr.bind('<ButtonPress-1>', self.on_ruler_click)      
        # Sheet
        self.diagram.sheet.bind("<Motion>", self.on_diagram_motion, add=True)
        self.diagram.sheet.bind("<Leave>", self.on_diagram_leave, add=True)
        self.diagram.sheet.bind("<<ZoomChanged>>", self.on_zoom_changed, add=True)
        self.diagram.sheet.bind("<<FocusChanged>>", self.on_focus_changed, add=True)
        self.diagram.sheet.bind("<<ShapeAdded>>", self.on_project_modified, add=True)
        self.diagram.sheet.bind("<<ShapeDeleted>>", self.on_project_modified, add=True)
        self.diagram.sheet.bind("<<ShapeMoved>>", self.on_project_modified, add=True)
        self.diagram.sheet.bind("<<ConnectorAdded>>", self.on_project_modified, add=True)
        self.diagram.sheet.bind("<<ConnectorDeleted>>", self.on_project_modified, add=True) 
        self.diagram.sheet.bind("<<SelectionChanged>>", self.on_selection_changed, add=True)
        # Chart
        self.results.bind("<<ConfigAdded>>", self.on_project_modified, add=True)
        self.results.bind("<<ConfigDeleted>>", self.on_project_modified, add=True)
        self.results.bind("<<ConfigChanged>>", self.on_project_modified, add=True)
        self.results.bind("<<ConfigSelected>>", self.on_config_selected, add=True)
        # Notebook
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed, add=True)
        # Propertygrid
        self.propertygrid.bind("<<ValueChanged>>", self.on_value_changed)

        # Start clipboard listener
        self.poll_clipboard()
        
        # Update ui elements
        self.update_ui()

    def update_progress(self, value):
        """Update the progress bar value and refresh the UI."""
        self.progress["value"] = value
        self.update_idletasks()

    def run_simulation(self):
        """Start the simulation process and poll progress until completion."""
        if self.wfr_process is None:
            self.progress.configure(mode=tk.INDETERMINATE)
            self.progress.start()
            self.progress.grid()
            #self.update_idletasks()
            
            # Update project
            self.output.console.append("Updating project...\n")
            self.diagram.sheet.update_project() 
            
            # Get multiprocessing manager to create data dict
            self.output.console.append("Creating process manager...\n")
            manager = multiprocessing.Manager()
            self.result_dict = manager.dict()
            self.result_dict["result"] = {}
            self.result_dict["statistics"] = {}
            self.result_dict["convergence"] = []
            
            # Launch the waveform
            self.output.console.append("Start launcher...\n")
            self.wfr_process = WaveformLauncher(
                copy.deepcopy(self.project), 
                self.app_config.aws_endpoint,
                self.app_config.mqtt_endpoint,
                self.result_dict,
                self.output.console.stdout_queue)
            self.wfr_process.start()

            # Update ribbon an poll simulation progress
            self.toolbar.ribbons["Start"].set_enabled("Stop", True)
            self.poll_simulation()

    def poll_simulation(self):
        """Poll the simulation process and finalize results when complete."""
        if self.wfr_process and self.wfr_process.is_alive():
            # If process is alive poll again
            self.after(50, self.poll_simulation)
        else:
            try:
                # Clean up if process has terminated 
                self.wfr_process = None
                self.output.console.append_divider()

                # Copy the results
                self.project.result = copy.deepcopy(self.result_dict["result"])
                self.project.statistics = copy.deepcopy(self.result_dict["statistics"])
                self.project.convergence = copy.deepcopy(self.result_dict["convergence"])

                # Reattach the project to update the charts
                self.results.set_project(self.project)
                self.output.set_project(self.project)
            finally:
                # Stop prgress bar
                self.progress.stop()
                # Remove progressbar
                self.progress.grid_remove()
                # Finally update ui
                self.update_ui()

    def stop_simulation(self):
        """Terminate the currently running simulation process."""
        if self.wfr_process:
            self.wfr_process.kill()
            self.wfr_process.join()
            self.output.console.append("Simulation process terminated.\n")

    def can_close(self):
        """Return True if closing is allowed, prompting for save or cancellation."""
        if self.wfr_process:
            res = messagebox.askyesnocancel(
                message="Do you want to cancel the current simulation?", 
                title="Cancel simulation", parent=self)
            if res == True:
                # Stop the simulation
                self.stop_simulation()
            else: 
                # Return false
                return False

        if self.is_dirty:
            # Ask for saving changes
            res = messagebox.askyesnocancel(
                message="Do you want to save your changes?", 
                title="Save changes", parent=self)
            if res == True:
                # Call on save
                self.on_save()
            elif res == False: 
                # We can close, so return True
                return True

        # Return True if project is clean otherwise false
        return not self.is_dirty

    def on_simulation_start(self):
        """Begin a new simulation run if none is active."""
        if self.wfr_process is None:
            self.output.notebook.select(self.output.notebook.tabs()[1])
            self.output.console.append("Simulation process warming up...\n")
            self.output.console.append("Using simunet® core version {}...\n".format(COREVERSION))
            self.toolbar.ribbons["Start"].set_enabled("Start", False)
            self.sim_id = self.after_idle(self.run_simulation)

    def on_simulation_stop(self):
        # Unschedle run_simulation call if it is scheduled 
        if self.sim_id:
            self.after_cancel(self.sim_id)
            self.sim_id = None

        # Stop the simulation
        if self.wfr_process:
            self.stop_simulation()
    
    def poll_clipboard(self):
        """Poll the clipboard and update paste availability."""
        ribbon = self.toolbar.ribbons["Edit"]
        enabled = self.diagram.sheet.can_paste()
        ribbon.set_enabled("Paste", enabled)
        self.after(250, self.poll_clipboard)

    def on_tab_changed(self, event):
        """Handle notebook tab changes and update the property grid."""
        tab_index = self.notebook.index("current")
        if tab_index == 0:
            self.on_focus_changed(event)
        elif tab_index == 1:
            self.propertygrid.set_selected_object(self.results)

    def on_focus_changed(self, event):
        """Update the property grid when sheet focus changes."""
        if self.suspend_update:
            return
        
        item = self.diagram.sheet.focused
        
        if item in self.diagram.sheet.shapes:
            item = self.diagram.sheet.shapes[item]
        elif item in self.diagram.sheet.connectors:
            item = self.diagram.sheet.connectors[item]

        self.propertygrid.set_selected_object(item)
        self.update_ui()

    def on_config_selected(self, event):
        if self.notebook.index("current") == 1:
            self.propertygrid.set_selected_object(self.results)

    def on_project_modified(self, event):
        """Mark the project as modified and refresh sheet statistics."""
        self.is_dirty = True

        # Update the sheet statistics
        self.var_sheet.set("{} Model(s), {} Connector(s)".format(
            len(self.diagram.sheet.shapes),
            len(self.diagram.sheet.connectors)))
        self.update_ui()

    def on_delete_results(self):
        # Clear the results
        self.project.result.clear()
        self.project.statistics.clear()
        self.project.convergence.clear()

        # Reattach the project (redraw charts)
        self.results.set_project(self.project)
        self.output.set_project(self.project)
        
        # Set dirty Flag
        self.is_dirty = True

        # Update the ui
        self.update_ui()

    def on_value_changed(self, event):
        """Handle property grid value changes by marking the project dirty."""
        self.is_dirty = True
        self.update_ui()

    def on_ruler_click(self, event):
        self.diagram.sheet.set_focus(self.diagram.sheet)

    def on_theme_changed(self, *args):
        """Apply a new theme when the theme selection changes."""
        self.app_config.style["themename"] = self.theme.get()
        self.style.theme_use(self.theme.get())

    def on_repo_selection_changed(self, *args):
        """Update the diagram sheet when a repository item is selected."""
        self.diagram.sheet.set_repo_item(self.repo.selected)

    def on_zoom_changed(self, event):
        """Refresh the UI when the sheet zoom level changes."""
        self.update_ui()

    def on_scale(self, scale):
        """Apply zoom factor changes from the zoom slider."""
        self.diagram.sheet.set_zoom_factor(float(scale))

    def on_diagram_leave(self, event):
        """Clear coordinate display when the mouse leaves the diagram."""
        self.lbl_coords.config(text="")

    def on_diagram_motion(self, event):
        """Display current diagram coordinates in the status bar."""
        self.lbl_coords.config(
            text="x: {}, y: {}".format(
                int(self.diagram.sheet.x),
                int(self.diagram.sheet.y),
            )
        )
    
    def on_chart_changed(self, event):
        """Refresh UI state when chart configuration changes."""
        self.update_ui()
    
    def on_selection_changed(self, event):
        """Refresh UI state when selection changes in the diagram or results."""
        self.update_ui()

    def on_close(self):
        """Handle application close while saving config and cleaning temporary files."""
        if self.can_close():
            try:
                #self.save_pane_states({
                #    "pane": self.pane, 
                #    "pane_middle": self.pane_middle, 
                #    "pane_right": self.pane_right})
                self.app_config.dump(os.path.join(self.userdir, "config.json"), indent=True)

                tmp_folder = './tmp/'
                for filename in os.listdir(tmp_folder):
                    file_path = os.path.join(tmp_folder, filename)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
            finally:
                self.withdraw()
                self.destroy()

    def on_export_image(self):
        """Export the current view to an image file."""
        index = self.notebook.index("current")
        if index == 0:
            filetypes = [("Image", "*.svg"), ("All files", "*")]
            dialog = filedialog.SaveAs(self, filetypes=filetypes, initialfile="flowsheet.svg")
            path = dialog.show()
            if path != "":
                self.diagram.sheet.export_img(path)
                os.startfile(path)
        elif index == 1:
            self.results.on_save()

    def on_export_excel(self):
        """Export simulation results to an Excel workbook."""
        filetypes = [("Excel", "*.xlsx"), ("All files", "*")]
        dialog = filedialog.SaveAs(self, filetypes=filetypes, initialfile="results.xlsx")
        path = dialog.show()
        if path != "":
            if not str.endswith(path, ".xlsx"):
                path += ".xlsx"
            export_excel(self.project.result, path)
            os.startfile(path)
    
    def on_new(self):
        """Create a new project document if the current project can be closed."""
        if self.can_close():
            # Suspend updates
            self.suspend_update = True

            # Project
            self.project = Project()
            self.project_path = None

            self.diagram.sheet.set_project(self.project)
            self.output.set_project(self.project)
            self.results.set_project(self.project)

            self.is_dirty = False
            self.suspend_update = False

            # Focus the project 
            self.diagram.sheet.set_focus(self.project)
            logger.info("Created new document.")

    def on_open(self):
        """Open an existing project file after prompting to save changes."""
        if self.can_close():
            filetypes = [("Simunet files", "*.sim"), ("All files", "*")]
            dialog = filedialog.Open(self, filetypes=filetypes)
            path = dialog.show()
            if path:
                # Suspend updates
                self.suspend_update = True
                self.progress.configure(mode=tk.DETERMINATE)
                self.progress.grid()
                self.update_progress(10)
                
                self.project = Project()
                self.project.load(path)
                self.project_path = path
                if "auto_config" not in self.project.simulation:
                    self.project.simulation["auto_config"] = False

                self.update_progress(20)

                self.diagram.sheet.set_project(self.project)
                self.update_progress(30)

                self.notebook.select(self.notebook.tabs()[0])
                self.update_progress(40)

                self.output.set_project(self.project)
                self.update_progress(60)

                self.results.set_project(self.project)
                self.update_progress(80)

                self.update_progress(100)
                self.progress.grid_remove()

                self.is_dirty = False
                self.suspend_update = False

                # Focus the project 
                self.diagram.sheet.set_focus(self.project)
                logger.info("Loaded {}.".format(path))

    def on_save(self):
        """Save the current project to disk, prompting for location if needed."""
        path = self.project_path
        if path is None:
            self.on_save_as()
        else:
            # Update the project data
            self.diagram.sheet.update_project()
            self.results.update_project()

            # Dump the project data
            self.project.dump(path, indent=4)
            self.project_path = path
            self.is_dirty = False

            self.update_ui()
            logger.info("Saved {}.".format(path))

    def on_save_as(self):
        """Prompt the user for a file path and save the project."""
        filetypes = [("Simunet files", "*.sim"), ("All files", "*")]
        defaultextension = "sim"

        dialog = filedialog.SaveAs(
            self, filetypes=filetypes, 
            defaultextension=defaultextension)
        
        path = dialog.show()
        if path:
            self.project_path = path
            self.on_save()

    def on_print(self):
        """Print the current flowsheet or results view to an SVG file."""
        index = self.notebook.index("current")
        if index == 0:
            path = os.path.dirname(os.path.abspath(__file__)) + "/tmp/print.svg"
            self.diagram.sheet.export_img(path)
            os.startfile(path)
        elif index == 1:
            path = os.path.dirname(os.path.abspath(__file__)) + "/tmp/print.svg"
            self.results.figure.savefig(path)
            os.startfile(path)
    
    def on_print_preview(self):
        """Show a print preview by exporting the current view."""
        self.on_print()
    
    def on_settings(self):
        """Open the application settings dialog."""
        dlg = AppConfigDlg(self.notebook, app_config=self.app_config)
        dlg.show()
        if dlg.result == "OK":
            rcParams["font.sans-serif"] = self.app_config.rc_params["font.sans-serif"]
            rcParams["font.size"] =  self.app_config.rc_params["font.size"]

            self.on_theme_changed(None)

    def on_exit(self):
        """Exit the application cleanly."""
        self.on_close()
  
    def on_toggle_statusbar(self):
        """Toggle visibility of the status bar."""
        if self.statusbar_visible:
            self.statusbar.grid_remove()
            self.statusbar_visible = False
        else:
            self.statusbar.grid()
            self.statusbar_visible = True
        self.update_ui()

    def on_toggle_diagram_bar(self):
        """Toggle the diagram toolbar visibility."""
        self.diagram.on_toggle_toolbar()
        self.update_ui()

    def on_toggle_results_bar(self):
        """Toggle the results toolbar visibility."""
        self.results.on_toggle_toolbar()
        self.update_ui()

    def on_toggle_repo(self):
        """Toggle the repository panel visibility."""
        if self.repo_visible():
            self.pane.remove(self.repo)
        else:
            self.pane.insert(0, self.repo, weight=1)
        self.update_ui()

    def on_toggle_output(self):
        """Toggle the output panel visibility."""
        if self.output_visible():
            self.pane_middle.remove(self.output)
        else:
            self.pane_middle.add(self.output, weight=1)
        self.update_ui()

    def on_toggle_propertygrid(self):
        """Toggle the property grid panel visibility."""
        if self.propertygrid_visible():
            self.pane.remove(self.pane_right)
        else:
            self.pane.add(self.pane_right, weight=1)
        self.update_ui()

    def on_about(self):
        about_dlg = AboutDlg(self.notebook)
        about_dlg.show()
    
    def on_help(self):
        url = URLS["help"]
        os.startfile(url)
    
    def on_support(self):
        url = URLS["support"]
        os.startfile(url)
    
    def on_getting_started(self):
        url = URLS["getting_started"]
        os.startfile(url)

    def repo_visible(self):
        """Return True if the repository panel is currently visible."""
        return self.repo._w in self.pane.panes()

    def output_visible(self):
        """Return True if the output panel is currently visible."""
        return self.output._w in self.pane_middle.panes()

    def propertygrid_visible(self):
        """Return True if the property grid panel is currently visible."""
        return self.pane_right._w in self.pane.panes()

    def update_ui(self):
        """Refresh the application UI state based on current project and view state."""
        if self.suspend_update:
            return

        # Update project name
        self.var_project.set(self.project.meta["name"])

        # Update caption
        if self.project_path:
            caption = "simunet® - {}".format(os.path.basename(self.project_path))
        else:
            caption = "simunet® - New document"

        if self.is_dirty:
            caption = caption + " *"
        self.title(caption)

        ribbon = self.toolbar.ribbons["Start"]
        ribbon.set_enabled("Start", not self.wfr_process)
        ribbon.set_enabled("Stop", self.wfr_process)

        ribbon = self.toolbar.ribbons["Edit"]
        ribbon.set_enabled("Cut", len(self.diagram.sheet.selected_shapes)>0)
        ribbon.set_enabled("Copy", len(self.diagram.sheet.selected_shapes)>0)
        ribbon.set_enabled("Undo", len(self.diagram.sheet.undo_stack)>0)
        ribbon.set_enabled("Redo", len(self.diagram.sheet.redo_stack)>0)
        
        ribbon = self.toolbar.ribbons["View"]
        ribbon.set_checked("PanelLeft", self.repo_visible())
        ribbon.set_checked("PanelRight", self.propertygrid_visible())
        ribbon.set_checked("PanelBottom", self.output_visible())
        ribbon.set_checked("Statusbar", self.statusbar_visible)
        ribbon.set_checked("Flowsheetbar", self.diagram.toolbar_visible)
        ribbon.set_checked("Resultsbar", self.results.toolbar_visible)

        zoom_text = str(int(self.diagram.sheet.zoom_factor*100))+"%"
        self.lbl_zoom.config(text=zoom_text)
        self.scale.config(value=self.diagram.sheet.zoom_factor)

if __name__ == '__main__':
    # Prepare logging
    logger.prepare_logging("logs/log.conf")
    logger.instance = logging.getLogger(__name__)

    # Create and run app
    app = SimunetApp(high_dpi=False)
    app.mainloop()

