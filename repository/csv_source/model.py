from simunetcore import Model
import pandas as pd
import numpy as np
import csv

# Model implementation for the CSV Source
class CSVSource(Model):
    def __init__(self, name="", model=None, u_id=None):
        Model.__init__(self, name)
        
        # Model parameters
        self.params = {
            # Parameters csv file
            "csv_file"  : {"value": "", "description": "CSV Source file", "unit": "-"}
        }
        # Model endpoint
        self.site = "local"
        self.threadsafe = True
        
    def compute(self, *args, **kwargs):
        # Parameter csv file
        csv_file = self.get_param("csv_file")
        
        # Set delimiter if not provided
        with open(csv_file, "r") as f:
            # Read csv file
            filedata = f.read()

            # Sniff the csv dialect
            dialect = csv.Sniffer().sniff(filedata)

            # Read csv into dataframe
            f.seek(0)
            df = pd.read_csv(f, delimiter=dialect.delimiter)

            # Set the time column 
            # By default the first column in the dataframe
            t_id = df.columns[0]

            # Handle the vars of the source
            for var_id in self.vars:
                # Interpolate the result
                y = np.interp(self.get_t(), df[t_id], df[var_id])
                # Set results
                self.set_var(var_id, y)
