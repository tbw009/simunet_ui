"""Ribbon and ribbon bar UI components for toolbar grouping and actions."""

import ttkbootstrap as ttk
import ttkbootstrap.constants as tk
from tooltip import Tooltip
from images import Images
from PIL import Image, ImageDraw, ImageTk


class Ribbon(ttk.Frame):
    """Toolbar group container that holds ribbon tool buttons and option menus."""

    def __init__(
            self, master, tb_images, 
            btn_style=tk.GHOST, 
            btn_style_checked=tk.PRIMARY, 
            **kwargs):
        """Initialize the ribbon group with image assets and button styles."""

        super().__init__(master, **kwargs)

        # Ribbon properties
        self.btn_style = btn_style
        self.btn_style_checked = btn_style_checked
        self.tb_images = tb_images

        # Store all groups, items and their states in dictionaries
        self.tb_widgets = {}
        self.tb_widgets_state = {}
        self.groups = {}

    def create_option_button(self, group, id, image, text, tooltip, options):
        """Create a menubutton with a dropdown menu for grouped options."""
        btn = ttk.Menubutton(
            group["items"],
            bootstyle=self.btn_style, 
            image=self.tb_images[image], 
            takefocus=False,
            text=text,
            compound=tk.TOP)
        btn.pack(side=tk.LEFT, fill=tk.Y)

        # Create options menu
        if options:
            sub_menu = ttk.Menu(btn, tearoff=1)
            btn.config(menu=sub_menu) 
            
            for entry in options:
                if entry == "---":
                    sub_menu.add_separator()
                else:
                    menu_id, menu_image, menu_text, menu_tooltip, menu_callback = entry
                    sub_menu.add_command(
                        label=menu_text, 
                        underline=0, 
                        image=self.tb_images[menu_image], 
                        compound=tk.LEFT,
                        command=menu_callback)
        
        # Create Tooltip
        if tooltip:
            Tooltip(btn, text=tooltip)

        # Store widget and state
        self.tb_widgets[id] = btn
        self.tb_widgets_state[btn] = "normal"

    def create_tool_button(self, group, id, image, text, tooltip, callback):
        """Create a standard toolbar button for the ribbon group."""
        btn = ttk.Button(
            group["items"],                   
            bootstyle=self.btn_style, 
            image=self.tb_images[image], 
            takefocus=False,
            text=text,
            compound=tk.TOP,
            command=callback)
        btn.pack(side=tk.LEFT, fill=tk.Y)

        # Create Tooltip
        if tooltip:
            Tooltip(btn, text=tooltip)

        self.tb_widgets[id] = btn
        self.tb_widgets_state[btn] = "normal"

    def create_separator(self, group):
        """Insert a vertical separator between ribbon buttons."""
        sep = ttk.Separator(group["items"], orient=tk.VERTICAL)
        sep.pack(side=tk.LEFT, fill=tk.Y)

    def add_items(self, tb_items):
        """Add ribbon items and separators from the toolbar item definition."""
        for item in tb_items:

            group = self.get_group(item)
            entries = tb_items[item]            

            for entry in entries:
                if entry == "---":
                    # Create a separator
                    self.create_separator(group)
                else:
                    # Add toolbar item
                    id, image, text, tooltip, callback = entry

                    if type(callback) is list:
                        # Create an option button
                        self.create_option_button(group, id, image, text, tooltip, callback)
                    else:
                        # create a default toolbutton
                        self.create_tool_button(group, id, image, text, tooltip, callback)


    def get_group(self, group):
        """Return or create a named ribbon group container."""
        if group not in self.groups:
            # Create a new group frame
            grp = ttk.Frame(self)
            grp.pack(side=tk.LEFT)

            # Create a nested frame for the items
            frm = ttk.Frame(grp)
            frm.grid(row=0, column=0)

            # Create the group label
            lbl = ttk.Label(grp, text=group)
            lbl.grid(row=1, column=0, pady=(2, 0))

            # Create a separator
            sep = ttk.Separator(grp, orient=tk.VERTICAL)
            sep.grid(row=0, column=1, rowspan=2, sticky=tk.NS)

            # Store the group in the groups dict
            self.groups[group] = { 
                "group" : grp,
                "label" : lbl,
                "items" : frm
            }
        
        # return the group
        return self.groups[group]
    
    def set_checked(self, key, checked):
        """Set the checked state for a ribbon button."""
        btn = self.tb_widgets[key]
        if checked:
            btn.configure(bootstyle=self.btn_style_checked)
            self.tb_widgets_state[btn] = "checked"
        else:
            btn.configure(bootstyle=self.btn_style)
            self.tb_widgets_state[btn] = "normal"

    def set_enabled(self, key, enabled):
        """Enable or disable a ribbon button by key."""
        if enabled:
            self.tb_widgets[key].configure(state="enabled")
        else:
            self.tb_widgets[key].configure(state="disabled")
      

class RibbonBar(ttk.Frame):
    """Tabbed ribbon bar containing multiple ribbon tool groups."""

    def __init__(
            self, master, tb_images, 
            btn_style=tk.GHOST, 
            btn_style_checked=tk.PRIMARY, 
            **kwargs):
        """Initialize the ribbon bar with toolbar image assets and styles."""

        super().__init__(master, **kwargs)

        # Ribbon properties
        self.btn_style = btn_style
        self.btn_style_checked = btn_style_checked
        self.tb_images = tb_images

        # Create the ribbon
        self.nb = ttk.Notebook(self, padding=(0, -1, 0, 0))
        self.nb.pack(side=tk.TOP, fill=tk.X, expand=tk.YES)

        self.ribbons = {}

    def add_items(self, ribbon_items):
        """Create ribbon tabs from the provided ribbon item definitions."""
        for key in ribbon_items:
            # Create ribbon
            ribbon = Ribbon(
                self.nb, self.tb_images,
                btn_style=self.btn_style,
                btn_style_checked=self.btn_style_checked)
            ribbon.add_items(ribbon_items[key])
            
            # Add ribbon
            self.add_ribbon(key, ribbon)

    def add_ribbon(self, key, ribbon):
        """Add a ribbon tab to the ribbon bar notebook."""
        self.ribbons[key] = ribbon
        # Add ribbon to notebook
        self.nb.add(ribbon, text = "   {}   ".format(key), padding=-1)
    

