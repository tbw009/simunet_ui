"""Diagram sheet canvas and interaction logic.

This module defines the Sheet widget responsible for rendering shapes,
connectors, grid controls, zooming, selection, and clipboard operations.
"""

from tkinter import messagebox
import ttkbootstrap as ttk
import ttkbootstrap.constants as tk
from ttkbootstrap.window import Toplevel
from ttkbootstrap.style import Style
import copy
import os
import converter
from shape import Shape
from connector import Connector
from images import Images
from simunetcore import Model
from codeeditor import CodeEditorDialog
from tableeditor import TableEditorDialog
import canvasvg
import json


class Sheet(ttk.Canvas):
    """Canvas-based diagram sheet for building simulation graphs.

    The Sheet widget manages shape placement, connectors, selection,
    grid rendering, zooming, and clipboard operations.
    """
    
    # Sheet modes
    SELECT     = 0
    RUBBERBAND = 1
    MOVE       = 2
    CONNECT    = 3
    SHAPE      = 4
    PAN        = 5
    MODULE     = 6
    VALID      = 7
    INVALID    = 8

    # Cursors
    CURSORS =[
        "arrow",    # SELECT
        "arrow",    # RUBBERBAND
        "fleur",    # MOVE
        "tcross",   # CONNECT
        "dotbox",   # SHAPE
        "fleur",    # PAN
        "plus",     # MODULE
        "hand2",    # VALID
        "X_cursor"  # INVALID
    ]   

    # Gripper
    GRIPPER_SIZE = 6
    
    # Sheet colors
    COLORS = {
        "grid":   ["#eeeeee", "#cccccc", "#aaaaaa"],
        "select": ["#aeb8c2", "#dddddd"]
    }

    def __init__(self, master,  sheet_width, sheet_height, **kwargs):
        """Initialize the sheet widget and configure interaction bindings.

        Args:
            master: Parent widget.
            sheet_width: Width of the underlying sheet canvas.
            sheet_height: Height of the underlying sheet canvas.
            **kwargs: Additional Canvas options.
        """
        super().__init__(master, **kwargs)

        # Store dimensions
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height

        # Grid properties     
        self.grid_step = 10
        self.grid_visible = True      

        # Zoom properties
        self.zoom_factor = 1.0
        self.zoom_step = 0.1
        self.zoom_factor_min = 0.5
        self.zoom_factor_max = 2.5
        self.snap_to_grid = True

        # Mouse coords
        self.x = 0
        self.y = 0
        self.dx = 0
        self.dy = 0

        # Tooltips for shapes and ports
        self.tooltip_id = None
        self.toplevel = None

        # Event bindings
        self.bind('<ButtonPress-1>', self.on_left_down)
        self.bind('<ButtonRelease-1>', self.on_left_up)
        self.bind('<ButtonRelease-3>', self.on_right_up)
        self.bind('<Motion>', self.on_motion)
        self.bind('<Control-a>', self.on_select_all)
        self.bind('<Control-x>', self.on_cut)
        self.bind('<Control-c>', self.on_copy)
        self.bind('<Control-v>', self.on_paste)
        self.bind('<Up>', self.on_key_up)
        self.bind('<Down>', self.on_key_down)
        self.bind('<Left>', self.on_key_left)
        self.bind('<Right>', self.on_key_right)
        self.bind('<Delete>', self.on_key_del)
        self.bind('<BackSpace>', self.on_key_del)
        self.bind("<MouseWheel>", self.on_mouse_wheel)
        self.bind("<Control-MouseWheel>", self.on_ctrl_mouse_wheel)

        # Tags bindings
        self.tag_bind("in", "<Enter>", self.on_port_enter)
        self.tag_bind("in", "<Leave>", self.on_port_leave)
        self.tag_bind("out", "<Enter>", self.on_port_enter)
        self.tag_bind("out", "<Leave>", self.on_port_leave)
        self.tag_bind("connector", "<Enter>", self.on_connector_enter)
        self.tag_bind("connector", "<Leave>", self.on_connector_leave)
        self.tag_bind("shape", "<Enter>", self.on_shape_enter)
        self.tag_bind("shape", "<Leave>", self.on_shape_leave)
        self.tag_bind("icon", "<Enter>", self.on_shape_enter)
        self.tag_bind("icon", "<Leave>", self.on_shape_leave)

        # Create selection rectangle
        select_color = self.COLORS["select"]
        self.select_rect = self.create_rectangle(
            0, 0, 0, 0, 
            outline=select_color[0], stipple="gray25", #dash=(2,1),
            fill=select_color[1], tags="select_rect", state=tk.HIDDEN)

        # Create new shape rectangle
        self.new_shape_rect = self.create_rectangle(
            0, 0, 0, 0, 
            outline=select_color[0], stipple="gray25", #dash=(2,1),
            fill=select_color[1], tags="new_shape_rect", state=tk.HIDDEN)

        # Create new shape model name
        self.new_shape_label = self.create_text(
            0, 0 , fill=select_color[0],
            font=(Shape.FONT[0], int(Shape.FONT[1])), text="",
            tags=["text", "new_shape_label"])

        # Create focused shape rectangle
        focus_color = Style().colors.primary
        self.focus_rect = self.create_rectangle(
            0, 0, 0, 0, outline=focus_color, #dash=(2,1),
            tags="focus_rect", state=tk.HIDDEN)

        # Create focused connector line
        self.focus_line = self.create_line(
            0,0, 0,0, capstyle=tk.BUTT, joinstyle=tk.MITER,
            arrow=tk.LAST, width=2, 
            fill=focus_color, arrowshape=Connector.ARROW,
            tags=["focus_line"], state = tk.HIDDEN)

        # Some working vars:
        # Left button state
        self.lb_state = 0
        # Start position of a drag operation
        self.drag_start = None
        # The current connector (that is currently created)
        self.current_connector = None
        # The currently hovered port
        self.hovered_port = None
        # The currently hovered connector
        self.hovered_shape = None
        # The currently hovered connector
        self.hovered_connector = None
        # The selected repo item
        self.repo_item = None
        # The focused tag
        self.focused = None
        # The simulation project
        self.project = None

        # Shapes
        self.shapes = {}
        self.selected_shapes = []
        self.order =[]
        # Connectors
        self.connectors = {}
        self.selected_connector = None
   
        # Context menu
        self.create_context_menus()

        # Set inital mode
        self.set_mode(self.SELECT)

        # Update scroll region and create the grid
        self.update_dimensions()

        # Undo and redo
        self.undo_stack = []
        self.redo_stack = []

        # Subscribe to ThemeChanged message
        self.bind("<<ThemeChanged>>", self._on_theme_change)

    def clear(self):
        """Reset the sheet state and remove all shapes and connectors."""
        # Clear working vars
        self.drag_start = None
        self.current_connector = None
        self.hovered_port = None
        self.hovered_shape = None
        self.hovered_connector = None
        self.set_repo_item(None)
        self.set_focus(None)

        # Clear shapes 
        for shape in self.shapes:
            self.delete(shape)
        self.shapes.clear()

        # Clear connectors
        for connector in self.connectors:
            self.delete(connector)
        self.connectors.clear()

        # Clear selection
        self.selected_shapes.clear()
        self.order.clear()
        self.selected_connector = None

        # Set selection mode
        self.set_mode(self.SELECT)
        
        # Clear undo and redo stack
        self.undo_stack.clear()
        self.redo_stack.clear()

    def set_project(self, project):
        """Load a project onto the sheet by restoring shapes and connectors.

        Args:
            project: Project instance containing model and edge data.
        """
        self.clear()      
        self.project = project
        
        # Add shapes form project
        for shape_id in self.project.models:
            repo_path = self.project.models[shape_id]["path"]
            pos_x, pos_y = self.project.models[shape_id]["coords"]
            shape = Shape(
                self, int(pos_x*self.zoom_factor), int(pos_y*self.zoom_factor), 
                repo_path, self.zoom_factor, tag=shape_id)
            shape.set_model(Model.from_data(self.project.models[shape_id]["model"]))
            self.add_shape(shape)

        # Create connectors from edges
        for edge in self.project.edges:
            src_shape_id = edge[0]
            dest_shape_id = edge[1]
            src_port_id, dest_port_id = edge[2]["ports"]
            connector_id = edge[2].get("tag")

            connector = Connector(
                self, 
                (
                    src_shape_id, 
                    self.shapes[src_shape_id].model.y[src_port_id]["type"], 
                    src_port_id
                ), 
                (
                    dest_shape_id, 
                    self.shapes[dest_shape_id].model.u[dest_port_id]["type"], 
                    dest_port_id
                ), 
                self.zoom_factor, tag=connector_id)
            connector.set_var_map(self.project.var_map[dest_shape_id][dest_port_id])
            self.add_connector(connector)

        # Clear undo and redo stack
        self.undo_stack.clear()
        self.redo_stack.clear()

    def update_project(self):
        """Update the project data from the current sheet contents."""
        self.project.models.clear()

        # Prepare the models 
        for shape_id in self.shapes:
            shape = self.shapes[shape_id]
            self.project.models[shape_id] = {
                "class": shape.class_name,
                "model": shape.model.__dict__,
                "coords": [shape.x, shape.y],
                "path" : shape.repo_path
            }
        
        # Prepare the var_map 
        self.project.var_map.clear()
        for shape_id in self.shapes:
            self.project.var_map[shape_id] = {}

        # Prepare the edges 
        self.project.edges.clear()
        for connector_id in self.connectors:
            connector = self.connectors[connector_id]
            src_shape_id, _, src_port_id = connector.src_port
            dest_shape_id, _, dest_port_id = connector.dest_port

            # Append edge
            self.project.edges.append([
                src_shape_id, dest_shape_id, {
                    "ports": [src_port_id, dest_port_id],
                    "tag": connector_id,
                }
            ])

            # Set var map
            self.project.var_map[dest_shape_id][dest_port_id] = connector.var_map

    def create_round_rectangle(self, x1, y1, x2, y2, radius=20, **kwargs):
        """Draw a rounded rectangle on the canvas.

        Args:
            x1: Left coordinate.
            y1: Top coordinate.
            x2: Right coordinate.
            y2: Bottom coordinate.
            radius: Corner radius.
            **kwargs: Additional create_polygon options.

        Returns:
            Canvas item id for the rounded rectangle.
        """
        points = [
            x1+radius, y1, x1+radius, y1,
            x2-radius, y1, x2-radius, y1,
            x2, y1,
            x2, y1+radius, x2, y1+radius,
            x2, y2-radius, x2, y2-radius,
            x2, y2,
            x2-radius, y2, x2-radius, y2,
            x1+radius, y2, x1+radius, y2,
            x1, y2,
            x1, y2-radius, x1, y2-radius,
            x1, y1+radius, x1, y1+radius,
            x1, y1
        ]
        # Create polygon from point list
        return self.create_polygon(points, **kwargs, smooth=True)

    def create_arrow(self, x1, y1, x2, y2, **kwargs):
        """Draw an arrow-shaped port indicator on the canvas.

        Args:
            x1: Left coordinate.
            y1: Top coordinate.
            x2: Right coordinate.
            y2: Bottom coordinate.
            **kwargs: Additional create_polygon options.

        Returns:
            Canvas item id for the arrow polygon.
        """
        offset = (y2-y1)/2
        points = [
            x1, y1, 
            x1+offset, y1, 
            x2, y1+offset, 
            x1+offset, y2, 
            x1, y2,
            x1, y1, 
        ]
        # Create polygon from point list
        return self.create_polygon(points, **kwargs)
        
    def update_dimensions(self):
        """Update sheet dimensions, recreate the grid, and emit change events."""
        self.set_zoom_factor(self.zoom_factor)
        # Recreate grid
        self.create_grid()
        # Generate <<DimensionsChanged>> event
        self.event_generate("<<DimensionsChanged>>")      

    def set_mode(self, new_mode):
        """Switch the sheet interaction mode and update the cursor."""
        self.mode = new_mode
        # Select the corresponding cursor
        self.config(cursor=self.CURSORS[self.mode])

    def export_img(self, filename, margin=10):
        """Export the sheet contents to an SVG file.

        Args:
            filename: Output SVG filename.
            margin: Margin around the exported content.
        """
        # Create SVG Document 
        doc = canvasvg.SVGdocument()
        doc.documentElement.setAttribute(
            "xmlns:xlink", "http://www.w3.org/1999/xlink")

        # Append all elements of the canvas
        for element in canvasvg.convert(doc, self):
            doc.documentElement.appendChild(element)

        # Append images of the model shapes
        for shape in self.shapes.values():
            # Get bbox of image
            x1, y1, x2, y2 = self.bbox(shape.image)
            
            # Compute deltas
            dx = x2-x1
            dy = y2-y1

            # Append XML DOM object
            element = doc.createElement("image")
            element.setAttribute("x", "%0.3f" % x1)
            element.setAttribute("y", "%0.3f" % y1)
            element.setAttribute("width", "%0.3f" % dx)
            element.setAttribute("height", "%0.3f" % dy)
            element.setAttribute("xlink:href", ".{}/model.svg".format(shape.repo_path))
            doc.documentElement.appendChild(element)

        # Get bbox of all shapes and add margin
        x1, y1, x2, y2 = self.bbox(tk.ALL)
        x1 -= margin
        y1 -= margin
        x2 += margin
        y2 += margin

        # Compute deltas
        dx = x2-x1
        dy = y2-y1

        # Set socument attributes
        doc.documentElement.setAttribute('width',  "%0.3f" % dx)
        doc.documentElement.setAttribute('height', "%0.3f" % dy)
        doc.documentElement.setAttribute(
            "viewBox", "%0.3f %0.3f %0.3f %0.3f" % (x1, y1, dx, dy))

        # Write xml to file
        file = open(filename, "w")
        file.write(doc.toxml())
        file.close()

    def create_context_menus(self):
        """Build the right-click context menu for sheet actions."""
        self.context_menu = ttk.Menu(self, tearoff = 0) 
 
        # Create menu items list
        menu_items = [
                ("Undo", "Undo previous action", "Ctrl+Z", self.on_undo, "command"),
                ("Redo", "Redo last action", "Ctrl+Y", self.on_redo, "command"),
                "---",
                ("Cut", "Cut selected objects", "Ctrl+X", self.on_cut, "command"),
                ("Copy", "Copy selected objects to clipboard", "Ctrl+C", self.on_copy, "command"),
                ("Paste", "Paste objecs from clipboard", "Ctrl+V", self.on_paste, "command"),
                "---",
                ("Duplicate", "Duplicate selected objects", None, self.duplicate_selected, "command"),
                ("Delete", "Delete selected objects", None, self.delete_selected, "command"),
                "---",
                #("SwitchPorts", "Switch ports", None,self.switch_ports, "command"),
                ("ShowDoc", "Show documentation", None, self.show_documentation, "command"),
                ("ShowSource", "Show source", None, self.show_source, "command"),
                ("ShowValues", "Show values", None, self.show_values, "command")
        ]
        
        # Iterate through the items for the menu
        self.menu_vars = {}
        for entry in menu_items:
            if entry == "---":
                # Create separator
                self.context_menu.add_separator()
            else: 
                image, label, acc, callback, type = entry
                if type == "command":
                    # Create command
                    self.context_menu.add_command(
                        label=label, underline=0, 
                        accelerator=acc,
                        image=Images().ribbon[image], 
                        compound=tk.LEFT, 
                        command=callback)
                if type =="checkbutton":
                    # Create check button
                    self.menu_vars[label] = ttk.BooleanVar(value=tk.TRUE)
                    self.context_menu.add_checkbutton(
                        label=label, 
                        accelerator=acc,
                        image=Images().ribbon[image], 
                        compound=tk.LEFT, 
                        command=callback,
                        variable = self.menu_vars[label])        

    def on_undo(self):
        """Handle the undo action."""
        pass

    def on_redo(self):
        """Handle the redo action."""
        pass

    def on_cut(self, event=None):
        """Handle cut keybinding or menu action."""
        self.cut_seleced()

    def on_copy(self, event=None):
        """Handle copy keybinding or menu action."""
        self.copy_seleced()

    def on_paste(self, event=None):
        """Handle paste keybinding or menu action."""
        if self.can_paste():
            self.paste_clipboard()

    def on_select_all(self, event=None):
        """Select all shapes on the sheet."""
        self.add_selected_shapes(list(self.shapes.keys()))

    def set_repo_item(self, repo_item):
        """Set the currently selected repository item for shape creation."""
        self.repo_item = repo_item
        
        # Delete current connector if it exists
        if self.current_connector:
            self.delete(self.current_connector.tag)
            self.current_connector = None

        if repo_item:
            # Show and adjust the new shape rect 
            # and label if repo_item is not none
            num_y_ports = len(repo_item.model_dict["y"])
            num_u_ports = len(repo_item.model_dict["u"])
            height = max(
                self.zoom_factor*Shape.SIZE, 
                max(num_y_ports, num_u_ports)*self.zoom_factor*Shape.PORT_DISTANCE)
            width = self.zoom_factor * Shape.SIZE

            self.itemconfig("new_shape_rect", state=tk.NORMAL)
            self.itemconfig("new_shape_label", state=tk.NORMAL)
            self.tag_raise("new_shape_rect")
            self.tag_raise("new_shape_label")
            self.coords("new_shape_rect", -width, -height, 0, 0)
            self.coords("new_shape_label", -width/2, -height+2.5*Shape.PORT_SIZE*self.zoom_factor)
            self.itemconfig("new_shape_label", text=repo_item.model_dict["name"])
            
            # Set mode to MODULE
            self.set_mode(self.MODULE)
        else:
            # Hide the new shape rect and label
            self.itemconfig("new_shape_rect", state = tk.HIDDEN)
            self.itemconfig("new_shape_label", state = tk.HIDDEN)
            
            # Set mode to SELECT
            self.set_mode(self.SELECT)

    def switch_ports(self):
        """Switch the selected shape ports from left to right."""
        # Switch the port from left to right asnd vice versa
        # BE CAREFUl -> currently not saved in pproject
        if self.focused and self.focused in self.shapes:
            shape_id = self.focused
            self.shapes[shape_id].switch_ports()
            self.update_focus()
            self.update_connectors(shape_id)
        
    def show_documentation(self, event=None):
        """Open the selected shape's documentation notebook if available."""
        if self.focused and self.focused in self.shapes:
            # Open the jupyter notebook for 
            # the selected shape if it exists
            shape_id = self.focused
            ipynb = self.shapes[shape_id].repo_path+"/model.ipynb"
            if os.path.exists(ipynb):
                file_out=converter.translate(ipynb)
                os.startfile(file_out)
            else:
                messagebox.showinfo(
                    "Documentation not found", 
                    "The documentation for this model is not available.")

    def show_source(self, event=None):
        """Display the selected shape's source representation."""
        if self.focused and self.focused in self.shapes:
            # Show the json representation for the selected shape
            shape_id = self.focused
            shape = self.shapes[shape_id]
            
            # Create json
            content = {
                "class": shape.class_name,
                "model": shape.model.__dict__,
                "coords": [shape.x, shape.y],
                "path" : shape.repo_path
            }
            json_str = json.dumps(content, indent=4)

            # Show code editor with json
            dlg = CodeEditorDialog(
                self, 
                title="Model inspector", 
                code=json_str,
                lang="json", 
                readonly=True)
            dlg.show()
 
    def show_values(self, event=None):
        """Display the selected shape's values."""
        if self.focused and self.focused in self.shapes:
            # Show the json representation for the selected shape
            shape_id = self.focused
            shape = self.shapes[shape_id]
            
            if shape_id in self.project.result:
                # Get the model data
                model_data = self.project.result[shape_id]

                # Get time frame an values
                header =["t"]
                values = [model_data["t"]]
                for var_id in model_data["vars"]:
                    header.append(var_id) 
                    values.append(model_data["vars"][var_id]["value"])

                # Show code editor with json
                dlg = TableEditorDialog(self, 
                    title = f"Values of model '{shape.model.name}' ({shape_id})", 
                    table_header=header,
                    table_data=list(zip(*values)),
                    readonly=True)
                dlg.show()
            else: 
                messagebox.showinfo(title="Show values", message=f"No data available for model '{shape.model.name}' ({shape_id}).")

    # context menu on right button click 
    def show_context_menu(self, x, y): 
        """Show the context menu at the specified screen coordinates."""
        try: 
            # Enable or disable Undo/Redo
            self.context_menu.entryconfig("Undo previous action", state=tk.DISABLED)
            self.context_menu.entryconfig("Redo last action", state=tk.DISABLED)

            # Enable or disable Shape operations
            entry_state = tk.NORMAL if len(self.selected_shapes)>0 else tk.DISABLED

            self.context_menu.entryconfig("Cut selected objects", state=entry_state)
            self.context_menu.entryconfig("Copy selected objects to clipboard", state=entry_state)
            self.context_menu.entryconfig("Duplicate selected objects", state=entry_state)
            self.context_menu.entryconfig("Show documentation", state=entry_state)
            self.context_menu.entryconfig("Show source", state=entry_state)
            self.context_menu.entryconfig("Show source", state=entry_state)

            # Enable or disable delete operation
            entry_state = tk.NORMAL if len(self.selected_shapes)>0 or self.selected_connector is not None else tk.DISABLED 
            self.context_menu.entryconfig("Delete selected objects", state=entry_state)

            # Enable or disable Paste operation
            entry_state = tk.NORMAL if self.can_paste() else tk.DISABLED
            self.context_menu.entryconfig("Paste objecs from clipboard", state=entry_state)
            
            # Show context menu
            self.context_menu.tk_popup(x, y)
        finally: 
            # Release menu
            self.context_menu.grab_release()                

    def toggle_grid(self):
        """Toggle sheet grid visibility."""
        if self.grid_visible:
            self.hide_grid()
        else:
            self.show_grid()

    def toggle_snap_to_grid(self):
        """Toggle snap-to-grid behavior."""
        self.snap_to_grid = not self.snap_to_grid
        self.event_generate("<<SnapChanged>>")

    def hide_grid(self):
        """Hide the grid lines on the sheet."""
        if self.grid_visible:
            self.grid_visible = False
            self.itemconfig("grid", state=tk.HIDDEN)
            self.event_generate("<<GridChanged>>")      

    def show_grid(self):
        """Show the grid lines on the sheet."""
        if not self.grid_visible:
            self.grid_visible = True
            self.itemconfig("grid", state=tk.NORMAL)
            self.event_generate("<<GridChanged>>")      

    def create_grid(self):
        """Create or refresh the sheet grid lines."""
        self.delete("grid")
        grid_color = self.COLORS["grid"]

        # Add the minor grid light colour lines
        for x in range(self.grid_step, self.sheet_width, self.grid_step):
            if x/self.grid_step % 10 != 0:
                self.create_line(x*self.zoom_factor, 0, 
                                 x*self.zoom_factor, self.sheet_height*self.zoom_factor, 
                                 width=1, fill=self.COLORS["grid"][0], tags=["grid", "minor"])
        
        for y in range(self.grid_step, self.sheet_height, self.grid_step):
            if y/self.grid_step % 10 != 0:
                self.create_line(0, y*self.zoom_factor, 
                                 self.sheet_width*self.zoom_factor, y*self.zoom_factor,
                                 width=1, fill=grid_color[0], tags=["grid", "minor"])

        # Add the major grid dark colour lines
        major_grid_step = 10 * self.grid_step
        for x in range(major_grid_step, self.sheet_width, major_grid_step):
            self.create_line(x*self.zoom_factor, 0, 
                             x*self.zoom_factor, self.sheet_height*self.zoom_factor,
                             width=1, fill=grid_color[1], tags=["grid", "major"])
            
        for y in range(major_grid_step, self.sheet_height, major_grid_step):
            self.create_line(0, y*self.zoom_factor, 
                             self.sheet_width*self.zoom_factor, y*self.zoom_factor,
                             width=1, fill=grid_color[1], tags=["grid", "major"])

        # Add the border grid dark colour lines
        self.create_rectangle(-1, -1, 
                              (self.sheet_width+1)*self.zoom_factor, 
                              (self.sheet_height+1)*self.zoom_factor,
                              width=1, outline=grid_color[2], tags=["grid", "border"])          
        
        # Lower the grid lines behind the shapes and connectors
        self.tag_lower("grid")

    def get_current_tags(self):
        """Return the current canvas tags under the mouse cursor."""
        tags = list(self.gettags(tk.CURRENT))

        # remove grid tag and current tag
        if tk.CURRENT in tags:
            tags.remove(tk.CURRENT)

        if len(tags) == 0:
            return [None]
        else:
            return tags
    
    def on_ctrl_mouse_wheel(self, event):
        """Handle Ctrl+mouse wheel zooming."""
        if event.num == 5 or event.delta == -120:
            self.zoom_out()
        if event.num == 4 or event.delta == 120:
            self.zoom_in()
    
    def on_mouse_wheel(self, event):
        """Scroll the sheet vertically with the mouse wheel."""
        self.yview("scroll", -1*int(event.delta/120), "units")

    def on_motion(self, event):
        """Handle mouse movement over the sheet and update drag operations."""
        x = self.canvasx(event.x)
        y = self.canvasy(event.y)
        dx = x - self.x
        dy = y - self.y 

        # case 0: MODULE mode and a valid model 
        # -> position new_shape_rect
        if self.mode == self.MODULE and self.repo_item:
            if self.snap_to_grid:
                grid_step = self.grid_step * self.zoom_factor
                pos_x = round(x/grid_step) * grid_step
                pos_y = round(y/grid_step) * grid_step
            else:
                pos_x = x
                pos_y = y

            coords = self.coords("new_shape_rect")
            self.coords(
                "new_shape_rect", pos_x, pos_y, 
                pos_x + coords[2]-coords[0],
                pos_y + coords[3]-coords[1])
            shape_width=coords[2]-coords[0]
            coords = self.coords("new_shape_label")
            self.coords(
                "new_shape_label", 
                pos_x+shape_width/2, 
                pos_y+2.5*Shape.PORT_SIZE*self.zoom_factor)

        # case 1: CONNECT mode and we have a current connector
        # -> update connector
        elif self.current_connector is not None:
            if self.hovered_port is not None:
                if self.is_connector_valid(self.current_connector.src_port, self.hovered_port):
                    self.current_connector.set_dest_port(self.hovered_port)
                else:
                    self.current_connector.set_dest_coord(x, y)
            else:
                self.current_connector.set_dest_coord(x, y)

        # case 2: PAN mode and mouse button pressed 
        # -> panning
        elif self.mode == self.PAN and event.state & 0x0001 and event.state & 0x0100:
            # Pan the sheet
            self.scan_dragto(event.x, event.y, gain=1)
            self.event_generate("<<ScanDragTo>>", x=event.x, y=event.y)

        # case 3: RUBBERBAND mode and mouse button pressed 
        # -> show rubberband selection
        elif self.mode == self.RUBBERBAND and event.state & 0x0100:
            # Show rubberband if left mouse button is pressed  
            # and current item is not in the selection list
            left = min(self.drag_start[0], x)
            top =  min(self.drag_start[1], y)
            right = max(self.drag_start[0], x)
            bottom = max(self.drag_start[1], y)

            self.coords("select_rect", left, top, right, bottom)
            self.itemconfig("select_rect", state = tk.NORMAL)
            self.tag_raise("select_rect")

        # case 4: MOVE mode and mouse button pressed 
        # -> move selection
        elif self.mode == self.MOVE and event.state & 0x0100:
            if len(self.selected_shapes) > 0:
                # Drag and drop if left mouse button is pressed  
                # and the current item is in the selection list
                if self.snap_to_grid:
                    # accumulate the deltas when in snap to grid mode
                    grid_step = self.grid_step * self.zoom_factor
                    self.dx += dx
                    self.dy += dy

                    if abs(self.dx) >= grid_step:
                        # Compute dx and reset accumulated value 
                        # when moved more than gridstep
                        dx = round(self.dx/grid_step)*grid_step
                        self.dx = 0
                    else:
                        dx = 0
                    if abs(self.dy) >= grid_step:
                        # Compute dy and reset accumulated value 
                        # when moved more than gridstep
                        dy = round(self.dy/grid_step)*grid_step
                        self.dy = 0
                    else:
                        dy = 0
                
                # Move the shapes and update the connectors
                for key in self.selected_shapes:
                    item = self.shapes[key]
                    item.move(dx, dy)
                    self.update_connectors(key)
                
                # Move focus rect
                if self.focused:
                    self.move("focus_rect", dx, dy)

        # Store mouse coordinates
        self.x = x
        self.y = y

    def on_right_up(self, event):        
        """Handle right mouse button release and show the context menu."""
        if self.mode == self.MODULE:
            self.set_repo_item(None)
            # Set select mode
            self.set_mode(self.SELECT)

        elif self.current_connector:
            self.delete(self.current_connector.tag)
            self.current_connector = None
            # Set select mode
            self.set_mode(self.SELECT)

        else:
            # Update selection and focus frame
            tags = self.get_current_tags()
            shape_id = tags[0]
            if shape_id in self.shapes:
                if shape_id not in self.selected_shapes:
                    self.set_selected_shapes([shape_id])
                self.set_focus(shape_id)

            # Show context menu
            self.show_context_menu(event.x_root, event.y_root)

    def on_left_down(self, event):
        """Handle left mouse button press for selection, placement, and dragging."""
        x = self.canvasx(event.x)
        y = self.canvasy(event.y)
        self.dx = 0
        self.dy = 0
        self.drag_start = (x, y)
        self.lb_state = 1

        tags = self.get_current_tags()

        # case 0: click while mode is MODULE and 
        # we have a valid model to add -> add shape
        if self.mode == self.MODULE and self.repo_item:
            if self.snap_to_grid:
                grid_step = self.grid_step*self.zoom_factor
                pos_x = round(x/grid_step) * grid_step
                pos_y = round(y/grid_step) * grid_step
            else:
                pos_x = x
                pos_y = y

            self.clear_seleced_shapes()
            self.set_selected_connector(None)
         
            shape = Shape(self, pos_x, pos_y, self.repo_item.path, self.zoom_factor)
            shape.set_model(Model.from_data(copy.deepcopy(self.repo_item.model_dict)))
        
            self.add_shape(shape)
            self.add_selected_shapes([shape.tag])
            self.set_focus(shape.tag)
            self.set_repo_item(None)
        
        # case 1: Connector mode
        elif self.mode == self.CONNECT and self.current_connector is not None:
            if self.hovered_port is not None:
                if self.is_connector_valid(self.current_connector.src_port, self.hovered_port):
                    self.current_connector.set_dest_port(self.hovered_port)
                    self.add_connector(self.current_connector)
                    self.current_connector.create_var_map()
                    self.set_selected_connector(self.current_connector.tag)
                    self.set_focus(self.current_connector.tag)
                    self.current_connector = None
                    self.set_mode(self.SELECT)

        # case 2: click on a model port -> start connector
        elif self.hovered_port is not None:
            if self.current_connector is None: 
                if self.is_connector_valid(self.hovered_port, None):
                    self.current_connector = Connector(self, self.hovered_port, None, self.zoom_factor)
                    self.set_mode(self.CONNECT)

        # case 3: click on the sheet or the grid 
        # and shift is pressed -> start panning
        elif (tags[0] is None or tags[0] == "grid") and event.state & 0x0001:
            # Set Pan mode
            self.set_mode(self.PAN)
            self.scan_mark(event.x, event.y)
            self.event_generate("<<ScanMark>>", x=event.x, y=event.y)

        # case 4: click on the sheet or the grid 
        # and no modifier button is pressed -> start rubberband
        elif tags[0] is None or tags[0] == "grid":
            # Clear selection if ctrl is not pressed 
            if not event.state & 0x0004:
                self.clear_seleced_shapes()
                self.set_selected_connector(None)
            
            # Set focus to project
            self.set_focus(self.project)

            # Set rubberband mode
            self.set_mode(self.RUBBERBAND)

        # case 5: we have clicked on a shape 
        # and the shape is selected already -> move the shape
        elif tags[0] in self.selected_shapes:
            # Get the shape id
            shape_id = tags[0]

            if event.state & 0x0004:
                self.remove_selected_shapes([shape_id])
                # Set select mode
                self.set_mode(self.SELECT)
            else:
                # Set move mode
                self.set_mode(self.MOVE)
            self.set_focus(shape_id)

        # case 6: we have clicked on a shape -> change selection
        elif tags[0] in self.shapes:
            # Set select mode
            self.set_mode(self.SELECT)

            # Reset selected connector
            self.set_selected_connector(None)

            # Get the shape id
            shape_id = tags[0]
            self.set_focus(shape_id)

            # Add current to selection if ctrl is pressed 
            # otherwise set selcetion to current
            if event.state & 0x0004:
                if self.shapes[shape_id].selected:
                    self.remove_selected_shapes([shape_id])
                else:
                    self.add_selected_shapes([shape_id])
            else:
                self.set_selected_shapes([shape_id])

        # case 6: we have clicked on a connector -> select the connector
        elif tags[0] in self.connectors:
            # Clear the selection
            self.clear_seleced_shapes()
            
            # Focus the selected connector
            connector_id = tags[0]
            self.set_focus(connector_id)

            # Set connector selection
            self.set_selected_connector(connector_id)

        # Store mouse coordinates
        self.x = x
        self.y = y

    def on_left_up(self, event):
        """Handle left mouse button release to complete interactions."""

        self.lb_state = 0
        self.focus_set()
        if self.mode == self.RUBBERBAND:
            # In rubberband mode select the shapes inside bbox
            rect = self.coords("select_rect")
            for key in self.shapes:
                bbox = self.bbox(key)
                if bbox[0]>rect[0] and bbox[1]>rect[1] and bbox[2]<rect[2] and bbox[3]<rect[3]:
                    self.add_selected_shapes([key])
            if len(self.selected_shapes) > 0 and self.focused not in self.selected_shapes:
                self.set_focus(self.selected_shapes[-1])

            self.coords("select_rect", 0, 0, 0, 0)
            self.itemconfig("select_rect", state = tk.HIDDEN)

            # Set select mode
            self.set_mode(self.SELECT)

        elif self.mode == self.MOVE:
            # Set select mode
            self.set_mode(self.SELECT)

        elif self.mode == self.PAN:
            # Set select mode
            self.set_mode(self.SELECT)

    def on_key_del(self, event):
        """Delete the currently selected shapes or connector."""
        self.delete_selected()

    def on_key_up(self, event):
        """Move the selected shape(s) upward using keyboard navigation."""
        dx = 0
        dy = -self.grid_step if self.snap_to_grid else -1

        for key in self.selected_shapes:
            item = self.shapes[key]
            item.move(dx, dy)
            self.update_connectors(key)

        # Move focus rect
        if self.focused:
            self.move("focus_rect", dx, dy)
 
    def on_key_down(self, event):
        """Move the selected shape(s) downward using keyboard navigation."""
        dx = 0
        dy = self.grid_step if self.snap_to_grid else 1

        for key in self.selected_shapes:
            item = self.shapes[key]
            item.move(dx, dy)
            self.update_connectors(key)

        # Move focus rect
        if self.focused:
            self.move("focus_rect", dx, dy)
                 
    def on_key_left(self, event):
        """Move the selected shape(s) left using keyboard navigation."""
        dx = -self.grid_step if self.snap_to_grid else -1
        dy = 0

        for key in self.selected_shapes:
            item = self.shapes[key]
            item.move(dx, dy)
            self.update_connectors(key)

        # Move focus rect
        if self.focused:
            self.move("focus_rect", dx, dy)

    def on_key_right(self, event):
        """Move the selected shape(s) right using keyboard navigation."""
        dx = self.grid_step if self.snap_to_grid else 1
        dy = 0

        for key in self.selected_shapes:
            item = self.shapes[key]
            item.move(dx, dy)
            self.update_connectors(key)

        # Move focus rect
        if self.focused:
            self.move("focus_rect", dx, dy)

    def on_shape_enter(self, event):
        """Handle mouse entering a shape area."""
        item = self.find_withtag(tk.CURRENT)
        tags = self.gettags(item)
        # Only handle hover if left button is not pressed
        if self.lb_state == 0:  
            # Call handle_shape_enter 
            self.after(0, self.handle_shape_enter, tags)
    
    def handle_shape_enter(self, tags):
        """Update internal hover state when the mouse enters a shape."""
        shape_id = tags[0]
        self.hovered_shape = shape_id

        # Shape hover only if we are in SELECT mode
        if self.mode == self.SELECT:
            # Switch frame width
            shape = self.shapes[shape_id]
            self.itemconfig(shape.frame, width=Shape.WIDTH+1)
 
    def on_shape_leave(self, event):
        """Handle mouse leaving a shape area."""
        self.after(0, self.handle_shape_leave)

    def handle_shape_leave(self):
        """Reset hovered shape state after the mouse leaves."""
        if self.hovered_shape in self.shapes:
            shape = self.shapes[self.hovered_shape]
            self.hovered_shape = None
            # Switch frame width
            self.itemconfig(shape.frame, width=Shape.WIDTH)
 
    def on_connector_enter(self, event):
        """Handle mouse entering a connector area."""
        item = self.find_withtag(tk.CURRENT)
        tags = self.gettags(item)
        # Call handle_connector_enter 
        self.after(0, self.handle_connector_enter, tags)
    
    def handle_connector_enter(self, tags):
        """Update internal hover state when the mouse enters a connector."""
        connector_id = tags[0]
        self.hovered_connector = connector_id

        # Connector hover only if we are in SELECT mode
        if self.mode == self.SELECT:
            connector = self.connectors[connector_id]
            # Switch line width
            self.itemconfig(connector.line, width=Connector.WIDTH+1)
 
    def on_connector_leave(self, event):
        """Handle mouse leaving a connector area."""
        self.after(0, self.handle_connector_leave)

    def handle_connector_leave(self):
        """Reset hovered connector state after the mouse leaves."""
        if self.hovered_connector in self.connectors:
            connector = self.connectors[self.hovered_connector]
            self.hovered_connector = None
            # Switch line width
            self.itemconfig(connector.line, width=Connector.WIDTH)

    def is_connector_valid(self, src_port, dest_port):
        """Return whether a connector can be created between two ports."""
        src_shape_id = src_port[0]
        src_port_type = src_port[1]
        src_port_id = src_port[2]

        # Return False if the port is already connected
        for connector in self.get_connectors(src_shape_id):
            if connector.src_port[0] == src_shape_id and \
               connector.src_port[2] == src_port_id:
                return False

        # Src port must be of type "out"
        if src_port_type != "out":
            return False

        if dest_port:
            dest_shape_id = dest_port[0]
            dest_port_type = dest_port[1]
            dest_port_id = dest_port[2]

            # Return False if the port is already connected
            for connector in self.get_connectors(dest_shape_id):
                if connector.dest_port[0] == dest_shape_id and \
                connector.dest_port[2] == dest_port_id:
                    return False

            # Dest port must be of type "out" and 
            # current_connector must be None 
            if dest_port_type != "in":
                return False
        
        # If everything is ok return True       
        return True

    def on_port_enter(self, event):
        """Handle mouse entering a port and update cursor/tooltip state."""
        item = self.find_withtag(tk.CURRENT)
        tags = self.gettags(item)
        # Call handle_port_enter 
        self.after(0, self.handle_port_enter, item, tags, event)
    
    def handle_port_enter(self, item, tags, event):
        """Show port hover feedback and tooltip for valid port interactions."""
        shape_id = tags[0]
        port_type = tags[1]
        port_id = tags[2]

        # Ignore port hover, if we are in MODULE mode
        if self.mode == self.MODULE:
            pass
        
        # In all other cases
        else:
            # Get source and dest port
            if self.current_connector:
                src_port = self.current_connector.src_port
                dest_port = tags
            else:
                src_port = tags
                dest_port = None

            # Check if connector is valid and show appropriate cursors
            if self.is_connector_valid(src_port, dest_port):
                self.config(cursor=self.CURSORS[self.VALID])
            else:
                self.config(cursor=self.CURSORS[self.INVALID])

            # show tooltip only if we haven't pressed the
            # left mouse button and we are on a valid port
            shape = self.shapes[shape_id]
            port = None
            if port_type == "in":
                caption = "Input {}".format(port_id)
                port = shape.model.u[port_id]
                self.itemconfig(shape.ports_in[port_id], width=2)
            else:
                caption = "Output {}".format(port_id)
                port = shape.model.y[port_id]
                self.itemconfig(shape.ports_out[port_id], width=2)

            if port and not event.state & 0x0100:
                text = "{}\nType: {}\nVars: {}".format(
                    port["description"],
                    port["type"],
                    port["vars"])

                coords = self.coords(item)
                x = self.winfo_rootx() + coords[0] + 15*self.zoom_factor - self.canvasx(0)
                y = self.winfo_rooty() + coords[1] + 15*self.zoom_factor - self.canvasy(0)
                self.show_tooltip(x, y, caption, text)

            self.hovered_port = (shape_id, port_type, port_id)
    
    def on_port_leave(self, event):
        """Handle mouse leaving a port area."""
        self.after(0, self.handle_port_leave)

    def handle_port_leave(self):
        """Reset port hover state and restore cursor and tooltip."""
        if self.hovered_port:
            shape_id, port_type, port_id = self.hovered_port
            shape = self.shapes[shape_id]
            if port_type == "in":
                self.itemconfig(shape.ports_in[port_id], width=1)
            else:
                self.itemconfig(shape.ports_out[port_id], width=1)

            # Reset hovered port
            self.hovered_port = None

            # Hide the tooltip
            self.hide_tooltip()

            # Reset the cursor
            if not self.current_connector:
                self.config(cursor=self.CURSORS[self.SELECT])
            else:
                self.config(cursor=self.CURSORS[self.CONNECT])
             
    def show_tooltip(self, x, y, caption, text):
        """Show a tooltip window near the mouse cursor."""
        self.toplevel = Toplevel(self)
        # Leave only the label and removes the app window
        self.toplevel.wm_overrideredirect(True)

        # Create and pack tooltip frame
        container = ttk.Frame(self.toplevel, bootstyle=tk.DARK)
        container.pack(fill = tk.BOTH)

        # Create and pack caption
        label = ttk.Label(           
            container, 
            text=caption,
            font = ("TkDefaultFont", 8, "bold"),
            justify=tk.LEFT, 
            wraplength=250,
            padding = (5, 3))
        label.pack(side = tk.TOP, fill = tk.X, padx=(1,1), pady=(1,0))

        # Create and pack hint
        label = ttk.Label(           
            container, 
            text=text,
            justify=tk.LEFT, 
            wraplength=250,
            padding = (5, 3))
        label.pack(fill = tk.BOTH, padx=1, pady=1) 

        # Set geometry
        self.toplevel.wm_geometry("+%d+%d" % (x, y))

    def hide_tooltip(self):
        """Hide any visible tooltip window."""
        if self.toplevel:
            self.toplevel.destroy()
        self.toplevel = None

    def get_connectors(self, shape_id, type="both"):
        """Return connectors related to a shape.

        Args:
            shape_id: Identifier of the shape.
            type: 'in', 'out', or 'both'.

        Returns:
            List of connector objects.
        """
        result = []
        for key in self.connectors:
            connector = self.connectors[key]
            src_shape = connector.src_port[0]
            dest_shape = connector.dest_port[0]
            if type=="out" and src_shape == shape_id:
                result.append(connector)
            elif type=="in" and dest_shape == shape_id:
                result.append(connector)    
            elif type=="both" and (src_shape == shape_id or dest_shape == shape_id):
                result.append(connector)
        return result

    def add_connector(self, connector):
        """Register a connector and emit a ConnectorAdded event."""
        self.connectors[connector.tag] = connector
        # Generate <<ConnectorAdded>> event
        self.event_generate("<<ConnectorAdded>>")

    def delete_connector(self, tag):
        """Delete a connector by tag and update dependent shapes."""
        con = self.connectors.pop(tag)
        src = con.src_port[0]
        dest = con.dest_port[0]

        # Update all other connectors of the src 
        # and dest shape of the connector to delete
        self.update_connectors(src)
        self.update_connectors(dest)

        # Delete connector from sheet
        self.delete(tag)
        # Generate <<ConnectorDeleted>> event
        self.event_generate("<<ConnectorDeleted>>")      

    def update_connectors(self, shape_id):
        """Refresh all connectors attached to a shape."""
        for connector in self.get_connectors(shape_id):
            if connector.src_port[0] in self.shapes and \
               connector.dest_port[0] in self.shapes:
                # Update the connector
                connector.update()

    def add_shape(self, shape):        
        """Add a shape to the sheet and emit a ShapeAdded event."""
        self.shapes[shape.tag] = shape
        self.order.append(shape.tag)
        # Generate <<ShapeAdded>> event
        self.event_generate("<<ShapeAdded>>")

    def delete_shape(self, tag):
        """Delete a shape by tag and remove its associated connectors."""
        if tag == self.focused:
            # Rest focus
            self.set_focus(None)

        self.shapes.pop(tag)
        self.order.pop(self.order.index(tag))

        # Delete shape from sheet
        self.delete(tag)
        self.event_generate("<<ShapeDeleted>>")      
        
        # Delete all connector of the shape to delete
        for connector in self.get_connectors(tag):
            self.delete_connector(connector.tag)

    def set_focus(self, tag):
        """Set focus to a shape, connector, or None and emit change events."""
        if self.focused != tag:
            # Generate a <<LostFocus>> message to give parent
            # the chance to react (update proeprties for example) 
            if self.focused:
                self.event_generate("<<LostFocus>>")
            
            # Set the new tag an generate the <<FocusChanged>> message
            self.focused = tag
            self.event_generate("<<FocusChanged>>")
            self.update_focus()

    def update_focus(self):
        """Update focus highlight for the current focused item."""
        
        if self.focused in self.shapes:
            # Hide focus line
            self.itemconfig("focus_line", state = tk.HIDDEN)

            # Get bounding box of the frame of the focused shape
            # left, top, right, bottom = self.bbox(self.focused)
            focus_shape = self.shapes[self.focused]
            left, top, right, bottom = self.bbox(focus_shape.frame)

            # Set the coords of the focus rect
            self.coords(self.focus_rect, left-1, top-1, right+1, bottom+1)

            # Show the focus rect and bring it behind the focused shape
            self.itemconfig("focus_rect", state = tk.NORMAL, width=2)
            self.tag_lower("focus_rect", focus_shape.frame)
            
 
        elif self.focused in self.connectors:
            # Hide focus rect
            self.itemconfig("focus_rect", state = tk.HIDDEN)
            connector = self.connectors[self.focused]
            line_coords = self.coords(connector.line)

            # Set the coords of the focus line
            self.coords(self.focus_line, line_coords)

            # Show the focus line and bring it to top
            self.itemconfig("focus_line", state = tk.NORMAL)
            self.tag_raise("focus_line")
    
        else:
            # Hide focus rect and focus line
            self.itemconfig("focus_rect", state = tk.HIDDEN)
            self.itemconfig("focus_line", state = tk.HIDDEN)      
        
    def set_selected_connector(self, tag):
        """Set the currently selected connector and update selection state."""
        # If connector is different from tag
        if self.selected_connector:
            # Unselect the previous selected connector
            connector = self.connectors[self.selected_connector]
            connector.unselect()
        
        # Set selected connector to tag
        self.selected_connector = tag

        # If tag is not None
        if self.selected_connector:
            # Clear selected shapes
            self.clear_seleced_shapes()
            # Select the connector
            connector = self.connectors[self.selected_connector]
            connector.select()
        # Generate <<SelectionChanged>> event
        self.event_generate("<<SelectionChanged>>")      

    def set_selected_shapes(self, tags):
        """Select a list of shapes and update selection state."""
        self.clear_seleced_shapes()
        # Add selected shapes
        self.add_selected_shapes(tags)
        # Generate <<SelectionChanged>> event
        self.event_generate("<<SelectionChanged>>")      

    def add_selected_shapes(self, tags):
        """Add shapes to the current selection."""
        self.set_selected_connector(None)
        for key in tags:
            item = self.shapes[key]
            item.select()
        self.selected_shapes = list(set().union(self.selected_shapes, tags))
        # Generate <<SelectionChanged>> event
        self.event_generate("<<SelectionChanged>>")

    def remove_selected_shapes(self, tags):
        """Remove shapes from the current selection."""
        for key in tags:
            self.shapes[key].unselect()
            self.selected_shapes.remove(key)
        # Generate <<SelectionChanged>> event
        self.event_generate("<<SelectionChanged>>")      

    def clear_seleced_shapes(self):
        """Clear the current shape selection."""
        for key in self.selected_shapes:
            self.shapes[key].unselect()
        self.selected_shapes = []
        # Generate <<SelectionChanged>> event
        self.event_generate("<<SelectionChanged>>")      

    def get_zoom_factor(self):
        """Return the current zoom factor."""
        return self.zoom_factor

    def set_zoom_factor(self, value):
        """Set the zoom factor and rescale sheet elements."""
        zoom_factor=max(min(self.zoom_factor_max, value), self.zoom_factor_min)
        # Compute scale factor
        factor = zoom_factor/self.zoom_factor
        # Scale canvas elements
        self.scale(tk.ALL, 0, 0, factor, factor)

        # Scale text
        for child_widget in self.find_withtag("text"):
            font = (Shape.FONT[0], int(Shape.FONT[1] * zoom_factor))
            self.itemconfigure(child_widget, font=font)

        # Scale images
        for shape in self.shapes.values():
            if shape.model_icon:
                shape.model_icon.configure(scale=1.0)
                svg_scale = zoom_factor * Shape.ICON_SIZE / float(max(shape.model_icon.width(), shape.model_icon.height()))
                shape.model_icon.configure(scale=svg_scale)
                self.itemconfig(shape.image, image=shape.model_icon)

        # Store new scale
        self.zoom_factor = zoom_factor
        # Update focus rect
        self.update_focus()
        # Update scroll region
        self.config(scrollregion=(0, 0, int(self.sheet_width*self.zoom_factor), int(self.sheet_height*self.zoom_factor)))

        # Inform subscribers about zoomchange
        self.event_generate("<<ZoomChanged>>")      

    def zoom_in(self):
        """Zoom in toward the sheet contents."""
        self.set_zoom_factor(self.zoom_factor+self.zoom_step)

    def zoom_100(self):
        """Reset zoom to 100%."""
        self.set_zoom_factor(1.0)

    def zoom_out(self):
        """Zoom out from the sheet contents."""
        self.set_zoom_factor(self.zoom_factor-self.zoom_step)

    def duplicate_selected(self):
        """Duplicate the currently selected shapes."""
        # Make a deep opy of the selected shapes list
        selection = copy.deepcopy(self.selected_shapes)
        # Clear the selection
        self.clear_seleced_shapes()
        # Loop through the selection
        for key in selection:
            # Get the source shape
            source = self.shapes[key]
            # Get the source ccords
            coords = self.coords(source.frame)
            # Add a new shape and move it one 
            # gridstep away form the source
            shape = Shape(
                self, 
                coords[0]+4*self.grid_step*self.zoom_factor, 
                coords[1]+4*self.grid_step*self.zoom_factor, 
                source.repo_path, self.zoom_factor)
            # Make a deep copy of the associated source 
            # model and assign it to the new shape
            shape.set_model(copy.deepcopy(source.model))

            # Add the new shapeto the sheet and to the selection
            self.add_shape(shape)
            self.add_selected_shapes([shape.tag])
            # Focus the new shape
            self.set_focus(shape.tag)

    def delete_selected(self):
        """Delete all currently selected shapes and connectors."""
        for key in self.selected_shapes:
            self.delete_shape(key)
        # Empty the selected shapes list
        self.selected_shapes = []

        # Delete teh selected connector 
        if self.selected_connector:
            self.delete_connector(self.selected_connector)
        # Reste the selected connector
        self.selected_connector = None
        # Reset the focus
        self.set_focus(None)
        
        # Generate a <<SelectionChanged>> event
        self.event_generate("<<SelectionChanged>>") 

    def cut_seleced(self):
        """Cut the selected shapes to the clipboard."""
        self.copy_seleced()
        self.delete_selected()

    def copy_seleced(self):
        """Copy selected shapes to the clipboard."""
        shape_dict = {}
        for shape_id in self.selected_shapes:
            shape = self.shapes[shape_id]
            shape_dict[shape_id] = {
                "class": shape.class_name,
                "model": shape.model.__dict__,
                "coords": [shape.x, shape.y],
                "path" : shape.repo_path
            }
        
        # Prepare the var_map 
        var_map_dict = {}
        for shape_id in self.selected_shapes:
            var_map_dict[shape_id] = {}

        # Copy edges
        edge_list = []
        for connector_id in self.connectors:
            connector = self.connectors[connector_id]
            src_shape_id, _, src_port_id = connector.src_port
            dest_shape_id, _, dest_port_id = connector.dest_port

            if src_shape_id in self.selected_shapes and dest_shape_id in self.selected_shapes:
                edge_list.append([
                    src_shape_id, dest_shape_id, {
                        "ports": [src_port_id, dest_port_id],
                        "tag": connector_id,
                    }
                ])

                var_map_dict[dest_shape_id][dest_port_id] = connector.var_map

        # Clear clipboard and apend shapes and edges
        self.clipboard_clear()
        self.clipboard_append(json.dumps([shape_dict, edge_list, var_map_dict]))
    
    def paste_clipboard(self):
        """Paste shapes from the clipboard into the sheet."""
        try:
            # Deserialize clipboard content
            content = self.clipboard_get()
            shape_dict, edges_list, var_map_dict = json.loads(content)
            
            # Clear the selection
            self.clear_seleced_shapes()
            
            # Dict to store old an new shape id's in a map
            id_map = {}
            
            # Paste shapes
            for shape_id in shape_dict:
                repo_path = shape_dict[shape_id]["path"]
                pos_x, pos_y = shape_dict[shape_id]["coords"]

                # Create shape (with new id)
                shape = Shape(
                    self, int(pos_x+4*self.grid_step*self.zoom_factor), 
                    int(pos_y+4*self.grid_step*self.zoom_factor), 
                    repo_path, self.zoom_factor)
                shape.set_model(Model.from_data(shape_dict[shape_id]["model"]))

                # Add the shape
                self.add_shape(shape)
                self.add_selected_shapes([shape.tag])

                # Store the new id
                id_map[shape_id] = shape.tag

            # Paste edges
            for edge in edges_list:
                # Get id's from the map
                src_shape_id = id_map[edge[0]]
                dest_shape_id = id_map[edge[1]]
                src_port_id, dest_port_id = edge[2]["ports"]

                # Create connector
                connector = Connector(
                    self, 
                    (
                        src_shape_id, 
                        self.shapes[src_shape_id].model.y[src_port_id]["type"], 
                        src_port_id
                    ), 
                    (
                        dest_shape_id, 
                        self.shapes[dest_shape_id].model.u[dest_port_id]["type"], 
                        dest_port_id
                    ), 
                    self.zoom_factor)
                
                # Set var map
                connector.set_var_map(var_map_dict[edge[1]][dest_port_id])

                # Replace source id's of var map
                for var_id in connector.var_map:
                    if type(connector.var_map[var_id]) is list:
                        if connector.var_map[var_id][0] in id_map:
                            connector.var_map[var_id][0] = id_map[connector.var_map[var_id][0]]
                        else:
                            connector.var_map[var_id] = None
                # Add the connector
                self.add_connector(connector)
        except:
            messagebox.showerror(title="ERROR", message="Clipboard does not contain valid shape data.")

    def can_paste(self):
        """Return whether the clipboard contains paste-able shape data."""
        # TODO: make this more stable!
        try:
            content = self.clipboard_get()
            obj = json.loads(content)

            if type(obj) is not list:
                return False
            if len(obj) != 3:
                return False
            if type(obj[0]) is not dict:
                return False
            if type(obj[1]) is not list:
                return False
            if type(obj[2]) is not dict:
                return False
            
            return True
        except:
            return False

    def send_backward(self):
        """Send selected shapes one step backward in the z-order."""
        # Get the indices in the order list for the selected shapes
        selection_order = [self.order.index(key) for key in self.selected_shapes]
        # Sort the index list
        selection_order.sort()
        # Now lower the order of the associated tag in the sheet
        # but only if index is greater than zero
        for index in selection_order:
            if index > 0:
                # Pop the item from the list
                item = self.order.pop(index)
                # Compute new index
                before = self.order[index-1]
                # Update the order list by inderting 
                # the popped item to the new position
                self.order.insert(index-1, item)
                # Lower the item in the sheet
                self.tag_lower(item, before)

        # Generate a <<OrderChanged>> event
        self.event_generate("<<OrderChanged>>")      

    def send_to_back(self):
        """Send selected shapes to the back of the stacking order."""
        for key in self.selected_shapes:
            self.tag_lower(key)
        # Lower the grid
        self.tag_lower("grid")
        # Generate a <<OrderChanged>> event
        self.event_generate("<<OrderChanged>>")      

    def bring_to_front(self):
        """Bring selected shapes to the front of the stacking order."""
        for key in self.selected_shapes:
            self.tag_raise(key)
        # Generate a <<OrderChanged>> event
        self.event_generate("<<OrderChanged>>")      

    def bring_forward(self):
        """Bring selected shapes one step forward in the z-order."""
        # Get the indices in the order list for the selected shapes
        selection_order = [self.order.index(key) for key in self.selected_shapes]
        # Sort and reverse the index list
        selection_order.sort()
        selection_order.reverse()
        # Now raise the order of the associated tag in the sheet
        # but only if index is lower than lenght of order list-1
        for index in selection_order:
            if index < len(self.order)-1:
                # Pop the item from the list
                item = self.order.pop(index)
                # Compute new index
                behind = self.order[index]
                # Update the order list by inderting 
                # the popped item to the new position
                self.order.insert(index+1, item)
                # Raise the item in the sheet
                self.tag_raise(item, behind)
        # Generate a <<OrderChanged>> event
        self.event_generate("<<OrderChanged>>")      

    def align_vertical_left(self):
        """Align selected shapes to the left edge of the focused shape."""
        # and more than one item is selected
        if self.focused is not None and len(self.selected_shapes)>0:
            coords = self.coords(self.shapes[self.focused].frame)
            for key in self.selected_shapes:
                item = self.shapes[key]
                item.set_position(coords[0], item.y)
                self.update_connectors(key)

    def align_vertical_center(self):
        """Align selected shapes vertically centered with the focused shape."""
        # and more than one item is selected
        if self.focused is not None and len(self.selected_shapes)>0:
            coords = self.coords(self.shapes[self.focused].frame)
            center = coords[0] + (coords[2]-coords[0])/2
            for key in self.selected_shapes:
                item = self.shapes[key]
                item_coords = self.coords(self.shapes[key].frame)
                item_width = item_coords[2] - item_coords[0]
                item.set_position(center-item_width/2, item.y)
                self.update_connectors(key)

    def align_vertical_right(self):
        """Align selected shapes to the right edge of the focused shape."""
        # and more than one item is selected
        if self.focused is not None and len(self.selected_shapes)>0:
            coords = self.coords(self.shapes[self.focused].frame)
            for key in self.selected_shapes:
                item = self.shapes[key]
                item_coords = self.coords(self.shapes[key].frame)
                item_width = item_coords[2] - item_coords[0]
                item.set_position(coords[2]-item_width, item.y)
                self.update_connectors(key)

    def align_horizontal_top(self):
        """Align selected shapes to the top edge of the focused shape."""
        # and more than one item is selected
        if self.focused is not None and len(self.selected_shapes)>0:
            coords = self.coords(self.shapes[self.focused].frame)
            for key in self.selected_shapes:
                item = self.shapes[key]
                item.set_position(item.x, coords[1])
                self.update_connectors(key)

    def align_horizontal_center(self):
        """Align selected shapes horizontally centered with the focused shape."""
        # and more than one item is selected
        if self.focused is not None and len(self.selected_shapes)>0:
            coords = self.coords(self.shapes[self.focused].frame)
            center = coords[1] + (coords[3]-coords[1])/2
            for key in self.selected_shapes:
                item = self.shapes[key]
                item_coords = self.coords(self.shapes[key].frame)
                item_height = item_coords[3] - item_coords[1]
                item.set_position(item.x, center-item_height/2)
                self.update_connectors(key)

    def align_horizontal_bottom(self):
        """Align selected shapes to the bottom edge of the focused shape."""
        # and mor than one item is selected
        if self.focused is not None and len(self.selected_shapes)>0:
            coords = self.coords(self.shapes[self.focused].frame)
            for key in self.selected_shapes:
                item = self.shapes[key]
                item_coords = self.coords(self.shapes[key].frame)
                item_height = item_coords[3] - item_coords[1]
                item.set_position(item.x, coords[3]-item_height)

                self.update_connectors(key)

    def fill_propertygrid(self, propertygrid):
        """Populate the sheet property grid with sheet configuration values."""
        propertygrid.add_category("Common")
        propertygrid.add_property(
            "Common", "sheet_width", self.sheet_width,
            "int", "Sheet widh", "Sets the width of the sheet.", 
            options={"min":1000, "max":25000})
        propertygrid.add_property(
            "Common", "sheet_height", self.sheet_height,
            "int", "Sheet height", "Sets the height of the sheet.", 
            options={"min":1000, "max":25000})
        propertygrid.add_property(
            "Common", "grid_step", self.grid_step,
            "spinbox", "Grid step", "Sets the grid step.", 
            options={"from_":5, "to": 250, "values":(5, 10, 20, 25, 50, 100, 200, 250)})
        propertygrid.add_property(
            "Common", "sheet_color", self["bg"], 
            "color", "Sheet color", "Sets the background color of the sheet.")

    def update_value(self, propertygrid):
        """Apply updated property values from the property grid to the sheet."""
        prop = propertygrid.props[propertygrid.value_label]
        
        if prop["property"] == "sheet_width":
            # Update common model properties
            self.sheet_width = int(prop["value"])
        if prop["property"] == "sheet_height":
            # Update common model properties
            self.sheet_height = int(prop["value"])
        if prop["property"] == "grid_step":
            # Update common model properties
            self.grid_step = int(prop["value"])
        if prop["property"] == "sheet_color":
            # Update common model properties
            self.config(bg = str(prop["value"]))

        self.update_dimensions()

    def _on_theme_change(self, *_):
        """Refresh theme-dependent appearance for sheet items."""
        focus_color = Style().colors.primary

        # Set focus color for shapes and connectors
        self.itemconfig("focus_rect", outline=focus_color)
        self.itemconfig("focus_line", fill=focus_color)

        # Update shapes
        for shape in self.shapes.values():
            shape.update_theme()
        # Update connectors
        for connector in self.connectors.values():
            connector.update_theme()

if __name__ == "__main__":
    # Create app window
    app = ttk.Window()

    sheet = Sheet(app, 2000, 2000)
    sheet.pack(fill=tk.BOTH, expand=tk.YES)

    app.mainloop()