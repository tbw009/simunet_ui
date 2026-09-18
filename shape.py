"""Shape widget for the diagram sheet.

This module defines the draggable diagram shape used in the application
canvas. It manages appearance, ports, model metadata, and property grid
integration.
"""

import ttkbootstrap.constants as tk
from repository import RepositoryItem
import uuid
import csv
from ttkbootstrap.style import Style


class Shape:
    """Represents a diagram shape with ports and model metadata.

    Shapes are rendered on a canvas-like sheet and provide selection,
    movement, and property editing support.
    """

    # Shape attributes
    SIZE          = 100
    WIDTH         = 1
    ICON_SIZE     = 48.0
    FONT          = ("TkDefaultFont", 8)
    COLORS = {
        "undefined": "#ff0000",
        "default":   "#000000"
    }

    # Port attributes
    PORT_DISTANCE = 20
    PORT_SIZE     = 10
    PORT_COLORS = {
        "default":   ["#ffffff", "#ffffff"],
        "adaptive":  ["#ffffaa", "#ffffaa"], 
        "liquid":    ["#ffffff", "#aaaaaa"], 
        "gas":       ["#ffffff", "#aaaaaa"], 
        "solid":     ["#ffffff", "#aaaaaa"], 
        "measure":   ["#aaffaa", "#aaffaa"], 
        "signal":    ["#aaaaff", "#aaaaff"], 
        "control":   ["#ffaaaa", "#ffaaaa"],
        "material":  ["#aaddff", "#aaddff"], 
        "cost":      ["#ffddaa", "#ffddaa"], 
        "energy":    ["#ffaaff", "#ffaaff"]
    }

    def __init__(self, sheet, x, y, repo_path, scale, tag=None):
        """Initialize the shape on the sheet.

        Args:
            sheet: Canvas-like sheet where the shape is drawn.
            x: X-coordinate of the shape origin.
            y: Y-coordinate of the shape origin.
            repo_path: Repository path for the shape model.
            scale: Scale factor for the shape dimensions.
            tag: Optional unique tag for grouping shape items.
        """
        self.sheet = sheet
        self.x = x
        self.y = y

        self.tag = tag if tag else str(uuid.uuid4().hex[:12])
        self.selected = False
        self.repo_path = repo_path
        self.model = None

        repo_item = RepositoryItem(repo_path, scale*self.ICON_SIZE)
        self.model_icon = repo_item.model_icon
        self.class_name = repo_item.class_name
        self.class_icon = repo_item.class_icon

        num_y_ports = len(repo_item.model_dict["y"])
        num_u_ports = len(repo_item.model_dict["u"])

        # Compute geometry
        height = max(scale*self.SIZE, max(num_y_ports, num_u_ports)*scale*self.PORT_DISTANCE)
        width = scale * self.SIZE
        port_size = scale * self.PORT_SIZE
        port_distance = scale * self.PORT_DISTANCE

        # Outer frame
        self.frame = self.sheet.create_round_rectangle(
            x, y, x+width, y+height, width=self.WIDTH, radius=port_distance,
            outline=self.COLORS["default"], fill=Style().colors.light, 
            tags=[self.tag, "frame", "shape"])

        # Model image
        self.image = self.sheet.create_image(
            x+width/2, y+height/2+1.5*port_size, anchor=tk.CENTER,  
            image=self.model_icon, tags=[self.tag, "model_icon", "shape"])
  
        # Model class image
        self.image_class = self.sheet.create_image(
            x+width-1, y+1, anchor=tk.NE, image=self.class_icon, 
            tags=[self.tag, "class_icon", "shape"])

        # Model name
        self.label = self.sheet.create_text(
            x+width/2, y+2.5*port_size, fill=Style().colors.dark,
            font=(self.FONT[0], int(self.FONT[1]*scale)), 
            text=repo_item.model_dict["name"], tags=[self.tag, "text", "shape"])

        # Inputs on the left
        self.ports_in = {}
        if num_u_ports > 0:
            pad_y = (height - (num_u_ports - 1) * port_distance) / 2
            num_port = 0
            for key in repo_item.model_dict["u"]:
                port_x = x - port_size / 2
                port_y = y + pad_y + port_distance * num_port-port_size / 2
                port_type = repo_item.model_dict["u"][key]["type"]
                if port_type in self.PORT_COLORS:
                    color = self.PORT_COLORS[port_type][0]
                else:
                    color = self.PORT_COLORS["default"][0]
                    
                self.ports_in[key] = self.sheet.create_arrow(
                    port_x, port_y, port_x+port_size, port_y+port_size,
                    outline=self.COLORS["default"], fill=color, 
                    tags=[self.tag, "in", key, "shape"])
                num_port += 1
        

        # Outputs on the right
        self.ports_out = {}
        if num_y_ports > 0:
            pad_y = (height - (num_y_ports - 1) * port_distance) / 2
            num_port = 0
            for key in repo_item.model_dict["y"]:
                port_x = width + x -port_size / 2
                port_y = y + pad_y + port_distance * num_port - port_size / 2
                port_type = repo_item.model_dict["y"][key]["type"]
                if port_type in self.PORT_COLORS:
                    color = self.PORT_COLORS[port_type][1]
                else:
                    color = self.PORT_COLORS["default"][1]

                self.ports_out[key] = self.sheet.create_arrow(
                    port_x, port_y, port_x+port_size, port_y+port_size,
                    outline=self.COLORS["default"], fill=color, 
                    tags=[self.tag, "out", key, "shape"])
                num_port += 1
   
    def set_model(self, model):
        """Associate a runtime model with the shape.

        Args:
            model: Model instance containing name, description and variable data.
        """
        self.model = model
        # Update label
        self.sheet.itemconfigure(self.label, text=model.name)
        # Update state
        self.update_defined_state()

    def move(self, dx, dy):
        """Move the shape by a relative delta.

        Args:
            dx: Horizontal delta in pixels.
            dy: Vertical delta in pixels.
        """
        self.x += dx
        self.y += dy
        
        # Move the shape by deltas
        self.sheet.move(self.tag, dx, dy)

        # Generate <<ShapeMoved>> event
        self.sheet.event_generate("<<ShapeMoved>>")

    def set_position(self, x, y):
        """Set the shape to an absolute position.

        Args:
            x: New X-coordinate for the shape.
            y: New Y-coordinate for the shape.
        """
        dx = x - self.x
        dy = y - self.y
        # Move the shape
        self.move(dx, dy)

    def select(self):
        """Mark the shape as selected and update its appearance."""
        self.selected = True
        # Configure frame background color
        self.sheet.itemconfigure(self.frame, fill=Style().colors.selectbg)
        # Configure label foreground color
        self.sheet.itemconfigure(self.label, fill=Style().colors.selectfg)

    def unselect(self):
        """Clear selection state and restore default appearance."""
        self.selected = False
        # Configure frame background color
        self.sheet.itemconfigure(self.frame, fill=Style().colors.light)
        # Configure label foreground color
        self.sheet.itemconfigure(self.label, fill=Style().colors.dark)

    def get_port_side(self, port):
        """Return the horizontal side of a port relative to the shape.

        Args:
            port: Canvas object id for the port.

        Returns:
            tk.LEFT or tk.RIGHT depending on the port position.

        Raises:
            ValueError: If the port is not part of this shape.
        """
        if port in self.ports_in.values() or port in self.ports_out.values():
            frame_coords = self.sheet.coords(self.frame)
            port_coords = self.sheet.coords(port)
            if port_coords[0] < frame_coords[0]:
                return tk.LEFT
            else:
                return tk.RIGHT
        else:
            raise ValueError("The port '{}' is not an element of this shape.".format(port))

    def switch_ports(self):
        """Toggle the horizontal side for all shape ports.

        Ports on the left and right are mirrored against the shape frame.
        """
        frame_coords = self.sheet.coords(self.frame)
        
        for port in self.ports_in.values():
            port_coords = self.sheet.coords(port)
            coord_index = 2 if port_coords[0] < frame_coords[0] else 0
            # Compute new port coords
            x1= frame_coords[coord_index] - (port_coords[2] - port_coords[0]) / 2
            y1= port_coords[1]
            x2= frame_coords[coord_index] + (port_coords[2] - port_coords[0]) / 2
            y2 = port_coords[3]
            # Update port coords
            self.sheet.coords(port, x1, y1, x2, y2)

        for port in self.ports_out.values():
            port_coords = self.sheet.coords(port)
            coord_index = 2 if port_coords[0] < frame_coords[0] else 0
            # Compute new port coords
            x1= frame_coords[coord_index] - (port_coords[2] - port_coords[0]) / 2
            y1= port_coords[1]
            x2= frame_coords[coord_index] + (port_coords[2] - port_coords[0]) / 2
            y2 = port_coords[3]
            # Update port coords
            self.sheet.coords(port, x1, y1, x2, y2)
    
    def is_defined(self):
        """Return whether the associated model has all initial values defined.

        Returns:
            bool: True when every initial variable has at least one value.
        """
        u_vars = self.model.get_u_vars()
        i_vars = [var_id for var_id in self.model.vars if var_id not in u_vars]

        # Check if every var has an initial value
        for var_id in i_vars:
            value = self.model.vars[var_id].get("value", [])
            if len(value) == 0:
                return False
        return True

    def update_defined_state(self):
        """Update the shape outline based on model completion status."""
        if self.is_defined():
            # Set default frame color
            self.sheet.itemconfig(self.frame, outline=self.COLORS["default"])
        else:
            # Set undefined frame color
            self.sheet.itemconfig(self.frame, outline=self.COLORS["undefined"])

    def update_theme(self):
        """Refresh the shape appearance for the current theme."""
        self.update_defined_state()
        if self.selected:
            self.sheet.itemconfigure(self.frame, fill=Style().colors.selectbg)
            self.sheet.itemconfigure(self.label, fill=Style().colors.selectfg)
        else:
            self.sheet.itemconfigure(self.frame, fill=Style().colors.light)
            self.sheet.itemconfigure(self.label, fill=Style().colors.dark)

    def fill_propertygrid(self, propertygrid):
        """Populate the property grid with shape and model metadata."""
        propertygrid.add_category("Common")
        propertygrid.add_property(
            "Common", "class", self.class_name,
            "str", "Class", "The class of the shape's underlying  model.", state=tk.READONLY)
        propertygrid.add_property(
            "Common", "id", self.tag,
            "str", "Shape ID", "The unique id of the shape.", state=tk.READONLY)
        propertygrid.add_property(
            "Common", "name", self.model.name,
            "str", "Name", "Sets the name of the model.")
        propertygrid.add_property(
            "Common", "description", self.model.description,
            "str", "Description", "Sets a brief description of the model.")
        
        # Common model Properties
        propertygrid.add_category("Model")
        propertygrid.add_property(
            "Model", "dim", self.model.dim, 
            "option", "Dimension", "Sets the dimension of the model.", 
            options=["unknown", "0D", "1D", "2D", "3D"], state=tk.READONLY)
        propertygrid.add_property(
            "Model", "domain", self.model.domain,
            "str", "Domain", "Sets the domain of the model.", 
            state=tk.READONLY)
        propertygrid.add_property(
            "Model",  "threadsafe", self.model.threadsafe, 
            "bool", "Threadsafe", "Sets wether the model is threadsafe or not.", 
            state=tk.READONLY)

        # Endpoint properties for models that support remote execution
        if "endpoint" in self.model.__dict__:
            propertygrid.add_category("Endpoint")

            for key in self.model.endpoint:
                value = self.model.endpoint[key]
                description = "Sets the endpoint parameter '{}' of the model.".format(key)
                prop_type = "str"
                if type(value) is bool:
                    prop_type = "bool"
                
                propertygrid.add_property(
                    "Endpoint", key, value, 
                    prop_type, key, description)
            
        self.add_parameters(propertygrid)
        self.add_initial_values(propertygrid)

    def add_parameters(self, propertygrid):
        """Add model parameters to the property grid.

        Args:
            propertygrid: Property grid widget to populate.
        """
        if len(self.model.params) > 0:
            propertygrid.add_category("Parameters")
            for param_id in self.model.params:
                value = self.model.params[param_id].get("value")
                unit = self.model.params[param_id].get("unit")
                description = self.model.params[param_id].get("description")
                description += "\nUnit: [{}]".format(unit)
                editor = None
                options = None
                state=tk.NORMAL
                if "property" in self.model.params[param_id]: 
                    editor = self.model.params[param_id]["property"].get("editor")
                    options = self.model.params[param_id]["property"].get("options")
                    state = self.model.params[param_id]["property"].get("state", tk.NORMAL)

                if not editor:
                    editor = "str"
                    if type(value) is float:
                        editor = "float"
                        if unit != "-" and unit != "":
                            editor = "quantity"
                            value=[value, unit]
                            options = unit
                    elif type(value) is int:
                        editor = "int"
                    elif type(value) is list:                       
                        editor = "range"

                propertygrid.add_property(
                    category="Parameters", 
                    property=param_id, 
                    value=value, 
                    editor=editor, 
                    displayname=param_id, 
                    description=description, 
                    state=state,
                    options=options)

    def add_initial_values(self, propertygrid):
        """Add initial model values to the property grid."""
        u_vars = self.model.get_u_vars()
        i_vars = [var_id for var_id in self.model.vars if var_id not in u_vars]
        if len (i_vars) > 0:
            propertygrid.add_category("Initial values")
            for var_id in i_vars:
                value = self.model.vars[var_id].get("value", [])
                value = value[0] if len(value) == 1 else ""
                unit = self.model.vars[var_id].get("unit")
                description = self.model.vars[var_id].get("description")
                description += "\nUnit: [{}]".format(unit)
                editor = "float"
                options = None
                if unit != "-" and unit != "":
                    editor = "quantity"
                    value=[value, unit]
                    options = unit

                propertygrid.add_property(
                    category="Initial values", 
                    property=var_id, 
                    value=value, 
                    editor=editor, 
                    displayname=var_id, 
                    description=description,
                    options=options)

    def update_value(self, propertygrid):
        """Apply a changed property value back to the model or shape."""
        prop = propertygrid.props[propertygrid.value_label]
        
        if prop["category"] == "Common":
            # Update common model properties
            self.model.__dict__[prop["property"]] = prop["value"]
            
            if prop["property"] == "name":
                # Update the label
                self.sheet.itemconfigure(self.label, text= self.model.name)

        elif prop["category"] == "Endpoint":
            # Update endpoint properties
            self.model.endpoint[prop["property"]] = prop["value"]

        elif prop["category"] == "Parameters":

            if prop["editor"] == "quantity":
                # Update the model
                self.model.params[prop["property"]]["value"] = prop["value"][0]
                self.model.params[prop["property"]]["unit"] = prop["value"][1]
                self.update_defined_state()
            else:
                # Update model parameters
                self.model.params[prop["property"]]["value"] = prop["value"]

            if prop["property"] == "csv_file":
                # Update the model
                self.create_vars_from_csv(self.model)
                self.update_defined_state()
            # Remove previous initial values
            if "Initial values" in propertygrid.categories:
                propertygrid.remove_category("Initial values")
            # add new initial values
            self.add_initial_values(propertygrid)

        elif prop["category"] == "Initial values":

            if prop["editor"] == "quantity":
                # Update the model
                self.model.vars[prop["property"]]["value"] = [prop["value"][0]]
                self.model.vars[prop["property"]]["unit"] = prop["value"][1]
            else:
                # Update model parameters
                self.model.vars[prop["property"]]["value"] = [prop["value"]]
            
            # Update the defined state of the shape
            self.update_defined_state()

    def create_vars_from_csv(self, model):
        """Create model variables from CSV file definitions.

        Args:
            model: Model instance containing the csv_file parameter.
        """
        csv_file = model.get_param("csv_file")
        
        # Set delimiter if not provided
        with open(csv_file, "r") as f:
            # Read csv file
            filedata = f.read()
            # Sniff the csv dialect
            dialect = csv.Sniffer().sniff(filedata)
            # Set csv header
            f.seek(0)
            reader = csv.DictReader(f, delimiter=dialect.delimiter)
            
            # Clear var array
            model.vars.clear()
            # Add fieldnames into var dict
            for field in reader.fieldnames[1:]:
                model.vars[field]={
                    "description" : field,
                    "unit"        : "-",
                    "value"       : [0.0]
                }

            # Clear outputs
            model.y.clear()
            # Define output
            model.y["y_1"] = {
                "type": "unknown",
                "description": "source",
                "vars": reader.fieldnames[1:]
            }       