from simunetcore import Model
import numpy as np
import math
from scipy.integrate import odeint  

# Model implementation for the Heatexchanger
class HeatExchanger(Model):
    
    def __init__(self, name:str=""):
        Model.__init__(self, name)
        # Model parameters
        self.params = {
            # Parameters inner pipe
            "r_1"   : {"value": 0.025, "description": "Inner pipe radius", "unit": "m"},
            "C_p_1" : {"value": 239.0, "description": "Heat capacity of inner fluid", "unit": "J/kg/K"},
            "rho_1" : {"value": 1000.0, "description": "Densitiy of inner fluid", "unit": "kg/m^3"},
            # Parameters outer pipe
            "r_2"   : {"value": 0.05, "description": "Outer pipe radius", "unit": "m"},
            "C_p_2" : {"value": 239.0, "description": "Heat capacity of outer fluid", "unit": "J/kg/K"},
            "rho_2" : {"value": 1000.0, "description": "Densitiy of outer fluid", "unit": "kg/m^3"},
            # Parameters heatexchanger
            "L"     : {"value": 30.0, "description": "Pipe length", "unit": "m"},
            "z"     : {"value": 25, "description": "Number of cells", "unit": "-"},
            "U"     : {"value": 340.0, "description": "Heat transfer coefficient", "unit": "W/m^2/K"},         
            "mode"  : {"value": "cocurrent", "description": "Mode of operation (countercurrent, cocurrent)", "unit": "-", }, 
            # ODE solver parameter
            "abserr": {"value": 1.0e-8, "description": "Absolute tolerance", "unit": "-"},
            "relerr": {"value": 1.0e-6, "description": "Relative tolerance", "unit": "-"}
        }
        # Model variables
        self.vars = {
            "q_1_f" : {"description": "Feed flow rate inner pipe", "unit": "m^3/s"}, 
            "T_1_f" : {"description": "Feed temperature inner pipe", "unit": "K"}, 
            "T_1_o" : {"description": "Outlet Temp. inner pipe", "unit": "K"}, 
            "T_1"   : {"description": "Temperature inner pipe", "unit": "K"}, 
            "q_2_f" : {"description": "Feed flow rate outer pipe", "unit": "m^3/s"},
            "T_2_f" : {"description": "Feed temperature outer pipe", "unit": "K"},
            "T_2_o" : {"description": "Outlet Temp. outer pipe", "unit": "K"},
            "T_2"   : {"description": "Temperature outer pipe", "unit": "K"}
        }
        # Model inputs
        self.u = {
            "u_1"   : {"type": "liquid", "description": "Inner pipe feed input", "vars": ["q_1_f", "T_1_f"]},
            "u_2"   : {"type": "liquid", "description": "Outer pipe feed input", "vars": ["q_2_f", "T_2_f"]}
        }
        # Model outputs
        self.y = {
            "y_1"   : {"type": "liquid", "description": "Inner pipe output", "vars": ["T_1_o"]},
            "y_2"   : {"type": "liquid", "description": "Outer pipe output", "vars": ["T_2_o"]}
        }
        # Port adjacencies
        self.adj = [
            ["u_1", "y_1"],
            ["u_2", "y_2"]
        ]
        
    def compute(self, *args, **kwargs):
        # ODE solver parameter
        abserr = self.get_param("abserr") # Absolute tolerance
        relerr = self.get_param("relerr") # Relative tolerance
        t_frame = self.get_t()            # time frame
        z = self.get_param("z")           # Number of cells
        mode = self.get_param("mode")     # Mode of operation (0=countercurrent, 1=cocurrent)
       
        # Create initial vector
        y_0 = np.zeros(2*z)
        T_1 = self.get_var("T_1")
        T_2 = self.get_var("T_2")
        if len(T_1) == 1:
            T_1 = np.full(z, T_1[0])
        if len(T_2) == 1:
            T_2 = np.full(z, T_2[0])
            
        y_0[0:z] = T_1
        y_0[z:2*z] = T_2
        y_sol = odeint(self.odeint_callback, y_0, t_frame, atol=abserr, rtol=relerr)
        
        # Store results
        self.set_var("T_1", y_sol[-1,0:z])
        self.set_var("T_2", y_sol[-1,z:2*z])
        self.set_var("T_1_o", y_sol[:,0] if mode == 0 else y_sol[:,z-1])
        self.set_var("T_2_o", y_sol[:,2*z-1])
 
    def odeint_callback(self, y, t):
        # Parameters inner pipe
        r_1   = self.get_param("r_1")   # inner pipe radius [m]
        C_p_1 = self.get_param("C_p_1") # heat capacity of inner fluid [J/kg/K]
        rho_1 = self.get_param("rho_1") # densitiy of inner fluid [kg/m³]
        A_1   = math.pi*r_1**2          # cross sectional areas of inner pipe [m²]
        # Parameters outer pipe
        r_2   = self.get_param("r_2")   # outer pipe radius [m]
        C_p_2 = self.get_param("C_p_2") # heat capacity of inner fluid [J/kg/K]
        rho_2 = self.get_param("rho_2") # densitiy of outer fluid [kg/m³]
        A_2   = math.pi*r_2**2-A_1      # cross sectional areas of outer pipe [m²]    
        # Parameters heatexchanger
        L     = self.get_param("L")     # pipe length [m]
        z     = self.get_param("z")     # number of cells [-]
        U     = self.get_param("U")     # overall heat transfer coefficient [W/m²/K]
        mode  = self.get_param("mode")  # Mode of operation (0=countercurrent, 1=cocurrent) [-]
        dx    = L/z                     # node width [m]
        A     = 2.0*math.pi*r_1*dx      # heat exchange area between inner and outer pipe# inner pipe
        
        # State variables
        T_1 = y[0:z]
        T_2 = y[z:2*z]
        dy = np.zeros(2*z)
        
        # Coupling vector
        q_1_f = self.get_var("q_1_f", t)
        T_1_f = self.get_var("T_1_f", t)
        q_2_f = self.get_var("q_2_f", t)
        T_2_f = self.get_var("T_2_f", t)
       
        # Differential equations
        if mode == "countercurrent":
            # Counter current heatexchanger inner pipe
            dy[0:z-1] = (q_1_f*rho_1*C_p_1*(T_1[1:z]-T_1[0:z-1]) + U*A*(T_2[0:z-1]-T_1[0:z-1])) / (rho_1*C_p_1*dx*A_1)
            dy[z-1] = (q_1_f*rho_1*C_p_1*(T_1_f-T_1[z-1]) + U*A*(T_2[z-1]-T_1[z-1])) / (rho_1*C_p_1*dx*A_1)

            # Counter current heatexchanger outer pipe
            dy[z+1:2*z] = (q_2_f*rho_2*C_p_2*(T_2[0:z-1]-T_2[1:z]) - U*A*(T_2[1:z]-T_1[1:z])) / (rho_2*C_p_2*dx*A_2)
            dy[z] = (q_2_f*rho_2*C_p_2*(T_2_f-T_2[0]) - U*A*(T_2[0]-T_1[0])) / (rho_2*C_p_2*dx*A_2)

        elif mode == "cocurrent":
            # Cocurrent heatexchanger inner pipe
            dy[1:z] = (q_1_f*rho_1*C_p_1*(T_1[0:z-1]-T_1[1:z]) + U*A*(T_2[1:z]-T_1[1:z])) / (rho_1*C_p_1*dx*A_1)
            dy[0] = (q_1_f*rho_1*C_p_1*(T_1_f-T_1[0]) + U*A*(T_2[0]-T_1[0])) / (rho_1*C_p_1*dx*A_1)

            # Cocurrent heatexchanger outer pipe
            dy[z+1:2*z] = (q_2_f*rho_2*C_p_2*(T_2[0:z-1]-T_2[1:z]) - U*A*(T_2[1:z]-T_1[1:z])) / (rho_2*C_p_2*dx*A_2)
            dy[z] = (q_2_f*rho_2*C_p_2*(T_2_f-T_2[0]) - U*A*(T_2[0]-T_1[0])) / (rho_2*C_p_2*dx*A_2)
        else:
            raise AttributeError("mode")
        return dy    