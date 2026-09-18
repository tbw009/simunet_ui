"""Configuration model for result chart appearance and axis options."""

from simunetcore.serializer import Serializer


class ResultConfig(Serializer):
    """Holds chart result configuration options for plotting output."""

    COLOR_MAPS = [
        'Pastel1', 
        'Pastel2', 
        'Paired', 
        'Accent',
        'Dark2', 
        'Set1', 
        'Set2', 
        'Set3',
        'tab10', 
        'tab20', 
        'tab20b', 
        'tab20c'
    ]

    def __init__(self):
        """Initialize the result config and restore default settings."""
        Serializer.__init__(self)
        self.default()

    def __str__(self):
        """Return the chart title as the string representation."""
        return self.chart_title

    def default(self):
        """Reset the configuration to default chart settings."""
        # Common chart properties
        self.chart_title = "Results"
        self.show_chart_title = True
        self.chart_title_position = "center"
        self.face_color = "#ffffff"
        self.markersize = 4
        self.colormap = "tab10"

        # X-axis
        self.show_frame_limits = True
        self.frame_limits_color = "#9ea6ae"
        self.frame_limits_style = "solid"
        self.frame_limits_line_width = 0.5
        self.show_x_grid = True
        self.x_grid_which = "major"
        self.x_grid_color = "#c4ccd4"
        self.x_grid_style = "dotted"
        self.x_scale = "linear"
        self.x_axis_label = "time [s]"

        # Left y-axis
        self.show_y1_grid = True
        self.y1_show_markers = True
        self.y1_grid_which = "major"
        self.y1_grid_color = "#c4ccd4"
        self.y1_grid_style = "dotted"
        self.y1_scale = "linear"
        self.y1_line_width = 1
        self.y1_var_ids = []

        # Right y-axis
        self.show_y2_grid = True
        self.y2_show_markers = True
        self.y2_grid_which = "major"
        self.y2_grid_color = "#c4ccd4"
        self.y2_grid_style = "dotted"
        self.y2_scale = "linear"
        self.y2_line_width = 1
        self.y2_var_ids = []

        # Legend
        self.show_legend = True
        self.legend_position = "upper right"

    def fill_propertygrid(self, propertygrid, result):
        """Populate a property grid with configurable chart settings."""
        # Common Properties
        propertygrid.add_category("Common")
        propertygrid.add_property(
            "Common", "chart_title", self.chart_title,
            "str", "Chart title", "Sets the chart title.")
        propertygrid.add_property(
            "Common", "show_chart_title", self.show_chart_title,
            "bool", "Show chart title", "Enables or disables the chart title.")
        propertygrid.add_property(
            "Common", "chart_title_position", self.chart_title_position,
            "option", "Chart title position", "Sets the chart title position.",
            options=[
                "center",
                "left",
                "right"])
        propertygrid.add_property(
            "Common", "face_color", self.face_color,
            "color", "Face color", "Configures the facecolor of the chart.")
        propertygrid.add_property(
            "Common", "markersize", self.markersize,
            "spinbox", "Marker size", "Sets the size of the line markers.",
            options={"from_": 2, "to": 8})
        propertygrid.add_property(
            "Common", "colormap", self.colormap,
            "color_map", "Color map", "Sets the color map for the chart.",
            options=['Pastel1', 'Pastel2', 'Paired', 'Accent',
                    'Dark2', 'Set1', 'Set2', 'Set3',
                    'tab10', 'tab20', 'tab20b', 'tab20c'])

        # X-axis properties
        propertygrid.add_category("X-axis")
        propertygrid.add_property(
            "X-axis", "x_axis_label", self.x_axis_label,
            "str", "Label", "Sets the chart x-axis label.")
        propertygrid.add_property(
            "X-axis", "show_frame_limits", self.show_frame_limits,
            "bool", "Show frame limits", "Enables or disables the visibility of frame limits.")
        propertygrid.add_property(
            "X-axis", "frame_limits_color", self.frame_limits_color,
            "color", "Frame limits line color", "Configures the frame limits line color.")
        propertygrid.add_property(
            "X-axis", "frame_limits_style", self.frame_limits_style,
            "option", "Frame limits line style", "Configures the frame limits line style.",
            options=[
                "solid",
                "dashed",
                "dashdot",
                "dotted"])        
        propertygrid.add_property(
            "X-axis", "show_x_grid", self.show_x_grid,
            "bool", "Show grid line", "Enables or disables the chart grid lines.")
        propertygrid.add_property(
            "X-axis", "x_grid_which", self.x_grid_which,
            "option", "Grid line type", "Configures the chart grid line type.",
            options=[
                "both",
                "major",
                "minor"])
        propertygrid.add_property(
            "X-axis", "x_grid_color", self.x_grid_color,
            "color", "Grid line color", "Configures the chart grid line color.")
        propertygrid.add_property(
            "X-axis", "x_grid_style", self.x_grid_style,
            "option", "Grid line style", "Configures the chart grid line style.",
            options=[
                "solid",
                "dashed",
                "dashdot",
                "dotted"])
        propertygrid.add_property(
            "X-axis", "x_scale", self.x_scale,
            "option", "Axis scale", "Sets the scale of the x-axis of the chart.",
            options=[
                "linear",
                "log"])

        # Left y-axis properties
        propertygrid.add_category("Left y-axis")
        propertygrid.add_property(
            "Left y-axis", "y1_var_ids", self.y1_var_ids,
            "multi_var", "Variables on left y-axis", "Selection of visible values on the left y-axis",
            options=result)
        propertygrid.add_property(
            "Left y-axis", "y1_show_markers", self.y1_show_markers,
            "bool", "Show line markers", "Enables or disables the markers for lines.")
        propertygrid.add_property(
            "Left y-axis", "show_y1_grid", self.show_y1_grid,
            "bool", "Show grid line", "Enables or disables the chart grid lines.")
        propertygrid.add_property(
            "Left y-axis", "y1_grid_which", self.y1_grid_which,
            "option", "Grid line type", "Configures the chart grid line type.",
            options=[
                "both",
                "major",
                "minor"])
        propertygrid.add_property(
            "Left y-axis", "y1_grid_color", self.y1_grid_color,
            "color", "Grid line color", "Configures the chart grid line color.")
        propertygrid.add_property(
            "Left y-axis", "y1_grid_style", self.y1_grid_style,
            "option", "Grid line style", "Configures the chart grid line style.",
            options=[
                "solid",
                "dashed",
                "dashdot",
                "dotted"])
        propertygrid.add_property(
            "Left y-axis", "y1_scale", self.y1_scale,
            "option", "Axis scale", "Scale of the y-axis of the chart.",
            options=[
                "linear",
                "log"])

        # Right y-axsis properties
        propertygrid.add_category("Right y-axis")
        propertygrid.add_property(
            "Right y-axis", "y2_var_ids", self.y2_var_ids,
            "multi_var", "Variables on right y-axis", "Selection of visible values on the right y-axis.",
            options=result)
        propertygrid.add_property(
            "Right y-axis", "y2_show_markers", self.y2_show_markers,
            "bool", "Show line markers", "Enables or disables the markers for lines.")
        propertygrid.add_property(
            "Right y-axis", "show_y2_grid", self.show_y2_grid,
            "bool", "Show grid line", "Enables or disables the chart grid lines.")
        propertygrid.add_property(
            "Right y-axis", "y2_grid_which", self.y2_grid_which,
            "option", "Grid line type", "Configures the chart grid line type.",
            options=[
                "both",
                "major",
                "minor"])
        propertygrid.add_property(
            "Right y-axis", "y2_grid_color", self.y2_grid_color,
            "color", "Grid line color", "Configures the chart grid line color.")
        propertygrid.add_property(
            "Right y-axis", "y2_grid_style", self.y2_grid_style,
            "option", "Grid line style", "Configures the chart grid line style.",
            options=[
                "solid",
                "dashed",
                "dashdot",
                "dotted"])
        propertygrid.add_property(
            "Right y-axis", "y2_scale", self.y2_scale,
            "option", "Axis scale", "Scale of the y-axis of the chart.",
            options=[
                "linear",
                "log"])

        # Chart legend Properties
        propertygrid.add_category("Chart legend")
        propertygrid.add_property(
            "Chart legend", "show_legend", self.show_legend,
            "bool", "Show legend", "Enables or disables the legend.")
        propertygrid.add_property(
            "Chart legend", "legend_position", self.legend_position,
            "option", "Legend position", "Sets the legend position.",
            options=[
                "best",
                "upper right",
                "upper left",
                "lower left",
                "lower right",
                "right",
                "center left",
                "center right",
                "lower center",
                "upper center",
                "center"])

    def update_value(self, propertygrid):
        """Apply the edited property value from the grid back to this config."""
        prop = propertygrid.props[propertygrid.value_label]

        self.__dict__[prop["property"]] = prop["value"]
