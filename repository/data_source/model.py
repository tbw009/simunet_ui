from simunetcore import Model
import numpy as np
import pandas as pd

# Model implementation for the data driven source
# The output vector is interpolated on the basis of the given samples
class DataSource(Model):
    def __init__(self, name=""):
        Model.__init__(self, name)
        
        #  Model parameters
        self.params = {
            "samples": {
                "value": {"t": []}, 
                "description": "Sample points", 
                "unit": "-",
                "property": {
                    "editor": "table",
                    "options": None
                }
            }
        }

    def compute(self, *args, **kwargs):
        # Get the value of the samples parameter
        samples = self.get_param("samples")
        header = samples[0]
        values = samples[1]

        # Create a corresponding DataFrame       
        df = pd.DataFrame(values, columns=header)

        # Get the time frame of the samples
        t_sample = df["t"]

        # Handle the vars of the source
        for var_id in self.vars:
            if var_id in df.columns:
                # Get the data for the var from the samples
                y_sample = df[var_id]
                # Interpolate the result
                y = np.interp(self.get_t(), t_sample, y_sample)
            else:
                len_t = len(self.get_t())
                initial_y = self.get_var(var_id)[-1]
                y = np.full(len_t, initial_y) 
            # Set results
            self.set_var(var_id, y)