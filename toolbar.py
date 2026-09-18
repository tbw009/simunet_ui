"""Toolbar widget for ribbon-style button groups."""

import ttkbootstrap as ttk
import ttkbootstrap.constants as tk
from tooltip import Tooltip
from images import Images


class Toolbar(ttk.Frame):
    """Frame-based toolbar that creates buttons and menu items."""

    def __init__(
            self, master, tb_images, tb_items, 
            btn_style=tk.GHOST, 
            btn_style_checked=tk.PRIMARY, 
            show_text=True, **kwargs):
        """Initialize the toolbar and create toolbar items.

        Args:
            master: Parent widget.
            tb_images: Dictionary of toolbar images.
            tb_items: List of toolbar item definitions.
            btn_style: Default button bootstyle.
            btn_style_checked: Bootstyle for checked buttons.
            show_text: Whether to display button text.
            **kwargs: Additional Frame options.
        """

        # Init base
        super().__init__(master, **kwargs)

        # Create a separator
        sep = ttk.Separator(self, orient= tk.HORIZONTAL)
        sep.pack(side=tk.BOTTOM, fill=tk.X)

        # Toolbar properties
        self.btn_style = btn_style
        self.btn_style_checked = btn_style_checked
        self.show_text = show_text
        self.tb_images = tb_images

        # Add all items into the toolbar fame
        self.tb_widgets = {}
        self.tb_widgets_state = {}

        # Create toolbar items
        if tb_items:
            self.create_items(tb_items)

    def create_option_button(self, id, image, text, tooltip, options):
        """Create a drop-down menu button in the toolbar.
        
        Args:
            id: Unique identifier for the button.
            image: Image for the button.
            text: Text for the button.
            tooltip: Tooltip text for the button.
            options: List of options for the drop-down menu.
        """
        btn = ttk.Menubutton(
            self,                   
            bootstyle=self.btn_style, 
            image=self.tb_images[image], 
            takefocus=False,
            text=text,
            compound=tk.TOP if self.show_text else tk.NONE)
        btn.pack(side=tk.LEFT, fill=tk.Y)

        # Create options menu
        if options:
            sub_menu = ttk.Menu(btn, tearoff=True)
            btn.config(menu=sub_menu) 

            for entry in options:
                if entry == "---":
                    sub_menu.add_separator()
                else:
                    menu_id, menu_image, menu_text, menu_tooltip, menu_callback = entry
                    sub_menu.add_command(
                        label=menu_text, underline=0, 
                        image=self.tb_images[menu_image], 
                        compound=tk.LEFT, 
                        command=menu_callback)

        # Create Tooltip
        if tooltip:
            Tooltip(btn, text=tooltip)

        # Store widget and state
        self.tb_widgets[id] = btn
        self.tb_widgets_state[btn] = "normal"

    def create_tool_button(self, id, image, text, tooltip, callback):
        """Create a toolbar button that invokes a callback.
        
        Args:
            id: Unique identifier for the button.
            image: Image for the button.
            text: Text for the button.
            tooltip: Tooltip text for the button.
            callback: Function to call when the button is clicked.
        """
        btn = ttk.Button(
            self,                   
            bootstyle=self.btn_style, 
            image=self.tb_images[image], 
            takefocus=False,
            text=text,
            compound=tk.TOP if self.show_text else tk.NONE,
            command=callback)
        btn.pack(side=tk.LEFT, fill=tk.Y)

        # Create Tooltip
        if tooltip:
            Tooltip(btn, text=tooltip)

        # Store widget and state
        self.tb_widgets[id] = btn
        self.tb_widgets_state[btn] = "normal"

    def create_separator(self):
        """Insert a vertical separator between toolbar groups."""
        sep = ttk.Separator(self, orient=tk.VERTICAL)
        sep.pack(side=tk.LEFT, fill=tk.Y)
    
    def create_items(self, tb_items):
        """Create toolbar widgets from a list of item definitions.
        
        Args:
            tb_items: List of toolbar item definitions.
        """
        for item in tb_items:
            if item == "---":
                self.create_separator()
            else:            
                id, image, text, tooltip, callback = item

                if type(callback) is list:
                    # Create an option button
                    self.create_option_button(id, image, text, tooltip, callback)
                else:
                    # create a default toolbutton
                    self.create_tool_button(id, image, text, tooltip, callback)

    def set_checked(self, key, checked):
        """Set the checked state of a toolbar button.
        
        Args:
            key: Unique identifier for the button.
            checked: Boolean indicating whether the button is checked.
        """
        btn = self.tb_widgets[key]
        if checked:
            btn.configure(bootstyle=self.btn_style_checked)
            self.tb_widgets_state[btn] = "checked"
        else:
            btn.configure(bootstyle=self.btn_style)
            self.tb_widgets_state[btn] = "normal"

    def set_enabled(self, key, enabled):
        """Enable or disable a toolbar button.
        
        Args:
            key: Unique identifier for the button.
            enabled: Boolean indicating whether the button is enabled.
        """
        if enabled:
            self.tb_widgets[key].configure(state="enabled")
        else:
            self.tb_widgets[key].configure(state="disabled")