if __name__ == '__main__':
    # Create and runn app
    test = ttk.Window()
    
    # Set geometry
    test.title("New Document")
    test.geometry("1200x600+100+100")
       
    # Create the mainframe
    images = Images().ribbon

    # Ribbon items
    # id, image, text, hint, callback
    ribbon_items = {
        "File": {
            "Project" : [
                ("New", "New", "New", "New Document", None),
                ("Open", "Open", "Open", "Open existing Document", None),
                ("Save", "Save", "Save", "Save Document", None),
                ("SaveAs", "SaveAs", "Save As", "Save document as...", None),
                "---",
                ("Export", "Export", "Export", "Export document...", None),
            ],
            "Print" : [
                ("Print", "Print", "Print", "Print Document", None),
                ("PrintPreview", "PrintPreview", "Print Preview", "Print preview...", None)
            ],
            "Simulation" : [
                ("Start", "Start", "Start", "Start the simulation", None),
                ("Stop", "Stop", "Stop", "Stop the simulation", None),
            ]
        },
        "Edit": {
            "Clipboard": [
                ("Cut", "Cut", "Cut", "Cut selected objects", None),
                ("Copy", "Copy", "Copy", "Copy selected objects to clipboard", None),
                ("Paste", "Paste", "Paste", "Paste objecs from clipboard", None),
            ],
            "Edit" : [
                ("Undo", "Undo", "Undo", "Undo previous action", None),
                ("Redo", "Redo", "Redo", "Redo last action", None),
                "---",
                ("SelectAll", "SelectAll", "Select all", "Select all objects", None),
                ("Duplicate", "Duplicate", "Duplicate", "Duplicate selected objects", None),
                ("Delete", "Delete", "Delete", "Delete selection", None),
            ]
        },
        "Arrange": {
            "Sort Objects": [
                ("BringForward", "BringForward", "Forward", "Bring forward", None),
                ("BringToFront", "BringToFront", "To front", "Bring to front", None),
                ("SendToBack", "SendToBack", "To back", "Send to back", None),
                ("SendBackward", "SendBackward", "Backward", "Send backward", None)
            ],
            "Align Objects" :[
                ("AlignVerticalLeft", "AlignVerticalLeft", "Left", "Align vertical left", None),
                ("AlignVerticalCenter", "AlignVerticalCenter", "Vertical center", "Align vertical center", None),
                ("AlignVerticalRight", "AlignVerticalRight", "Right", "Align vertical right", None),
                ("AlignHorizontalTop", "AlignHorizontalTop", "Top", "Align horizontal top", None),
                ("AlignHorizontalCenter", "AlignHorizontalCenter", "Horizontal center", "Align horizontal center", None),
                ("AlignHorizontalBottom", "AlignHorizontalBottom", "Bottom", "Align horizontal bottom", None)
            ]
        },
        "View": {
            "Panel" : [
                ("PanelLeft", "PanelLeft", "Repostory", "Toggle repository", None),
                ("PanelRight", "PanelRight", "Property Grid", "Toggle property grid", None),
                ("PanelBottom", "PanelBottom", "Output", "Toggle output", None)
            ],
            "Bars" : [
                ("Toolbar", "Toolbar", "Toolbar","Toggle toolbar", None),
                ("Statusbar", "Statusbar", "Statusbar", "Toggle statusbar", None),
            ],
            "Sheet" : [
                ("Gridlines", "Gridlines", "Grid", "Toggle grid", None),
                ("Ruler", "Ruler", "Ruler", "Toggle ruler", None),
                ("SnapToGrid", "SnapToGrid", "Snap to grid", "Snap to grid", None),
            ],
            "Zoom" : [
                ("ZoomOut", "ZoomOut", "Zoom out", "Zoom out", None),
                ("Zoom100Percent", "Zoom100Percent", "Zoom 100%", "Zoom 100%", None),
                ("ZoomIn", "ZoomIn", "Zoom in", "Zoom in", None),
            ],
            "Results" : [
                ("Refresh", "Refresh", "Refresh", "Refresh the drawing area", None),
                ("Reset", "Reset", "Reset", "Reset the current config to default", None),
            ]
        },
        "Help": {
            "Info" : [
                ("Info", "Info", "About...", "About ...", None)
            ]
        }
    }

    themes =[]
    styles = test.style._theme_definitions
    for key in styles:
        bg = styles[key].colors.bg
        primary = styles[key].colors.primary
        secondary = styles[key].colors.secondary
        light = styles[key].colors.light
        img = Image.new('RGBA', (36, 24), (255, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle((0,0,34,23), fill=bg)
        draw.rectangle((2,2,10,21), fill=primary)
        draw.rectangle((13,2,21,21), fill=light)
        draw.rectangle((24,2,32,21), fill=secondary)
        images[key] = ImageTk.PhotoImage(img) 

        # id, image, text, hint, callback
        themes.append((key, key, key, key, None))   

    ribbon_items["View"]["Style"] = [
        ("Theme", "Theme", "Theme", "Select Theme", themes),
    ]

    # Create the ribbon
    ribbon = RibbonBar(test, images)
    ribbon.pack(fill=tk.X)
    ribbon.add_items(ribbon_items)

    
    test.mainloop()

