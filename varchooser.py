"""Dialog for choosing one or more process variables from modeled objects."""

import ttkbootstrap as ttk
import ttkbootstrap.constants as tk
from ttkbootstrap.dialogs import Dialog
from ttkbootstrap import utils
from ttkbootstrap.style import Style
from images import Images
from tooltip import Tooltip


class VarChooserDialog(Dialog):
    """Dialog for selecting variables from a model option tree."""

    def __init__(self, parent=None, options=None, initialvars=None, title="Choose Variable", selectmode=tk.EXTENDED):
        """Initialize the variable chooser dialog.

        Args:
            parent: Parent widget for the dialog.
            options: Dictionary of available models and variables.
            initialvars: Initial variable selection list.
            title: Dialog title.
            selectmode: Selection mode for the variable list.
        """
        super().__init__(parent=parent, title=title)

        self.vars = initialvars
        self._options = options
        self._selectmode = selectmode
        
    def create_body(self, master):
        """Create the main body of the dialog with filter controls and variable list."""
 
        # Create toolbar
        self.toolbar = ttk.Frame(master)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # Add horizontal separator at the bottom of the toolbar
        line = ttk.Separator(self.toolbar, orient= tk.HORIZONTAL)
        line.pack(side=tk.BOTTOM, fill=tk.X)

        # Add search label into the toolbar
        self.lbl_filter = ttk.Label(self.toolbar, text="Filter:", padding=(5,0))
        self.lbl_filter.pack(side=tk.LEFT)

        # Add search entry into the toolbar
        self.entry_filter = ttk.Entry(self.toolbar)
        self.entry_filter.bind("<Return>", lambda e: self.on_filter())
        self.entry_filter.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=0, pady=3)
        
        # Add search button into the toolbar
        self.btn_filter = ttk.Button(
                    self.toolbar, 
                    bootstyle=tk.GHOST, 
                    image=Images().system["Filter"], 
                    takefocus=False,
                    command=self.on_filter)
        self.btn_filter.pack(side=tk.LEFT)

        # Add a tooltip for the search button
        Tooltip(self.btn_filter, text="Filter list")
        
        # Add search button into the toolbar
        self.btn_clear_filter = ttk.Button(
                    self.toolbar, 
                    bootstyle=tk.GHOST, 
                    image=Images().system["FilterClear"], 
                    takefocus=False,
                    command=self.on_clear_filter)
        self.btn_clear_filter.pack(side=tk.LEFT)

        container = ttk.Frame(master, padding=(10,0))
        container.pack(fill=tk.BOTH, expand=tk.YES, anchor=tk.N)

        # Add a tooltip for the search button
        Tooltip(self.btn_clear_filter, text="Clear filter")

        self.order = []
        self.detached_items =[]   

        self.create_var_selector(container)

        self._toplevel.wm_attributes("-toolwindow", "true")
        self._toplevel.wm_resizable(width=True, height=True)
  
    def on_clear_filter(self):
        """Clear the filter text and restore the full variable list."""
        self.entry_filter.delete(0, tk.END)
        self.on_filter()

    def on_filter(self):
        # Detach all visible items
        for iid in self.listbox.get_children():
            self.listbox.detach(iid)

        # Reattach all items in the correct order
        for iid in self.order:
            self.listbox.reattach(iid, "", 0)
        
        # Clear the detached list
        self.detached_items.clear()
        
        # Get the filter string
        search_str = str(self.entry_filter.get())
        # Filter the tree view
        for iid in self.listbox.get_children():
            values = self.listbox.item(iid)["values"]
            filtered = [val for val in values if search_str in val]
            if len(filtered) == 0:
                self.listbox.detach(iid)
                self.detached_items.append(iid)
                
    def create_var_selector(self, master):
        """Create the treeview control for selecting available variables."""
        container = ttk.Frame(master)
        container.pack(fill=tk.BOTH, expand=tk.YES, side=tk.LEFT)

        # Cerate header
        header = ttk.Label(
            container,
            text="Available models and variables",
            font="TkHeadingFont",
        )
        header.grid(row=0, column=0, sticky=tk.EW)

        # Create treeview
        self.listbox = ttk.Treeview(
            container, bootstyle="primary-table", 
            columns=[0,1,2,3], show="headings",
            selectmode=self._selectmode)
        self.listbox.grid(row=1, column=0, sticky=tk.NSEW)
        
        # Configure columns
        self.listbox.column(0, anchor=tk.W, width=utils.scale_size(master, 150), stretch=tk.NO)
        self.listbox.column(1, anchor=tk.W, width=utils.scale_size(master, 100), stretch=tk.NO)
        self.listbox.column(2, anchor=tk.W, width=utils.scale_size(master, 250), stretch=tk.YES)
        self.listbox.column(3, anchor=tk.W, width=utils.scale_size(master, 100), stretch=tk.NO)

        # Configure heading
        self.listbox.heading(0, text='Model', anchor=tk.W)
        self.listbox.heading(1, text='Variable', anchor=tk.W)
        self.listbox.heading(2, text='Description', anchor=tk.W)
        self.listbox.heading(3, text='Unit', anchor=tk.W)
       
        #Fill the treeview
        self.fill_tree()

        # Bind select event
        self.listbox.bind("<<TreeviewSelect>>", self.on_select_var)

        # Create and attach scrollbar to treeview
        self.sb_y = ttk.Scrollbar(
            master=container,
            orient=tk.VERTICAL,
            command=self.listbox.yview
        )
        self.sb_y.grid(row=1, column=1, sticky=tk.NS)
        self.listbox.configure(yscrollcommand=self.sb_y.set)
        
        # Configure grid rows and columns
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)
    
    def fill_tree(self):
        """Populate the treeview with available model variables."""
        for iid in self.listbox.get_children():
            self.listbox.delete(iid)

        # Configure stripe color
        row = 0
        stripe_color = Style().colors.active

        # Add data to treeview
        for model_id in self._options:
            model=self._options[model_id]
            name = model["name"]
            vars = model["vars"]
            for var_id in vars:
                description = vars[var_id].get("description", "")
                unit = vars[var_id].get("unit", "")
                iid = iid=f"{model_id}.{var_id}"
                self.listbox.insert(
                    "", iid=iid, index=tk.END, tags=(model_id, var_id), 
                    values=[name, var_id, description, f"[{unit}]"])
                self.order.insert(0, iid)
            row += 1
            if row % 2:
                self.listbox.tag_configure(model_id, background=stripe_color)
        
        # Set selection
        selected_items = []
        for item in self.vars:
            if item[0] not in self._options:
                continue
            selected_items.append("{}.{}".format(item[0], item[1]))

        if len(selected_items):
            self.listbox.selection_set(selected_items)
            self.listbox.see(selected_items[0])

    def on_select_var(self, e):
        """Update the selected variable list when the treeview selection changes."""
        self.vars = list([self.listbox.item(item)["tags"] for item in self.listbox.selection()])

    def create_buttonbox(self, master):
        """Create the OK and Cancel buttons for the dialog."""
        # Add a sizegrip at the bottom-right
        sizegrip = ttk.Sizegrip(master)
        sizegrip.pack(side=tk.RIGHT, anchor=tk.SE)

        container = ttk.Frame(master, padding=(0, 10))
        container.pack(fill=tk.X)

        # OK button
        btn_ok = ttk.Button(
            master=container,
            bootstyle=tk.PRIMARY,
            takefocus=False,  
            width=6,
            text="OK"
        )
        btn_ok.bind("<Return>", lambda _: btn_ok.invoke())
        btn_ok.configure(command=lambda b=btn_ok: self.on_button_press(b))
        btn_ok.pack(padx=5, side=tk.RIGHT)

        # Cancel button
        btn_cancel = ttk.Button(
            container,
            bootstyle=tk.SECONDARY, 
            takefocus=False,  
            width=6, 
            text="Cancel")
        btn_cancel.bind("<Return>", lambda _: btn_cancel.invoke())
        btn_cancel.configure(command=lambda b=btn_cancel: self.on_button_press(b))
        btn_cancel.pack(padx=5, side=tk.RIGHT)
 
    def on_button_press(self, button):
        """Handle button presses and save edited table values on OK.

        Args:
            button: The button widget that was pressed.
        """
        self._result = button.cget('text')

        # Close window
        self.close()
        
if __name__ == "__main__":
    
    options = {
        "M1": {
            "name": "Const. Source",
            "vars": {
                "c_A_f": {
                    "description": "Feed concentration",
                    "unit": "mol/m^3",
                },
                "q_r_f": {
                    "description": "Reactor feed flow rate",
                    "unit": "m^3/s",
                }
            }
        },
        "M2": {
            "name": "3L-Controller",
            "vars": {
                "p_v": {
                    "description": "Process value",
                    "unit": "mA"
                },
                "m_v": {
                    "description": "Manipulated value",
                    "unit": "mA",
                },
                "s_p": {
                    "description": "Set Point",
                    "unit": "mA",
                }
            }
        }
    }

    dlg = VarChooserDialog(
        None, 
        options=options, 
        initialvars=[["M1", "q_r_f"]],
        selectmode=tk.BROWSE)
    dlg.show()

    print(dlg.result)
    print(dlg.vars)
