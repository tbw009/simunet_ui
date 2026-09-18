from simunetcore import Model

# Model implementation for the Custom model
class Custom(Model):
    def __init__(self, name:str=""):
        Model.__init__(self, name)

        # Model parameters
        self.params = {
            # Source code of the model's compute function
            "compute_src"  : {"value": "", "description": "Python compute source", "unit": "-"}
        }
        
        # Model endpoint
        self.site = "local"
        self.threadsafe = False
                        
    def compute(self, *args, **kwargs):
        # Parameters ccompute src
        compute_src = self.get_param("compute_src")
        try:
            exec(compute_src)
        except:
            raise