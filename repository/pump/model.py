from simunetcore import Model
import numpy as np

# Model implementation for the Tank
class Pump(Model):
    def __init__(self, name:str=""):
        Model.__init__(self, name)

        # Model parameters
        self.params = {
            # Parameters pump
            "c_range": {"value": [4.0, 20.0], "description": "Range of control value", "unit": "mA"},
            "q_range": {"value": [0.0, 0.005], "description": "Range of flow rate", "unit": "m³\\s"}
        }
        # Model variables
        self.vars = {
            "c": {"description": "Control value", "unit": "mA"},
            "q": {"description": "Flow Rate", "unit": "m³/s"} 
        }
        # Model inputs
        self.u = {
            "u_1": {"type": "liquid", "description": "Pump feed input", "vars": []},
            "u_2": {"type": "control", "description": "Control value input", "vars": ["c"]}
        }
        # Model outputs
        self.y = {
            "y_1": {"type": "liquid", "description": "Pump output", "vars": ["q"]}
        }
        # Port adjacencies
        self.adj = [
            ["u_1", "y_1"]
        ]
             
    def compute(self, *args, **kwargs):
        # Get parameter q_range
        q_range = self.get_param("q_range") # Range of flow rate [m³\s]
        c_range = self.get_param("c_range") # Range of control value [mA]
        
        # Get control value
        c = self.get_var("c")
        c = np.maximum(np.minimum(c, c_range[-1]), c_range[0])
        c = (c-c_range[0])/(c_range[-1]-c_range[0])
        
        # Compute flow
        q = np.ones(c.shape)*q_range[0] + c*(q_range[-1]-q_range[0])

        # Store results
        self.set_var("q", q)