if __name__ == "__main__":
    # Create app window
    app = ttk.Window()

    # Toolbar items
    # id, image, text, hint, callback
    tb_items=[
        ("New", "New", "New", "New Document", None),
        ("Open", "Open", "Open", "Open existing Document", None),
        ("Save", "Save", "Save", "Save Document", None),
        ("Print", "Print", "Print", "Print Document", None),
        "---",
        ("Export", "Export", "Export", "Export document", None),
        "---",
        ("Undo", "Undo", "Undo", "Undo previous action", None),
        ("Redo", "Redo", "Redo", "Redo last action", None),
        "---",
        ("Cut", "Cut", "Cut", "Cut selected objects", None),
        ("Copy", "Copy", "Copy", "Copy selected objects to clipboard", None),
        ("Paste", "Paste", "Paste", "Paste objecs from clipboard", None),
        "---",
        ("PanelLeft", "PanelLeft", "Repostory", "Toggle repository", None),
        ("PanelRight", "PanelRight", "Property Grid", "Toggle property grid", None),
        ("PanelBottom", "PanelBottom", "Output", "Toggle output", None),
        "---",
        ("SortObjects", "SortObjects", "Sort", "Sort objects", [
            ("BringForward", "BringForward", "Bring forward", "Bring forward", None),
            ("BringToFront", "BringToFront", "Bring to front", "Bring to front", None),
            ("SendToBack", "SendToBack", "Send to back", "Send to back", None),
            ("SendBackward", "SendBackward", "Send backward", "Send backward", None)
        ]),
        "---",
        ("AlignObjects", "AlignObjects", "Align", "Align objects", [
            ("AlignVerticalLeft", "AlignVerticalLeft", "Align left", "Align left", None),
            ("AlignVerticalCenter", "AlignVerticalCenter", "Align vertical center", "Align vertical center", None),
            ("AlignVerticalRight", "AlignVerticalRight", "Align right", "Align right", None),
            ("AlignHorizontalTop", "AlignHorizontalTop", "Align top", "Align top", None),
            ("AlignHorizontalCenter", "AlignHorizontalCenter", "Align horizontal center", "Align horizontal center", None),
            ("AlignHorizontalBottom", "AlignHorizontalBottom", "Align bottom", "Align bottom", None)
        ]),
        "---",
        ("Info", "Info", "Info", "About ...", None),
        "---"
    ]

    images = Images().ribbon

    # Create the toolbar
    toolbar = Toolbar(app, images, tb_items)
    toolbar.pack(side=tk.TOP, fill=tk.X)
    container = ttk.Frame(app, height=200, padding=10)
    container.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES)
    app.mainloop()

