from simunetcore import Model

# Model implementation for the Tank
class PIDController(Model):
    def __init__(self, name=""):
        Model.__init__(self, name)

        # Model Parameters
        self.params = {
             "y_range": {
                "value": [4.0, 20.0],
                "description": "Range of controller output",
                "unit": "mA",
            },
            "k_p": {
                "value": 12,
                "description": "Proportional control gain",
                "unit": "-",
            },
            "k_i": {
                "value": 0.9, 
                "description": "Integral control gain", 
                "unit": "-"
            },
            "k_d": {
                "value": 20.0,
                "description": "Derivative control gain",
                "unit": "-",
            },
            "beta": {
                "value": 1.0,
                "description": "Setpoint weighting for proportional control",
                "unit": "-",
            },
            "gamma": {
                "value": 1.0,
                "description": "Setpoint weighting for derivative control",
                "unit": "-",
            },
            "mode": {
                "value": 1.0, 
                "description": "Mode of operation", 
                "unit": ""
            },
            "delta_t" : {
                "value": 0.0, 
                "description": "Time intervall", 
                "unit": "s"
            }
        }
        # Model variables
        self.vars = {
            "p_v": {"description": "Process value", "unit": "mA"},
            "m_v": {"description": "Manipulated value", "unit": "mA"},
            "s_p": {"description": "Set Point", "unit": "mA"},
        }
        # Model inputs
        self.u = {
            "u_1": {
                "type": "signal",
                "description": "Instrument input",
                "vars": ["p_v"],
            },
            "u_2": {
                "type": "signal",
                "description": "Set Point input",
                "vars": ["s_p"],
            },
        }
        # Model outputs
        self.y = {
            "y_1": {
                "type": "control",
                "description": "Controller output",
                "vars": ["m_v"],
            }
        }
        self.__eP = None
        self.__eP1 = None
        self.__eI = None
        self.__eD = None
        self.__eD1 = None
        self.__eD2 = None
        self.__t_last = 0

    def reset(self):
        self.__eP = None
        self.__eP1 = None
        self.__eI = None
        self.__eD = None
        self.__eD1 = None
        self.__eD2 = None

    def compute(self, *args, **kwargs):
        # Parameter
        y_min, y_max = self.get_param("y_range")
        k_p = self.get_param("k_p")
        k_i = self.get_param("k_i")
        k_d = self.get_param("k_d")
        beta = self.get_param("beta")
        gamma = self.get_param("gamma")
        delta_t = self.get_param("delta_t")
        t_frame = self.get_t()

        if self.get_param("mode") == "direct":
            mode = 1.0
        elif self.get_param("mode") == "inverse":
            mode = -1.0
        else:
            raise AttributeError("mode")

        # Create python list to log results
        result = []

        # Get inital values set point, process value and  manipulated value
        s_p = self.get_var("s_p", t_frame[0])
        p_v = self.get_var("p_v", t_frame[0])
        m_v = self.get_var("m_v")[-1]

        # Set the inital errors in the first run
        if self.__eP1 is None:
            self.__eP1 = beta * s_p - p_v
        if self.__eD1 is None:
            self.__eD1 = gamma * s_p - p_v
        if self.__eD2 is None:
            self.__eD2 = gamma * s_p - p_v

        # Compute dt (assume equidistant stepsize)
        if delta_t == 0:
            dt = (t_frame[-1] - t_frame[0]) / (len(t_frame) - 1)
        else:
            dt = delta_t

        for i in range(len(t_frame)):
            # Append current manipulated to the result
            result.append(m_v)

            # Get time step
            t = t_frame[i]

            # Evaluate only after time intervall (delta_t)
            if t >= self.__t_last + delta_t or delta_t == 0:
                # Get set point and processvalue for the time step
                s_p = self.get_var("s_p", t)
                p_v = self.get_var("p_v", t)

                # Error calculations
                self.__eP = beta * s_p - p_v
                self.__eI = s_p - p_v
                self.__eD = gamma * s_p - p_v

                # PID control calculations
                dy = k_p * (self.__eP - self.__eP1)
                dy += k_i * dt * self.__eI
                dy += k_d * (self.__eD - 2 * self.__eD1 + self.__eD2) / dt

                # Update and saturate manipulatedd value
                m_v -= mode * dy
                m_v = max(y_min, min(y_max, m_v))

                # Save data for the next iteration
                self.__eD2 = self.__eD1
                self.__eD1 = self.__eD
                self.__eP1 = self.__eP
                
                # Increment __t_last    
                self.__t_last += dt

        # Return result array
        self.set_var("m_v", result)