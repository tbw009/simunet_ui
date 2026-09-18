"""Project model and simulation configuration container."""

from simunetcore.serializer import Serializer
from simunetcore import utils
import uuid


class Project(Serializer):
    """Represents a simulation project with metadata and settings."""

    def __init__(self):
        """Create a new project and initialize default values."""
        self.default()

    def default(self):
        """Reset the project to default metadata, simulation settings, and containers."""
        self.meta = {
            "id": str(uuid.uuid4().hex[:12]),
            "time": utils.current_time(),
            "name": "New project",
            "description": "Description of new project"
        }

        # Simulation settings for Waveform
        self.simulation = {
            "auto_config":False,
            "t_start":0,
            "t_end":360,
            "num_points":1001,
            "max_iter":5000,
            "epsilon":0.001,
            "frame_length":3.6,
            "min_frame_length":0.36,
            "max_frame_length":36,
            "points_per_frame":101,
            "max_iter_frame":15,
            "iter_threshold":1,
            "alpha":1.5,
            "beta":0.25,
            "step_type":"gauss-seidel"
        }

        # The models collection
        self.models = {}

        # The adjacencies
        self.edges = []

        # The varaible map
        self.var_map = {}

        # The aggregated convergence statistics for each frame
        self.statistics = {}

        # The convergence values for each iteration
        self.convergence = []

        # The results
        self.result = {}

        # The chart configurations
        self.configs = []

    def fill_propertygrid(self, propertygrid):
        """Populate a property grid with editable project fields."""
        propertygrid.add_category("Common")
        propertygrid.add_property(
            "Common", "name", self.meta["name"],
            "str", "Name", "Name of the project.")
        propertygrid.add_property(
            "Common", "description", self.meta["description"],
            "str", "Description", "Description of the project.")
        
        # Simulation properties
        propertygrid.add_category("Simulation")
        propertygrid.add_property(
            "Simulation", "t_start", self.simulation["t_start"],
            "float", "Start time", "Start time of the simulation.")
        propertygrid.add_property(
            "Simulation", "t_end", self.simulation["t_end"],
            "float", "End time", "End time of the simulation.")
        propertygrid.add_property(
            "Simulation", "num_points", self.simulation["num_points"],
            "int", "Output points", "The number of output points.", 
            options={"min":101, "max":10001})
        propertygrid.add_property(
            "Simulation", "auto_config", self.simulation["auto_config"],
            "bool", "Auto configuration", 
            "Specifies wether the simunet core chooses the simulation options autmatically or not.")
        
        if not self.simulation["auto_config"]:
            self.fill_propertygrid_options(propertygrid)
            self.fill_propertygrid_frame(propertygrid)

    def fill_propertygrid_options(self, propertygrid):
        """Add simulation option properties to the property grid."""
        propertygrid.add_property(
            "Options", "max_iter", self.simulation["max_iter"],
            "int", "Max. iterations", "The maximum number of overall iterations.", 
            options={"min":0, "max":500000})
        propertygrid.add_property(
            "Options", "epsilon", self.simulation["epsilon"],
            "float", "Epsilon", "The maximum relative error between two iteration steps.", 
            options={"min":1e-20, "max":0.05})
        propertygrid.add_property(
            "Options", "step_type", self.simulation["step_type"],
            "option", "Step type", "The waveform iteration base step type.", 
            options=["gauss-seidel","jacobi"])
        
    def fill_propertygrid_frame(self, propertygrid):
        """Add frame configuration properties to the property grid."""
        propertygrid.add_property(
            "Frame", "frame_length", self.simulation["frame_length"],
            "float", "Initial frame length", "The initial frame length.")
        propertygrid.add_property(
            "Frame", "min_frame_length", self.simulation["min_frame_length"],
            "float", "Min. frame length", "The minimum frame length.")
        propertygrid.add_property(
            "Frame", "max_frame_length", self.simulation["max_frame_length"],
            "float", "Max. frame length", "The maximum frame length.")
        propertygrid.add_property(
            "Frame", "points_per_frame", self.simulation["points_per_frame"],
            "int", "Points per frame", "The number of output points per frame.",
            options={"min":101, "max":5001})
        propertygrid.add_property(
            "Frame", "max_iter_frame", self.simulation["max_iter_frame"],
            "int", "Iterations per frame", "The maximum number of iterations per frame.",
            options={"min":5, "max":100})
        propertygrid.add_property(
            "Frame", "iter_threshold", self.simulation["iter_threshold"],
            "int", "Iteration threshold", "The iterations threshold for frame adaption.",
            options={"min":1, "max":10})
        propertygrid.add_property(
            "Frame", "alpha", self.simulation["alpha"],
            "float", "Alpha", "The expansion factor for frame adaption.", 
            options={"min":1.01, "max":5.0})
        propertygrid.add_property(
            "Frame", "beta", self.simulation["beta"],
            "float", "Beta", "The contraction factor for frame adaption.", 
            options={"min":0.05, "max":0.99})

    def update_value(self, propertygrid):
        """Apply a changed property value back to the project model."""
        prop = propertygrid.props[propertygrid.value_label]
        
        if prop["category"] == "Common":
            # Update common model properties
            self.meta[prop["property"]] = prop["value"]
        else:
            # Update model parameters
            self.simulation[prop["property"]] = prop["value"]

        if self.simulation["auto_config"] and "Frame" in propertygrid.categories:
            propertygrid.remove_category("Frame")
        if self.simulation["auto_config"] and "Options" in propertygrid.categories:
            propertygrid.remove_category("Options")
        if not self.simulation["auto_config"] and "Frame" not in propertygrid.categories:
            self.fill_propertygrid_frame(propertygrid)
        if not self.simulation["auto_config"] and "Options" not in propertygrid.categories:
            self.fill_propertygrid_options(propertygrid)
            

