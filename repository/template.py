from simunetcore import Model
import numpy as np

# Model implementation
class Template(Model):
    def __init__(self, name:str=""):
        Model.__init__(self, name)

        # Model parameters
        self.params = {
            "param_1": {"value": 1.0, "description": "Parameter 1", "unit": "1"},
            "param_1": {"value": 2.0, "description": "Parameter 2", "unit": "1"}
        }
        # Model variables (The units have to match the units of the connected vars)
        self.vars = {
            "var_1": {"description": "Variable 1", "unit": "m"},
            "var_2": {"description": "Variable 2", "unit": "K"},
            "var_3": {"description": "Variable 3", "unit": "1"},
            "var_4": {"description": "Variable 4", "unit": "m"}
        }
        # Model inputs
        self.u = {
            "u_1": {"type": "liquid", "description": "Input 1", "vars": ["var_1", "var_2"]},
            "u_2": {"type": "liquid", "description": "Input 2", "vars": ["var_3"]}
        }
        # Model outputs
        self.y = {
            "y_1": {"type": "liquid", "description": "Output 1", "vars": ["var_4"]}
        }
        # Port adjacencies (Remove if not used)
        self.adj = [
            ["u_1", "y_1"]
        ]
             
    def compute(self, *args, **kwargs):
        # Get parameters
        param_1 = self.get_param("param_1")
        
        # Get input vars
        var_1 = self.get_var("var_1")

        # Get time
        t = self.get_t()

        # Compute output vars
        var_2 = var_1 + param_1*t

        # Store results
        self.set_var("var_2", var_2)