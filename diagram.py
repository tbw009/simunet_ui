"""Diagram container widget with ruler, sheet, and toolbar support.

The Diagram frame hosts a drawing sheet, rulers, scrollbars, and a
toolbar. It synchronizes ruler movement, zoom events, and UI state
based on sheet interactions.
"""

from ruler import Ruler
from sheet import Sheet
from toolbar import Toolbar
from images import Images
import ttkbootstrap as ttk
import ttkbootstrap.constants as tk


class Diagram(ttk.Frame):
    """Frame widget that composes a drawing diagram editor."""

    COLORS = {
        "sheet": "#ffffff"
    }

    def __init__(self, master, width=2500, height=2500, **kwargs):
        """Initialize the diagram container.

        Args:
            master: Parent widget.
            width: Width of the drawing sheet.
            height: Height of the drawing sheet.
            **kwargs: Additional Frame options.
        """
        super().__init__(master, **kwargs)
        
        # Create toolbar images
        self.images = Images().ribbon

        # Create horizontal ruler
        self.hr = Ruler(
            self, length=width, orient=tk.HORIZONTAL, 
            highlightthickness=0)
        self.hr.grid(row=1, column=1, sticky=tk.NSEW)
        
        # Create vertical ruler
        self.vr = Ruler(
            self, length=height, orient=tk.VERTICAL, 
            highlightthickness=0)
        self.vr.grid(row=2, column=0, sticky=tk.NSEW)
        self.ruler_visible = True

        # Create sheet canvas
        self.sheet = Sheet(
            self, sheet_width=width, sheet_height=height,  
            autostyle=False, highlightthickness=0, bg=self.COLORS["sheet"])
        self.sheet.grid(row=2, column=1, sticky =tk.NSEW)
        
        # Bind events of the sheet
        self.sheet.bind("<Enter>", self.on_sheet_enter, add=True)
        self.sheet.bind("<Leave>", self.on_sheet_leave, add=True)
        self.sheet.bind("<Motion>", self.on_sheet_motion, add=True)
        self.sheet.bind("<MouseWheel>", self.on_sheet_mouse_wheel, add=True)
        self.sheet.bind("<<GridChanged>>", self.on_grid_changed, add=True)
        self.sheet.bind("<<SnapChanged>>", self.on_snap_changed, add=True)
        self.sheet.bind("<<ZoomChanged>>", self.on_zoom_changed, add=True)
        self.sheet.bind("<<FocusChanged>>", self.on_focus_changed, add=True)
        self.sheet.bind("<<SelectionChanged>>", self.on_selection_changed, add=True)
        self.sheet.bind("<<ScanMark>>", self.on_scan_mark, add=True)
        self.sheet.bind("<<ScanDragTo>>", self.on_scan_dragto, add=True)
        self.sheet.bind("<<DimensionsChanged>>", self.on_dimensions_changed, add=True)
 
        # Create x-scrollhandler
        def xviews(*args):
            self.sheet.xview(*args)
            self.hr.xview(*args)
        # Create y-scrollhandler
        def yviews(*args):
            self.sheet.yview(*args)
            self.vr.yview(*args)

        # Create x-scrollbar and attach widget
        self.sb_x = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=xviews)
        self.sb_x.grid(row=3, column=1, sticky=tk.EW)
        self.sheet.config(xscrollcommand=self.sb_x.set)
        self.hr.config(xscrollcommand=self.sb_x.set)

        # Create y-scrollbar and attach widget
        self.sb_y = ttk.Scrollbar(self, orient=tk.VERTICAL, command=yviews)
        self.sb_y.grid(row=2, column=2, sticky=tk.NS)
        self.sheet.config(yscrollcommand=self.sb_y.set)
        self.vr.config(yscrollcommand=self.sb_y.set)

        # Create toolbar
        self.create_toolbar()
        self.toolbar.grid(row=0, columnspan=3, sticky=tk.NSEW)
        self.toolbar_visible = True

        # Configure grid rows and columns
        self.columnconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        
        # Update toolbar items
        self.update_ui()

    def create_toolbar(self):
        """Create the toolbar and populate available actions."""
        tb_items=[
            ("SelectAll", "SelectAll", "Select all", "Select all objects", self.sheet.on_select_all),
            ("Duplicate", "Duplicate", "Duplicate", "Duplicate selected objects", self.sheet.duplicate_selected),
            ("Delete", "Delete", "Delete", "Delete selection", self.sheet.delete_selected),
            "---",
            ("Gridlines", "Gridlines", "Toggle grid", "Toggle grid", self.sheet.toggle_grid),
            ("Ruler", "Ruler", "Toggle ruler", "Toggle ruler", self.toggle_ruler),
            ("SnapToGrid", "SnapToGrid", "Snap to grid", "Snap to grid", self.sheet.toggle_snap_to_grid),
            "---",
            ("ZoomIn", "ZoomIn", "Zoom in", "Zoom in", self.sheet.zoom_in),
            ("Zoom100Percent", "Zoom100Percent", "Zoom 100%", "Zoom 100%", self.sheet.zoom_100),
            ("ZoomOut", "ZoomOut", "Zoom out", "Zoom out", self.sheet.zoom_out),
            "---",
            ("SortObjects", "SortObjects", "Sort objects", "Sort objects", [
                ("BringForward", "BringForward", "Bring forward", "Bring forward", self.sheet.bring_forward),
                ("BringToFront", "BringToFront", "Bring to front", "Bring to front", self.sheet.bring_to_front),
                ("SendToBack", "SendToBack", "Send to back", "Send to back", self.sheet.send_to_back),
                ("SendBackward", "SendBackward", "Send backward", "Send backward", self.sheet.send_backward)
            ]),
            "---",
            ("AlignObjects", "AlignObjects", "Align objects", "Align objects", [
                ("AlignVerticalLeft", "AlignVerticalLeft", "Align left", "Align left", self.sheet.align_vertical_left),
                ("AlignVerticalCenter", "AlignVerticalCenter", "Align vertical center", "Align vertical center", self.sheet.align_vertical_center),
                ("AlignVerticalRight", "AlignVerticalRight", "Align right", "Align right", self.sheet.align_vertical_right),
                ("AlignHorizontalTop", "AlignHorizontalTop", "Align top", "Align top", self.sheet.align_horizontal_top),
                ("AlignHorizontalCenter", "AlignHorizontalCenter", "Align horizontal center", "Align horizontal center", self.sheet.align_horizontal_center),
                ("AlignHorizontalBottom", "AlignHorizontalBottom", "Align bottom", "Align bottom", self.sheet.align_horizontal_bottom)
            ]),
           "---"
        ]

        self.toolbar = Toolbar(self, self.images, tb_items, show_text=True)
  
    def on_toggle_toolbar(self):
        """Toggle the toolbar visibility."""
        if self.toolbar_visible:
            self.toolbar.grid_remove()
            self.toolbar_visible = False
        else:
            self.toolbar.grid()
            self.toolbar_visible = True

    def on_dimensions_changed(self, event):
        """Update ruler lengths when sheet dimensions change."""
        self.hr.length = self.sheet.sheet_width
        self.vr.length = self.sheet.sheet_height
        self.hr.update_dimensions()
        self.vr.update_dimensions()

    def on_scan_mark(self, event):
        """Record the scan origin when the sheet drag begins."""
        self.hr.scan_mark(event.x, 0)
        self.vr.scan_mark(0, event.y)

    def on_scan_dragto(self, event):
        """Move rulers while the sheet is dragged."""
        self.hr.scan_dragto(event.x, 0, gain=1)
        self.vr.scan_dragto(0, event.y, gain=1)

    def on_sheet_mouse_wheel(self, event):
        """Scroll the vertical ruler in response to mouse wheel movement."""
        self.vr.yview("scroll", -1 * int(event.delta / 120), "units")

    def on_sheet_leave(self, event):
        """Hide ruler indicators when the cursor leaves the sheet."""
        self.hr.hide_position()
        self.vr.hide_position()

    def on_sheet_enter(self, event):
        """Show ruler indicators when the cursor enters the sheet."""
        self.hr.show_position()
        self.vr.show_position()
    
    def on_sheet_motion(self, event):
        """Update ruler indicator positions while the mouse moves on the sheet."""
        self.hr.set_position(self.sheet.x)
        self.vr.set_position(self.sheet.y)

    def hide_ruler(self):
        """Hide both horizontal and vertical rulers."""
        self.hr.grid_remove()
        self.vr.grid_remove()
        self.ruler_visible = False

    def show_ruler(self):
        """Show both rulers and synchronize scroll position."""
        self.vr.grid()
        self.hr.grid()
        self.ruler_visible = True
        
        self.vr.yview_moveto(self.sheet.yview()[0])
        self.hr.xview_moveto(self.sheet.xview()[0])

    def on_zoom_changed(self, event):
        """Synchronize ruler scaling when the sheet zoom changes."""
        self.hr.set_zoom_factor(self.sheet.zoom_factor)
        self.vr.set_zoom_factor(self.sheet.zoom_factor)

        self.hr.set_position(self.sheet.x)
        self.vr.set_position(self.sheet.y)

        self.update_ui()

    def on_grid_changed(self, event):
        """Refresh toolbar state when grid visibility changes."""
        self.update_ui()

    def on_snap_changed(self, event):
        """Refresh toolbar state when snap-to-grid changes."""
        self.update_ui()

    def on_focus_changed(self, event):
        """Refresh toolbar state when focus changes."""
        self.update_ui()

    def on_selection_changed(self, event):
        """Refresh toolbar state when selection changes."""
        self.update_ui()

    def toggle_ruler(self):
        """Toggle ruler visibility and generate change event."""
        if self.ruler_visible:
            self.hide_ruler()
        else:
            self.show_ruler()

        self.event_generate("<<RulerChanged>>")
        self.update_ui()

    def update_ui(self):
        """Update toolbar buttons and checked state based on sheet state."""
        self.toolbar.set_enabled("Duplicate", len(self.sheet.selected_shapes) > 0)
        self.toolbar.set_enabled(
            "Delete",
            len(self.sheet.selected_shapes) > 0 or self.sheet.selected_connector,
        )
        self.toolbar.set_checked("Gridlines", self.sheet.grid_visible)
        self.toolbar.set_checked("Ruler", self.ruler_visible)
        self.toolbar.set_checked("SnapToGrid", self.sheet.snap_to_grid)
        self.toolbar.set_enabled(
            "ZoomIn", self.sheet.get_zoom_factor() < self.sheet.zoom_factor_max
        )
        self.toolbar.set_enabled(
            "Zoom100Percent", self.sheet.get_zoom_factor() != 1.0
        )
        self.toolbar.set_enabled(
            "ZoomOut", self.sheet.get_zoom_factor() > self.sheet.zoom_factor_min
        )

        sort_enabled = self.sheet.focused in self.sheet.shapes
        self.toolbar.set_enabled("SortObjects", sort_enabled)

        align_enabled = (
            self.sheet.focused is not None
            and len(self.sheet.selected_shapes) > 1
        )
        self.toolbar.set_enabled("AlignObjects", align_enabled)

if __name__ == "__main__":
    # Create app window
    app = ttk.Window()
    dia = Diagram(app, bootstyle=tk.LIGHT)
    dia.pack(fill=tk.BOTH, expand=True)

    app.mainloop()        


