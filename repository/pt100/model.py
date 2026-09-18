from simunetcore import Model
import numpy as np

# Model implementation for the Measure Instrument
class Instrument(Model):
    def __init__(self, name:str=""):
        Model.__init__(self, name)
        # Model parameters
        self.params = {
            # Parameters signal range
            "s_range": {"value": [4.0, 20.0], "description": "Signal range (DIN IEC 60381-1)", "unit": "mA"},
            "m_range": {"value": [223.15, 770.15], "description": "Measurement range", "unit": "K"}
        }
        # Model variables
        self.vars = {
            "m" : {"description": "Measurement input", "unit": "K"}, 
            "s" : {"description": "Signal output", "unit": "mA"}
        }
        # Model inputs
        self.u = {
            "u_1" : {"type": "measure", "description": "Instrument input", "vars": ["m"]}
        }
        # Model outputs
        self.y = {
            "y_1" : {"type": "signal", "description": "Instrument output", "vars": ["s"]}
        }
             
    def compute(self, *args, **kwargs):
        # Get parameter q_range
        m_range = self.get_param("m_range") # Measurement range
        s_range = self.get_param("s_range") # Signal range (DIN IEC 60381-1) [mA]
        
        # Get measurement
        x = self.get_var("m")
        x = np.maximum(np.minimum(x, m_range[-1]), m_range[0])

        # linear characteristics follows y = a*x + b
        a = (s_range[-1]-s_range[0])/(m_range[-1]-m_range[0])
        b = s_range[0]
        y = a * (x - m_range[0]) + b

        # Store results
        self.set_var("s", y)
