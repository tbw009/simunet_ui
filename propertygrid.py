"""Property grid widget for editing object properties.

This module implements a collapsible property grid used by the simulation
UI to display and edit object properties, including inline editors,
popup selectors, and live filtering.
"""

from tkinter.font import Font
from tooltip import Tooltip
from collapsingframe import CollapsingFrame
from images import Images
import ttkbootstrap as ttk
import ttkbootstrap.constants as tk
from ttkbootstrap import utils
from propertyeditors import *
import datetime
from ttkbootstrap import utils


class PropertyGrid(ttk.Frame):
    """Grid control for displaying and editing object properties."""

    def __init__(self, master, **kwargs):
        """Initialize the property grid widget and its toolbar controls."""
        super().__init__(master, **kwargs)
 
        # Create toolbar
        self.toolbar = ttk.Frame(self)
        self.toolbar.grid(row=0, column=0, sticky=tk.EW)

        # Add horizontal separator at the bottom of the toolbar
        line = ttk.Separator(self.toolbar, orient= tk.HORIZONTAL)
        line.pack(side=tk.BOTTOM, fill=tk.X)

        # Add search label into the toolbar
        self.lbl_filter = ttk.Label(self.toolbar, text="Filter:", padding=(5,0))
        self.lbl_filter.pack(side=tk.LEFT)

        # Add search entry into the toolbar
        self.entry_filter = ttk.Entry(self.toolbar)
        self.entry_filter.bind("<Return>", lambda e: self.on_filter())
        self.entry_filter.bind("<Escape>", lambda e: self.on_clear_filter())
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
        Tooltip(self.btn_filter, text="Filter")

        # Add object label
        self.object_name = ttk.Label(self, padding=(5,0), bootstyle=tk.PRIMARY)
        self.object_name.grid(row=1, column=0, sticky=tk.EW)

        # Add horizontal separator under the object label
        line = ttk.Separator(self, orient= tk.HORIZONTAL)
        line.grid(row=2, column=0, sticky=tk.EW)

        # Create property grid
        self.categories = {}
        self.category_rows = {}
        self.anchor = tk.W

        self.cf = CollapsingFrame(self, padding=0)
        self.cf.grid(row=3, column=0, sticky=tk.NSEW)

        # Configure grid rows and columns
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        
        # Properties
        self.props={}
        self.prop_descriptor = None
        self.value_editor = None
        self.value_label = None
        self._selected_object = None
    
    def add_category(self, category):
        """Add a new property category section to the grid."""
        # Create a category frame
        container = ttk.Frame(self.cf)
        container.columnconfigure(0, weight=1)

        # Add frame to collapsable frame
        self.categories[category] = container
        self.category_rows[category] = 0
        self.cf.add(container, title=category)

        # Add a separator to the frame
        sep = ttk.Separator(container, orient=tk.HORIZONTAL)
        sep.grid(row=0, column=0, sticky=tk.EW)
 
    def remove_category(self, category):
        """Remove a property category and its associated properties."""
        # Remove frame
        prop_to_remove= [k for k in self.props if self.props[k]["category"] == category]
        for prop_value in prop_to_remove:
            self.props.pop(prop_value)

        container = self.categories[category]
        self.cf.remove(container)
        self.categories.pop(category)

    def update_value_label(self, prop_value):
        """Update the displayed label text and preview style for a property."""
        # Get property and value
        prop = self.props[prop_value]
        value = prop["value"]

        # By default the value is just the string conversion
        label = str(value)
        
        if prop["editor"] == "color" or prop["editor"] == "color_str":
            # Update bg and fg of the value label
            prop_value.config(
                background=value, 
                foreground=utils.contrast_color(value, model=utils.HEX))
        elif prop["editor"] == "color_map":
            # Update image of the value label
            prop_value.config(
                image=Images().colormap[value], 
                compound=tk.CENTER)
            label =  " "
        elif prop["editor"] == "font":
            # Set label to fontname and font size
            label = "{} {}".format(
                value.actual()["family"], value.actual()["size"])
        elif prop["editor"] == "date" or prop["editor"] == "date_str":
            # Update label with the given time format option
            label = value.strftime(prop["options"])
        elif prop["editor"] == "single_var" or prop["editor"] == "multi_var":
            # Set label to the list of model names and vars
            if type(value) is list:
                entries = []
                for item in value:
                    if item[0] not in prop["options"]:
                        continue
                    entries.append("{}.{}".format(
                        prop["options"][item[0]]["name"], 
                        item[1]))
                label = ", ".join(entries)
            else:
                label=""
        elif prop["editor"] == "password":
            # IfSet label to dotted string
            label = "••••••••••"
        elif prop["editor"] == "code":
            #Set label to the number of codelines
            label = "{} line(s) of code".format(value.count("\n")+1)
        elif prop["editor"] == "table":
            #Set label to the number of codelines
            label = "{} datarow(s)".format(len(value[1]))
        elif prop["editor"] == "quantity":
            #Set label to the number of codelines
            label = "{} {}".format(value[0], value[1])

        # Update the value label
        prop_value.config(text=label)

    def on_drag_motion(self, event):
        """Resize the property field columns while dragging the separator."""
        widget = event.widget
        x = widget.winfo_x() + event.x
        prop_container = widget._container
        width = prop_container.winfo_width()

        for prop in self.props.values():
            prop_container = prop["frame"]
            prop_container.columnconfigure(0, weight=width, minsize=max(min(width-15, x), 15))
            prop_container.columnconfigure(1, weight=0)
            prop_container.columnconfigure(2, weight=1)

    def add_property(
            self, category, property, value, editor, 
            displayname="", description="", state=tk.NORMAL, 
            options=None, bootstyle=tk.DEFAULT):
        """Add a property entry to a category with an optional editor."""

        # Fix displayname if not given
        if displayname == "":
            displayname = property

        # Create a category if neccessary
        if category not in self.categories.keys():
            self.add_category(category)

        # Get the category frame
        cat_container = self.categories[category]
        row_index = self.category_rows[category] + 1

        # Create a new property frame and pack it into the category frame
        prop_container = ttk.Frame(cat_container)
        prop_container.grid(
            row=row_index, column=0, sticky=tk.NSEW, 
            padx=0)
        self.category_rows[category] = row_index

        # Create the property label and set it to pos 0,0 in the property frame grid
        prop_label = ttk.Label(
            prop_container, padding=(5,5), text=displayname, 
            width=80, 
            bootstyle="@chrome", 
            anchor=self.anchor)
        
        prop_label.grid(row=0, column=0, sticky=tk.NSEW)
        prop_label.bind("<Button-1>", self.on_prop_label_click)

        # Create a horizontal separator 
        sep = ttk.Separator(prop_container, orient=tk.HORIZONTAL)
        sep.grid(row=1, column=0, sticky=tk.EW)
 
        # Create a vertical seperator and set it to pos 0,1 in the property frame grid
        sep = ttk.Frame(prop_container, bootstyle=tk.PRIMARY, width=2, height=20, cursor="sb_h_double_arrow")
        sep._container = prop_container
        sep.grid(row=0, column=1, rowspan=2, sticky=tk.NS)

        # Make slider draggable
        sep.bind("<B1-Motion>", self.on_drag_motion)

        # Create the value label
        prop_value = ttk.Label(
            prop_container, padding=(5,5), text=str(value), 
            width=80, bootstyle=bootstyle)

        # Set gridpos to 0,2 in the property frame grid
        prop_value.grid(row=0, column=2, sticky=tk.NSEW)

        # Create a horizontal separator 
        sep = ttk.Separator(prop_container, orient=tk.HORIZONTAL)
        sep.grid(row=1, column=2, sticky=tk.EW)

        # Tie prop label and prop value together    
        prop_label.prop_value = prop_value

        # Bind the mouse click event to begin edit if state is Normal
        if state == tk.NORMAL:
            prop_value.bind("<Button-1>", self.on_begin_edit)
        else:
            prop_value.config(bootstyle=tk.SECONDARY)           
            prop_value.bind("<Button-1>", self.on_end_edit)
        
        # Store props in the property dictionary
        self.props[prop_value] = {
            "category": category, 
            "property": property, 
            "value": value, 
            "editor": editor,
            "displayname": displayname,
            "description": description, 
            "state": state,
            "options": options,
            "frame": prop_container
        }

        # Update label text
        self.update_value_label(prop_value)

        # Update row and column weights for grid manager
        prop_container.rowconfigure(0, weight=1)
        prop_container.rowconfigure(1, weight=0)
        prop_container.columnconfigure(0, weight=1)
        prop_container.columnconfigure(1, weight=0)
        prop_container.columnconfigure(2, weight=1)
    
    def update_prop_descriptor(self, value_label):
        """Update the descriptor panel with the current property information."""
        if self.prop_descriptor:
            if value_label:
                # get the corresponding prop entry
                prop = self.props[value_label]

                # Configure the prop descriptor if available
                if self.prop_descriptor:
                    hint = prop["description"]
                    options = prop["options"]
                    if options:
                        if "min" in options:
                            hint += "\nmin={}\n".format(options["min"])
                        if "max" in options:
                            hint += "max={}".format(options["max"])
                    self.prop_descriptor.set(prop["displayname"], hint)
            else:
                self.prop_descriptor.set("", "")      

    def on_prop_label_click(self, event):
        """Handle clicks on a property label by ending the current edit."""
        # End edit if a prop label is clicked
        self.on_end_edit(event)

    def on_begin_edit(self, event):
        """Begin editing the clicked property value with the appropriate editor."""
        # End a previous editor
        try:
            self.on_end_edit(None)
        except:
            return

        # Get the value_label
        self.value_label = event.widget

        # Update the propery descriptor
        self.update_prop_descriptor(self.value_label)

        # Generate the BeginEdit event. 
        # This event could be used to create a custom editor
        self.event_generate("<<BeginEdit>>") 

        # Create an editor if not created yet
        if not self.value_editor and self.value_label:
            prop = self.props[self.value_label]
            self.value_editor = create_value_editor(
                prop["editor"], self.value_label.master, 
                prop["value"], prop["options"])
       
        # Show editor with the grid config of the associated value label
        self.value_editor.grid(self.value_label.grid_info())     
        
        # Bind the callbacks to corresponding events
        if isinstance(self.value_editor, ttk.Combobox):
            self.value_editor.bind("<<ComboboxSelected>>", self.on_focus_out, add=True)
        elif not isinstance(self.value_editor, DatePopupEntry):
            self.value_editor.bind("<FocusOut>", self.on_focus_out, add=True)

        self.value_editor.bind("<Return>", self.on_end_edit, add=True)
        self.value_editor.bind("<Escape>", self.on_cancel_edit, add=True)
        
        # Give the focus to the editor
        self.value_editor.focus()
    
    def on_cancel_edit(self, event):
        """Cancel the current edit and remove the active editor widget."""
        # Destroy the editor and set the internal widgets to None
        self.value_editor.destroy()
        self.value_editor = None
        self.value_label = None
    
    def on_focus_out(self, event):
        """End editing when the current editor loses focus."""
        pass
        #self.on_end_edit(event)

    def on_end_edit(self, event):
        """Finalize editing, validate the new value, and update the property."""
        # If we have a valid property and a valid label
        if self.value_editor is not None and self.value_label is not None:
            # ignore end edit if popup was opened
            if self.value_editor.popup:
                return

            # Update the value in the props dictionary
            prop = self.props[self.value_label]
            try:
                value = self.value_editor.get_value()
                if self.value_editor.on_validate(value):
                    if prop["value"] != value:
                        prop["value"] = value
                        # Update the selected object
                        if self._selected_object:
                            self._selected_object.update_value(self)
                        # Update the label text with the value of the editor
                        self.update_value_label(self.value_label)
                        # Generate ValueChanged event
                        self.event_generate("<<ValueChanged>>")
                else:
                    raise ValueError("Validation of property editor failed.") 
            except:
                self.value_editor.config(bootstyle=tk.DANGER)
                raise
      
            # Generate the EndEdit event
            self.event_generate("<<EndEdit>>")

            # Destroy the edior and set the internal widgets to None
            self.value_editor.destroy()
            self.value_editor = None
            self.value_label = None
            
        # Configure the prop descriptor if available
        self.update_prop_descriptor(None)
   
    def clear(self):
        """Clear all properties and reset the grid state."""
        # Cancel editing
        # End a previous editor
        try:
            self.on_end_edit(None)
        except:
            return

        # Clear the colapsable frame
        self.cf.grid_forget()
        self.cf.clear()
        self.cf.grid(row=3, column=0, sticky=tk.NSEW)


        # Reset internal vars
        self.props={}
        self.categories = {}
        self.category_rows = {}
        self.value_editor = None
        self.value_label = None

    def on_clear_filter(self):
        """Clear the filter text and refresh the visible properties."""
        # Clear search entry
        self.entry_filter.delete(0, tk.END)
        self.on_filter()

    def on_filter(self):
        """Show or hide properties based on the filter text."""
        # Get the search entry
        find_str = str(self.entry_filter.get())
        
        # Filter the labels regarding the search entry
        for prop in self.props.values():
            if find_str in prop["displayname"] or find_str in str(prop["value"]):
                # Show item if search entry matches
                prop["frame"].grid()
            else:
                # Remove item if search entry does not match
                prop["frame"].grid_remove()

    def set_selected_object(self, object):
        """Set the currently selected object and populate its properties."""
        # End edit mode
        if self._selected_object:
            # End a previous editor
            try:
                self.on_end_edit(None)
            except:
                return
        # Store the new object
        self._selected_object = object
 
        # Update object label
        if self._selected_object is not None:
            self.object_name.config(text="Properties of " + type(self._selected_object).__name__)
        else:
            self.object_name.config(text="")
       
        # Clear property grid if object is none
        if not self._selected_object:
            self.clear()
        else:
            self.clear()
            self._selected_object.fill_propertygrid(self)

