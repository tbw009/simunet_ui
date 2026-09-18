from simunetcore import Model

# Model implementation for the Sink
class Sink(Model):
    def __init__(self, name=""):
        Model.__init__(self, name)
        
        # Model endpoint
        self.site = "local"
        self.threadsafe = True
        
    def compute(self, *args, **kwargs):
        # The sink has no output, nothing to do here
        pass