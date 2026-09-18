from simunetcore import Model
import numpy as np
import math
from scipy.integrate import odeint  

# Model implementation for the reactor
class CSTR(Model):
    def __init__(self, name:str=""):
        Model.__init__(self, name)
        # Model parameters
        self.params = {
            # Parameters Reaction rate
            "E_a"   : {"value": 72750.0, "description": "Activation energy", "unit": "J/mol"},
            "R"     : {"value": 8.314, "description": "Gas constant", "unit": "J/mol/K"},
            "k_0"   : {"value": 1.2e9, "description": "Arrhenius rate constant", "unit": "1/s"},
            "dH_R"  : {"value": -5.0e4, "description": "Enthalpy of reaction", "unit": "J/mol"},
            # Parameters Reactor
            "V_r"   : {"value": 0.1, "description": "Volume", "unit": "m^3"},
            "rho_r" : {"value": 1000.0, "description": "Density", "unit": "kg/m^3"},
            "C_p_r" : {"value": 239.0, "description": "Heat capacity", "unit": "J/kg/K"},
            # Parameters Cooling jacket
            "V_c"   : {"value": 0.020, "description": "Cooling jacket volume", "unit": "m^3"},
            "rho_c" : {"value": 1000.0, "description": "Density", "unit": "kg/m^3"},
            "C_p_c" : {"value": 239.0, "description": "Heat capacity", "unit": "J/kg/K"},
            "UA"    : {"value": 833.3, "description": "Heat transfer", "unit": "J/s/K"},
            # ODE solver parameter
            "abserr": {"value": 1.0e-8, "description": "Absolute tolerance", "unit": "-"},
            "relerr": {"value": 1.0e-6, "description": "Relative tolerance", "unit": "-"}
        }
        # Model variables
        self.vars = {
            "c_A_f" : {"description": "Feed concentration", "unit": "mol/m^3"}, 
            "q_r_f" : {"description": "Reactor feed flow rate", "unit": "m^3/s"},
            "T_r_f" : {"description": "Reactor feed temperature", "unit": "K"},
            "c_A"   : {"description": "Reactor concentration", "unit": "mol/m^3"}, 
            "T_r"   : {"description": "Reactor temperature", "unit": "K"},
            "q_c_f" : {"description": "Cooling feed flow rate", "unit": "m^3/s"},
            "T_c_f" : {"description": "Cooling feed temperature", "unit": "K"},
            "T_c"   : {"description": "Cooling outlet temperature", "unit": "K"}
        }
        # Model inputs
        self.u = {
            "u_1"   : {"type": "liquid", "description": "Reactor feed input", "vars": ["c_A_f", "q_r_f", "T_r_f"]},
            "u_2"   : {"type": "liquid", "description": "Cooling jacket feed input", "vars": ["q_c_f", "T_c_f"]}
        }
        # Model outputs
        self.y = {
            "y_1"   : {"type": "liquid", "description": "Reactor output", "vars": ["c_A", "T_r"]},
            "y_2"   : {"type": "liquid", "description": "Cooling jacket output", "vars": ["T_c"]},
            "y_3"   : {"type": "measure", "description": "Reactor temperatur",  "vars": ["T_r"]}
        }
        # Port adjacencies
        self.adj = [
            ["u_2", "y_2"]
        ]
        
    def compute(self, *args, **kwargs):
        # ODE solver parameter
        abserr = self.get_param("abserr") # Absolute tolerance
        relerr = self.get_param("relerr") # Relative tolerance
        t_frame = self.get_t()
        
        # Create initial vector
        y_0 = [self.get_var("c_A")[-1], self.get_var("T_r")[-1], self.get_var("T_c")[-1]]
        y_sol = odeint(self.odeint_callback, y_0, t_frame, atol=abserr, rtol=relerr)
        
        # Store results
        self.set_var("c_A", y_sol[:,0])
        self.set_var("T_r", y_sol[:,1])
        self.set_var("T_c", y_sol[:,2])

    def odeint_callback(self, y, t):
        # Parameters reaction rate
        E_a    = self.get_param("E_a")   # Activation energy [J/mol]
        R      = self.get_param("R")     # Gas constant [J/mol/K]
        k_0    = self.get_param("k_0")   # Arrhenius rate constant, [1/s]
        dH_R   = self.get_param("dH_R")  # Enthalpy of reaction [J/mol]
        # Parameters reactor
        V_r    = self.get_param("V_r")   # Volume [m³]
        rho_r  = self.get_param("rho_r") # Density [kg/m³]
        C_p_r  = self.get_param("C_p_r") # Heat capacity [J/kg/K]
        # Parameters cooling jacket
        V_c    = self.get_param("V_c")   # Cooling jacket volume [m³]
        rho_c  = self.get_param("rho_c") # Density [kg/m³]
        C_p_c  = self.get_param("C_p_c") # Heat capacity [J/kg/K]
        UA     = self.get_param("UA")    # Heat transfer [J/s/K]    
        
        # State variables
        c_A, T_r, T_c = y
        
        # Coupling vector
        c_A_f = self.get_var("c_A_f", t)
        q_r_f = self.get_var("q_r_f", t)
        T_r_f = self.get_var("T_r_f", t)
        q_c_f = self.get_var("q_c_f", t)
        T_c_f = self.get_var("T_c_f", t)
        # Arrhenius rate expression
        k = lambda T : k_0 * np.exp(-E_a / R / T)

        # Differential equations
        d_c_A = (q_r_f/V_r)*(c_A_f-c_A)-k(T_r)*c_A
        d_T_r = (q_r_f/V_r)*(T_r_f-T_r)+(-dH_R/rho_r/C_p_r)*k(T_r)*c_A+\
                (UA/V_r/rho_r/C_p_r)*(T_c-T_r)
        d_T_c = (q_c_f/V_c)*(T_c_f-T_c)+\
                (UA/V_c/rho_c/C_p_c)*(T_r-T_c)

        dy = [d_c_A, d_T_r, d_T_c]
        return dy 