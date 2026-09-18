"""Export simulation result data to Excel workbook files."""

import pandas as pd
import json
import numpy as np


def export_excel(result, filename):
    """Write simulation result data into an Excel file.

    Args:
        result: Dictionary containing simulation result data.
        filename: Path to the output Excel file.
    """

    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        # Build metadata table and initialize worksheet counter
        meta_columns = ["sheet", "name", "id", "description"]
        meta_data = []
        i = 0

        # Loop all models 
        for model_key in result:
            # retrieve model data
            model_data = result[model_key]
            
            # Retrieve name, description and time line
            model_name = model_data["name"]
            model_description= model_data["description"]
            t = model_data["t"]

            # Append meta data
            meta_data.append([i, model_name, model_key, model_description])

            # Create columns list
            columns = ["t"] 
            # Create the nested data list
            data = [t]
            
            # Loop all vars for the current model
            for var_key in model_data["vars"].keys():
                # Retrieve the values and the unit from the var list
                values = model_data["vars"][var_key]["value"]
                unit = model_data["vars"][var_key]["unit"]

                # Append column key
                columns.append("{} [{}]".format(var_key, unit))
                
                # If lengths are matching append the values directly
                if len(values) == len(t):
                    data.append(values)
                # Otherwise create an empty numpy array, fill it up and append it
                else:
                    val_array = np.empty(len(t))
                    val_array.fill(np.nan)
                    val_array[0:len(values)] = values
                    data.append(val_array)

            # Create a dataframe
            df = pd.DataFrame(np.array(data).T, columns=columns)
            # Export it using the excel writer
            df.to_excel(writer, sheet_name=str(i), index=False)
            i += 1

        # Create a dataframe from meta data
        df = pd.DataFrame(meta_data, columns=meta_columns)
        # Finally write legend
        df.to_excel(writer, sheet_name="meta", index=False)

if __name__ == "__main__":
    project_file = "./projects/cstr.sim"
    output_file = "./test1.xlsx"

    # Load result
    with open(project_file, "r") as f:
        project = json.load(f)
    # Export to excel
    export_excel(project["result"], output_file)