from simunetcore import Model

# Model implementation for the 2-level controller
class TwoLevelController(Model):
    def __init__(self, name=""):
        Model.__init__(self, name)
        # Model parameters
        self.params = {
            "y_range" : {"value": [4.0, 20.0], "description": "Range of controller output", "unit": "mA"},
            "hysteresis" : {"value": 0.1, "description": "Switch hysteresis", "unit": "mA"},
            "delta_t" : {"value": 0.0, "description": "Time intervall", "unit": "s"}
        }
        # Model variables
        self.vars = {
            "p_v" : {"description": "Process value", "unit": "mA"}, 
            "m_v" : {"description": "Manipulated value", "unit": "mA"},
            "s_p" : {"description": "Set Point", "unit": "mA"}
        }
        # Model inputs
        self.u = {
            "u_1" : {"type": "signal", "description": "Instrument input", "vars": ["p_v"]},
            "u_2" : {"type": "signal", "description": "Set Point input", "vars": ["s_p"]}
        }
        # Model outputs
        self.y = {
            "y_1" : {"type": "control", "description": "Controller output", "vars": ["m_v"]}
        }
        self.__t_last = 0
        
    def compute(self, *args, **kwargs):
         # Parameters
        y_min, y_max = self.get_param("y_range")
        hysteresis = self.get_param("hysteresis")
        delta_t = self.get_param("delta_t")
        t_frame = self.get_t()
        
        # Create python list to log results
        result = []

        # Get inital manipulated value
        m_v = self.get_var("m_v")[-1]

        for i in range(len(t_frame)):
            # Append current manipulated to the result
            result.append(m_v)

            # Get time step
            t = t_frame[i]
            
            # Evaluate only after time intervall (delta_t)
            if t >= self.__t_last + delta_t or delta_t == 0:
                # Get set point and process value for the time step
                s_p = self.get_var("s_p", t) 
                p_v = self.get_var("p_v", t)

                # Error calculations
                err = s_p - p_v

                # Three level control calculations
                if err < - hysteresis/2.0:
                    m_v = y_min
                elif err > hysteresis/2.0:
                    m_v = y_max
                    
                # Increment __t_last    
                self.__t_last += delta_t
                
        # Return result array
        self.set_var("m_v", result)     