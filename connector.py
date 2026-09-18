"""Connector geometry and routing logic for diagram edges.

This module defines the `Connector` class used to draw and manage routed
connections between shape ports on the sheet. It tracks connector state,
visual appearance, variable mappings, and predecessor/successor chains.
"""

import copy
import uuid

import networkx as nx
import ttkbootstrap.constants as tk


class Connector:
    """Shape connector managing line geometry and connection state."""

    # Connector attributes
    ARROW      = (10, 11, 5)
    WIDTH      = 1

    # Autorouting parameters
    OFFSET     = 10
    OFFSET_IN  = 15
    OFFSET_OUT = 5

    COLORS = {
        "undefined": "#ff0000",
        "default":   "#000000",
        "edit":      "#a0a0a0",
        "unknown":   "#808080",
        "adaptive":  "#000000",
        "liquid":    "#000000", 
        "gas":       "#000000", 
        "solid":     "#000000", 
        "measure":   "#00aa00", 
        "signal":    "#0000c0", 
        "control":   "#c00000",
        "material":  "#000000", 
        "cost":      "#aaaa00", 
        "energy":    "#aa00aa"
    }

    def __init__(self, sheet, src_port, dest_port, scale, tag=None):
        """Initialize a connector between two shape ports.

        Args:
            sheet: The diagram sheet owning the connector.
            src_port: Source port tuple (shape_id, direction, port_id).
            dest_port: Destination port tuple (shape_id, direction, port_id).
            scale: Current zoom scale of the sheet.
            tag: Optional explicit tag for the connector.
        """

        self.sheet = sheet
        self.src_port = src_port
        self.dest_port = dest_port
        self.tag = tag if tag else str(uuid.uuid4().hex[:12])
        self.selected = False
        self.line = self.sheet.create_line(
            0,
            0,
            0,
            0,
            capstyle=tk.BUTT,
            joinstyle=tk.MITER,
            arrow=tk.NONE,
            width=self.WIDTH,
            fill=self.COLORS["default"],
            arrowshape=self.ARROW,
            tags=[self.tag, "connector"],
        )
        self.sheet.itemconfig(self.line, state=tk.HIDDEN)

        self.var_map = {}
        self.set_src_port(src_port)
        self.set_dest_port(dest_port)
        self.direction = None

    def set_src_port(self, src_port):
        """Set the source port and position the connector start.

        Args:
            src_port: Source port tuple (shape_id, direction, port_id).
        """
        if src_port:
            # Set the source port
            self.src_port = src_port

            # Retrieve source port properties
            shape_id, _, port_id = self.src_port
            shape = self.sheet.shapes[shape_id]
            port = shape.ports_out[port_id]
            port_coords = self.sheet.coords(port)

            # Compute start coords of the line
            x = port_coords[4]
            y = port_coords[5]

            # Update the line
            self.sheet.coords(self.line, x, y, x, y)
            self.sheet.itemconfig(self.line, state=tk.NORMAL)
            self.sheet.tag_raise(self.tag, "grid")

    def set_dest_coord(self, x, y):
        """Set the connector target coordinate and draw the route.

        Args:
            x: Destination x coordinate.
            y: Destination y coordinate.
        """
        # Retrieve source port properties
        shape_id = self.src_port[0]
        shape = self.sheet.shapes[shape_id]
        frame_coords = self.sheet.coords(shape.frame)
        line_coords = self.sheet.coords(self.line)

        # Compute offsets
        connectors = self.sheet.get_connectors(shape_id, "out")
        index = len(connectors) if self not in connectors else connectors.index(self)
        single_offset = self.sheet.zoom_factor * self.OFFSET
        out_offset = self.sheet.zoom_factor * self.OFFSET_OUT
        offset_h = single_offset * index + out_offset
        offset_v = single_offset * (index + 1)

        # First coord pair
        x0 = line_coords[0]
        y0 = line_coords[1]

        # Second coord pair
        x1 = x0 + offset_h
        if x < frame_coords[2]:
            # We are heading to the left
            if y < y0:
                # Draw above the shape
                y1 = min(frame_coords[1] - offset_v, y)
            else:
                # Draw under the shape
                y1 = max(frame_coords[3] + offset_v, y)
        else:
            # We are heading to the right
            y1 = y

        # Update the line geometry
        self.sheet.coords(self.line, x0, y0, x1, y0, x1, y1, x, y1, x, y)
        self.sheet.itemconfig(self.line, arrow=tk.NONE, fill=self.COLORS["edit"])

    def set_dest_port(self, dest_port):
        """Set the destination port and route the connector accordingly.

        Args:
            dest_port: Destination port tuple (shape_id, direction, port_id).
        """
        if dest_port:
            # Set the destination port
            self.dest_port = dest_port

            # Retrieve source port properties
            src_shape = self.sheet.shapes[self.src_port[0]]
            src_frame_coords = self.sheet.bbox(src_shape.frame)

            # Retrieve destination port properties
            shape_id, _, port_id = self.dest_port
            shape = self.sheet.shapes[shape_id]
            frame_coords = self.sheet.bbox(shape.frame)
            port = shape.ports_in[port_id]
            port_coords = self.sheet.coords(port)

            # Compute offsets
            connectors = self.sheet.get_connectors(shape_id, "in")
            index = len(connectors) if self not in connectors else connectors.index(self)
            single_offset = self.sheet.zoom_factor * self.OFFSET
            in_offset = self.sheet.zoom_factor * self.OFFSET_IN
            offset_h = single_offset * index + in_offset
            offset_v = single_offset * (index + 1)

            # Correct vertical offset if source and destination are the same model
            if self.dest_port[0] == self.src_port[0]:
                offset_v -= single_offset

            # Use the destination port coords to update line
            x = port_coords[0]
            y = port_coords[5]
            self.set_dest_coord(x, y)

            # Retrieve the current coords of the line
            line_coords = self.sheet.coords(self.line)
            x0, y0, x1, y1, x2, y2 = line_coords[0:6]

            # Route the connection around shapes if needed
            if x1 > x - offset_h:
                # There is not enough space between the shapes to connect directly
                x2 = port_coords[0] - offset_h
                if y2 > y1:
                    # Source shape is above destination shape
                    if frame_coords[1] - src_frame_coords[3] >= offset_v + single_offset:
                        y2 = src_frame_coords[3] + offset_v
                    else:
                        y2 = max(frame_coords[3] + offset_v, y2)
                        if x1 < frame_coords[2] + offset_v:
                            x1 = frame_coords[2] + offset_v
                else:
                    # Destination shape is below source shape
                    if src_frame_coords[1] - frame_coords[3] >= offset_v + single_offset:
                        y2 = src_frame_coords[1] - offset_v
                    else:
                        y2 = min(frame_coords[1] - offset_v, y2)
                        if x1 < frame_coords[2] + offset_v:
                            x1 = frame_coords[2] + offset_v

                # Update line coords with a detour route
                self.sheet.coords(
                    self.line,
                    x0, y0, x1, y1,
                    x1, y2, x2, y2,
                    x2, y, x, y,
                )
            else:
                # There is enough space between the shapes to connect directly
                self.sheet.coords(self.line, x0, y0, x1, y0, x1, y, x, y)

        self.update_defined_state()

    def get_color(self):
        """Return the connector color based on its destination/source types."""
        if self.dest_port:
            dest_shape_id, _, dest_port_id = self.dest_port
            dest_shape = self.sheet.shapes[dest_shape_id]
            dest_port = dest_shape.model.u[dest_port_id]

            src_shape_id, _, src_port_id = self.src_port
            src_shape = self.sheet.shapes[src_shape_id]
            src_port = src_shape.model.y[src_port_id]
            if dest_port["type"] == "adaptive":
                return self.COLORS[src_port["type"]]
            return self.COLORS[dest_port["type"]]

        return self.COLORS["default"]
        
    def is_defined(self):
        """Return True if all connected variable mappings are defined."""
        return None not in self.var_map.values()

    def update_defined_state(self):
        """Update the connector appearance based on its defined state."""
        if self.is_defined():
            self.sheet.itemconfig(self.line, state=tk.NORMAL, arrow=tk.LAST, fill=self.get_color())
        else:
            self.sheet.itemconfig(self.line, state=tk.NORMAL, arrow=tk.LAST, fill=self.COLORS["undefined"])

    def update_theme(self):
        """Refresh the connector theme by updating its defined state."""
        self.update_defined_state()

    def set_var_map(self, var_map):
        """Set the connector variable mapping and refresh its state."""
        self.var_map = var_map
        self.update_defined_state()

    def create_var_map(self):
        """Build the variable mapping for the connector.

        Auto-assigns variables between source and destination models.
        """
        self.var_map.clear()
        if self.dest_port and self.src_port:
            dest_shape_id, _, dest_port_id = self.dest_port
            dest_shape = self.sheet.shapes[dest_shape_id]
            dest_port = dest_shape.model.u[dest_port_id]

            src_shape_id, _, src_port_id = self.src_port
            src_shape = self.sheet.shapes[src_shape_id]
            src_port = src_shape.model.y[src_port_id]

            # Create varmap for sinks (auto-copy output vars of connected model)
            if dest_port["type"] == "adaptive":
                for var_id in dest_port["vars"]:
                    dest_shape.model.vars.pop(var_id)
                dest_port["vars"].clear()

                for var_id in src_port["vars"]:
                    dest_shape.model.vars[var_id] = copy.deepcopy(src_shape.model.vars[var_id])
                    dest_port["vars"].append(var_id)
                    if var_id not in self.var_map:
                        self.var_map[var_id] = [src_shape_id, var_id]

            # Create varmap for sources (auto-copy input vars of successor models)
            elif src_port["type"] == "adaptive":
                for var_id in src_port["vars"]:
                    src_shape.model.vars.pop(var_id)
                src_port["vars"].clear()

                chain = self.create_successor_chain(src_shape_id, src_port_id)

                for shape_id, edge_data in chain:
                    shape = self.sheet.shapes[shape_id]
                    port_id = edge_data["ports"][1]
                    port = shape.model.u[port_id]
                    if port["type"] != "adaptive":
                        for var_id in port["vars"]:
                            if var_id not in src_shape.model.vars:
                                src_shape.model.vars[var_id] = copy.deepcopy(shape.model.vars[var_id])
                                src_port["vars"].append(var_id)
                        src_shape.update_defined_state()

                for var_id in dest_port["vars"]:
                    if var_id not in self.var_map:
                        self.var_map[var_id] = [src_shape_id, var_id]

            # Create varmap for all other models
            else:
                for var_id in dest_port["vars"]:
                    if var_id not in self.var_map:
                        self.var_map[var_id] = None

    def update(self):
        """Refresh the connector route based on current source/destination ports."""
        self.set_src_port(self.src_port)
        self.set_dest_port(self.dest_port)

    def select(self):
        """Mark this connector as selected."""
        self.selected = True

    def unselect(self):
        """Unmark selection and refresh connector appearance."""
        self.selected = False
        self.update_defined_state()

    def create_successor_chain(self, shape_id, port_id):
        """Return the successor chain for an adaptive source port.

        The chain is built from the current connector graph and internal
        adjacency metadata.
        """
        # Create the search node name (internal adjacencies)
        search_node = shape_id
        model = self.sheet.shapes[shape_id].model
        for adj in model.adj:
            if port_id == adj[1]:
                search_node += ".{}-{}".format(adj[0], adj[1])
                break

        # Handle internal adjacencies
        edges = []
        for connector_id in self.sheet.connectors:
            connector = self.sheet.connectors[connector_id]

            src_shape_id, _, src_port_id = connector.src_port
            dest_shape_id, _, dest_port_id = connector.dest_port

            src_model = self.sheet.shapes[src_shape_id].model
            dest_model = self.sheet.shapes[dest_shape_id].model

            for adj in src_model.adj:
                if src_port_id == adj[1]:
                    src_shape_id += ".{}-{}".format(adj[0], adj[1])
                    break

            for adj in dest_model.adj:
                if dest_port_id == adj[0]:
                    dest_shape_id += ".{}-{}".format(adj[0], adj[1])
                    break

            edges.append([
                src_shape_id,
                dest_shape_id,
                {
                    "ports": [src_port_id, dest_port_id],
                    "tag": connector_id,
                },
            ])

        # Create a DiGraph and build the successor chain
        graph = nx.DiGraph(edges)
        successor = nx.dfs_edges(graph, search_node)

        # Filter nodes to fix double entries
        filtered = []
        for item in successor:
            stripped = item[1].split(".")[0]
            if stripped not in filtered and stripped != shape_id:
                filtered.append([stripped, graph.get_edge_data(item[0], item[1])])

        return filtered

    def create_predecessor_chain(self, shape_id, port_id):
        """Return the predecessor chain for a destination port.

        This method computes the chain of upstream shapes that can provide
        variable assignments to the destination port.
        """
        # Create the search node name (internal adjacencies)
        search_node = shape_id
        model = self.sheet.shapes[shape_id].model
        for adj in model.adj:
            if port_id == adj[0]:
                search_node += ".{}-{}".format(adj[0], adj[1])
                break

        # Handle internal adjacencies
        edges = []
        for connector_id in self.sheet.connectors:
            connector = self.sheet.connectors[connector_id]

            src_shape_id, _, src_port_id = connector.src_port
            dest_shape_id, _, dest_port_id = connector.dest_port

            src_model = self.sheet.shapes[src_shape_id].model
            dest_model = self.sheet.shapes[dest_shape_id].model

            for adj in src_model.adj:
                if src_port_id == adj[1]:
                    src_shape_id += ".{}-{}".format(adj[0], adj[1])
                    break

            for adj in dest_model.adj:
                if dest_port_id == adj[0]:
                    dest_shape_id += ".{}-{}".format(adj[0], adj[1])
                    break

            edges.append([
                src_shape_id,
                dest_shape_id,
                {
                    "ports": [src_port_id, dest_port_id],
                    "tag": connector_id,
                },
            ])

        # Create a DiGraph and build the predecessor chain
        graph = nx.DiGraph(edges)
        predecessor = nx.dfs_predecessors(graph.reverse(), search_node)

        # Filter nodes to fix double entries
        filtered = []
        for item in predecessor:
            stripped = item.split(".")[0]
            if stripped not in filtered and stripped != shape_id:
                filtered.append(stripped)

        return filtered

    def fill_propertygrid(self, propertygrid):
        """Populate the property grid with connector metadata."""
        # Common model Properties
        propertygrid.add_category("Common")
        propertygrid.add_property(
            "Common",
            "id",
            self.tag,
            "str",
            "Connector ID",
            "The unique id of the connector.",
            state=tk.READONLY,
        )

        propertygrid.add_category("Source")
        src = self.sheet.shapes[self.src_port[0]]
        propertygrid.add_property(
            "Source",
            "source_shape",
            src.model.name,
            "str",
            "Shape",
            "Source shape",
            state=tk.DISABLED,
        )
        propertygrid.add_property(
            "Source",
            "source_port",
            self.src_port[2],
            "str",
            "Port",
            "Source port",
            state=tk.DISABLED,
        )

        propertygrid.add_category("Destination")
        dest = self.sheet.shapes[self.dest_port[0]]
        propertygrid.add_property(
            "Destination",
            "dest_shape",
            dest.model.name,
            "str",
            "Shape",
            "Destination shape",
            state=tk.DISABLED,
        )
        propertygrid.add_property(
            "Destination",
            "dest_port",
            self.dest_port[2],
            "str",
            "Port",
            "Destination port",
            state=tk.DISABLED,
        )

        # Var map of the connector
        port = dest.model.u[self.dest_port[2]]
        if len(port["vars"]) > 0:
            cat_name = "Assignments for {} of {}".format(
                self.dest_port[2], dest.model.name
            )
            propertygrid.add_category(cat_name)

            options = {}
            chain = self.create_predecessor_chain(self.dest_port[0], self.dest_port[2])
            for shape_id in chain:
                shape = self.sheet.shapes[shape_id]
                options[shape.tag] = {
                    "name": shape.model.name,
                    "vars": shape.model.vars,
                }

            for var_id in port["vars"]:
                unit = dest.model.vars[var_id].get("unit")
                description = dest.model.vars[var_id].get("description")
                description += "\nUnit: [{}]".format(unit)
                value = [] if self.var_map[var_id] is None else [self.var_map[var_id]]

                propertygrid.add_property(
                    category=cat_name,
                    property=var_id,
                    value=value,
                    editor="single_var",
                    displayname="{} =".format(var_id),
                    description=description,
                    options=options,
                )

    def update_value(self, propertygrid):
        """Update connector state from a changed property grid entry."""
        prop = propertygrid.props[propertygrid.value_label]

        if prop["category"] == "Common":
            self.__dict__[prop["property"]] = prop["value"]

        if prop["category"].startswith("Assignment"):
            var_id = prop["property"]
            value = prop["value"]
            self.var_map[var_id] = value[0]
            self.update_defined_state()