if __name__ == "__main__":
    # Create app window
    app = ttk.Window()

    Images().color_map = {}

    # Create repository
    grid = PropertyGrid(app)
    grid.pack(fill=tk.BOTH, expand=tk.YES)

    # Common editors
    grid.add_category("Common")
    grid.add_property(
        "Common", "prop1", "str value", 
        "str", "String editor", "A String value property.")
    grid.add_property(
        "Common", "prop2", "str value readonly", 
        "str", "String editor readonly", "A readonly string value property.", 
        state=tk.READONLY)
    grid.add_property(
        "Common", "prop3", "dontuse123", 
        "password", "Password editor", "Sets the password.")
    grid.add_property(
        "Common", "prop4", "5.0", 
        "float", "Float editor", "A float value property.")
    grid.add_property(
        "Common", "prop5", "5.0", 
        "float", "Float editor (Min/Max)", "A float value property with min and max options.",
        options={"min":1.0, "max":20.0})
    grid.add_property(
        "Common", "prop6", "5", 
        "int", "Int editor", "An int value property.")
    grid.add_property(
        "Common", "prop7", "5", 
        "int", "Int editor (Min/Max)", "An int value property with min and max options.",
        options={"min":1, "max":20})
    grid.add_property(
        "Common", "prop8", False,
        "bool", "Bool editor", "A boolean value editor.")

    grid.add_property(
        "Common", "prop8_1", False,
        "bool_combo", "Bool combo editor", "Another boolean value editor.")
    
    # Special editors
    grid.add_category("Special")
    grid.add_property(
        "Special", "prop10", "0D", 
        "option", "Option Editor", "A dropdown list editor.", 
        options=["unknown", "0D", "1D", "2D", "3D"])
    grid.add_property(
        "Special", "prop10_1", "val", 
        "combo", "Combobox Editor", "A combobox editor.", 
        options=["unknown", "val0", "val1", "vla2", "val3"])
    grid.add_property(
        "Special", "prop11", 5,
        "spinbox", "Spinbox editor", "A spinbox editor.", 
        options={"from_":1, "to":10})
    grid.add_property(
        "Special", "prop11_1", 5,
        "slider", "Slider editor", "A slider editor.", 
        options={"from_":1, "to":10})
    grid.add_property(
        "Common", "prop12", [4.0, 20.0],
        "range", "Range editor", "A range value editor with two float entries")
    grid.add_property(
        "Special", "prop13", "#121212", 
        "color", "Color editor", "A color popup editor")
    grid.add_property(
        "Special", "prop13_1", "#121212", 
        "color_str", "Color editor entry", "A color entry editor")
    grid.add_property(
        "Special", "prop13_2", "tab10",
        "color_map", "Color map", "Sets the color map for the chart.",
        options=['Pastel1', 'Pastel2', 'Paired', 'Accent',
                'Dark2', 'Set1', 'Set2', 'Set3',
                'tab10', 'tab20', 'tab20b', 'tab20c'])

    grid.add_property(
        "Special", "prop14", Font(),
        "font", "Font editor", "A font dropdown editor.")
    grid.add_property(
        "Special", "prop15", "c:/",
        "dir", "Directory picker", "A directory picker editor.")
    grid.add_property(
        "Special", "prop16", "c:/test.txt",
        "file", "File picker", "A file picker editor.",
        options={"filetypes": [("Simunet files", "*.sim"), ("All files", "*")]})
    grid.add_property(
        "Special", "prop17", datetime.date(2000,1,1),
        "date", "Date popup editor", "A date popup editor.",
        options="%d.%m.%Y")
    grid.add_property(
        "Special", "prop17_1", datetime.date(2000,1,1),
        "date_str", "Date editor", "A date editor.",
        options="%d.%m.%Y")
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
    grid.add_property(
        "Special", "prop18", [],
        "multi_var", "A multi variable picker", "A multi variable picker editor.",
        options=options)

    grid.add_property(
        "Special", "prop19", [],
        "single_var", "A single variable picker", "A single variable picker editor.",
        options=options)

    grid.add_property(
        "Special", "prop20", "def __init__():\n    pass",
        "code", "A source code editor", "A source code editor.")

    grid.add_property(
        "Special", "prop21", [30.0, "°C"],
        "quantity", "Physical quantity editor", "A physical quantity editor.",
        options="K")

    grid.add_property(
        "Special", "prop21", [30.0, "°C"],
        "quantity", "Physical quantity editor", "A physical quantity editor.",
        options="K")

    table_header = ["A", "B", "C"]
    table_data = [
        ["1", 30, "324"],
        ["2", 25, "345435"],
        ["4", 35, "567856757"]
    ]
    grid.add_property(
        "Special", "prop22", [table_header, table_data],
        "table", "Table editor", "An inline table editor.")
    app.mainloop()  