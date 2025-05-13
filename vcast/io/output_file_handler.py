import os
import csv

class OutputFileHandler:
    """
    Handles opening, writing, and closing an output file.
    """

    def __init__(self, config):
        """
        Initializes the OutputFileHandler and opens the output file.

        Args:
            config (ConfigLoader): Configuration object containing output parameters.
        """
        self.output_file = None
        self.writer = None

        self.config = config

        self.open_output_file()

    def open_output_file(self):
        """
        Opens the output file for writing.

        Args:
            output_dir (str): Directory where the output file will be saved.
            output_filename (str): Name of the output file.
            stat_name (list): List of statistical variables to include in the header.

        Returns:
            None
        """
        
        output_dir = self.config.output_dir
        output_filename = self.config.output_filename
        stat_name = self.config.stat_name
        ens = self.config.cmem

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_filename)
        self.output_file = open(output_path, 'w', newline='')
        self.writer = csv.writer(self.output_file, delimiter="\t")

        # Prepare the header row
        header = ["date", "fcst_lead", "fcst_var", "level"]
        
        if ens:
            header += ["model"]

        for stat in stat_name:
            stat_lower, p1, p2, p3 = OutputFileHandler.parse_metric_string(stat.lower())
            if stat_lower == "quantiles":
                header += ["25p", "50p", "75p", "IQR", "LW", "UW"]
            else:
                ss = ""
                if p1 is not None:
                    ss += f":{p1}"

                if p2 is not None:
                    ss += f":{p2}"
                
                if p3 is not None:
                    ss += f":{p3}"

                fstat = f"{stat_lower}{ss}"
                header.append(fstat)

        self.write_to_output_file(header)  # Write header row

    def write_to_output_file(self, row):
        """
        Writes a row to the output file.

        Args:
            row (list): List representing a row to write.
        """
        if self.writer is None:
            raise ValueError("Output file is not open. Ensure open_output_file() was called successfully.")
        self.writer.writerow(row)
        self.output_file.flush()

    def close_output_file(self):
        """
        Closes the output file if it is open.
        """
        if self.output_file:
            self.output_file.close()
            self.output_file = None
            self.writer = None
    
    @staticmethod
    def parse_metric_string(var_string):
        """
        Parse a metric specifier of the form:
            "metric"             → returns (metric, None, None)
            "metric:thresh"      → returns (metric, float(thresh), None)
            "metric:thresh:rad"  → returns (metric, float(thresh), int(rad))
    
        Raises ValueError if the format isn't recognized.
        """
        parts = var_string.split(":")
        metric = parts[0]
    
        # no extra args
        if len(parts) == 1:
            return metric, None, None, None
    
        # one extra arg  → threshold
        if len(parts) == 2:
            return metric, float(parts[1]), None, None
    
        # two extra args → threshold and radius
        if len(parts) == 3:
            return metric, float(parts[1]), float(parts[2]), None
        
        if len(parts) == 4:
            return metric, float(parts[1]), float(parts[2]), float(parts[3])
    
        raise ValueError(f"Invalid metric specifier: '{var_string}'")
