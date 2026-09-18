from simunetcore import Model
import numpy as np

# Model implementation for the Source
class ConstantSource(Model):
    def __init__(self, name=""):
        Model.__init__(self, name)

        # Model endpoint
        self.site = "local"
        self.threadsafe = True
                 
    def compute(self, *args, **kwargs):
        for var_id in self.vars:
            # Create result array
            y = np.full(len(self.t), self.get_var(var_id)[-1]).tolist()
            # Set results
            self.set_var(var_id, y)