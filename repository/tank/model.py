from simunetcore import Model
from scipy.integrate import odeint  

# Model implementation for the Tank
class Tank(Model):
    def __init__(self, name:str=""):
        Model.__init__(self, name)
        # Model parameters
        self.params = {
            # Tank properties
            "V_s" : {"value": 0.05, "description": "Tank Volume", "unit": "m³"},
            # ODE solver parameter
            "abserr" : {"value": 1.0e-8, "description": "Absolute tolerance", "unit": "-"},
            "relerr" : {"value": 1.0e-6, "description": "Relative tolerance", "unit": "-"}
        }      
        # Model variables
        self.vars = {
            "q_s_f" : {"description": "Feed flow Rate", "unit": "m^3/s"}, 
            "T_s_f" : {"description": "Feed temperature", "unit": "K"}, 
            "T_s" : {"description": "Outlet temperature", "unit": "K"}
        }
        # Model inputs
        self.u = {
            "u_1" : {"type": "liquid", "description": "Tank feed input", "vars": ["q_s_f", "T_s_f"]}
        }
        # Model outputs
        self.y = {
            "y_1" : {"type": "liquid", "description": "Tank output", "vars": ["T_s"]}
        }
             
    def compute(self, *args, **kwargs):
        # ODE solver parameter
        abserr = self.get_param("abserr") # Absolute tolerance
        relerr = self.get_param("relerr") # Relative tolerance
        t_frame = self.get_t()        

        # Create initial vector
        y_0 = self.get_var("T_s")[-1]
        
        # Solve model
        y_sol = odeint(self.odeint_callback, y_0, t_frame, atol=abserr, rtol=relerr)
        
        # Store results
        self.set_var("T_s", y_sol[:,0])
            
    def odeint_callback(self, y, t):
        # Parameters Tank
        V_s = self.get_param("V_s") # Volume [m³]

        # State variables
        T_s = y
        
        # Coupling vector
        q_s_f = self.get_var("q_s_f", t)
        T_s_f = self.get_var("T_s_f", t)

        # Differential equation
        d_T_s = (q_s_f/V_s)*(T_s_f-T_s)
        dy = d_T_s
        
        return dy