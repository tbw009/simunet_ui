"""Iterations chart panel for simunet results visualization."""

import ttkbootstrap as ttk
import ttkbootstrap.constants as tk
from simunetcore import plot
from project import Project
from ttkbootstrap.style import Style

import matplotlib
import matplotlib.style

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

matplotlib.use("TkAgg")
matplotlib.style.use("fast")


class Iterations(ttk.Frame):
    """Frame widget that displays simulation iteration statistics."""

    def __init__(self, master, **kwargs):
        """Initialize the iterations chart container."""
        super().__init__(master, **kwargs)

        # Create a figure
        self.figure = Figure(figsize=(9, 4), dpi=90, tight_layout=True)
        
        # Create FigureCanvasTkAgg object
        self.figure_canvas = FigureCanvasTkAgg(self.figure, self)
        self.figure_canvas._update_device_pixel_ratio()

        # Pack wrapper widget into the host frame
        self.figure_canvas_widget=self.figure_canvas.get_tk_widget()
        self.figure_canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # The project
        self.project = None

        # Create the plot
        self.create_plot()

        # Subscribe to ThemeChanged message
        self.bind("<<ThemeChanged>>", self._on_theme_change)

    
    def _on_theme_change(self, *_):
        """Rebuild the plot using current theme colors."""
        self.create_plot()

    def set_project(self, project):
        """Assign a project and redraw the iteration plot."""
        self.project = project
        self.create_plot()
        
    def create_plot(self):
        """Render the iteration plot for the current project data."""
        self.figure.clear()
        self.figure.set_facecolor("#ffffff")

        if self.project:
            # Load the data
            statistics = self.project.statistics
            epsilon = self.project.simulation["epsilon"]
            
            # Retrieve theme colors
            col_0=Style().colors.primary
            col_1=Style().colors.secondary
            col_2=Style().colors.danger

            # Use plot lib from simunet
            plot.plot_iterations(
                self.figure, statistics, epsilon,
                col_0=col_0, col_1=col_1, col_2=col_2)
            for ax in self.figure.axes:
                ax.set_facecolor("#ffffff")

            # Update the canvas
            self.figure_canvas.draw()

    def fill_propertygrid(self, propertygrid):
        """Populate the property grid with iteration widget settings."""
        pass

    def update_value(self, propertygrid):
        """Update widget state from the property grid values."""
        pass

if __name__ == "__main__":
    # Create app window
    app = ttk.Window()

    project = Project()
    project.load("./projects/cstr.sim")

    res = Iterations(app)
    res.set_project(project)
    res.pack(fill=tk.BOTH, expand=tk.YES)

    app.mainloop()