import os
import csv
from vcast.stat import AVAILABLE_VARS

class OutputFileHandler:
    """
    Handles opening, writing, and closing an output file.
    """

    def __init__(self, config):
        from vcast.io import Preprocessor
        """
        Initializes the OutputFileHandler and opens the output file.

        Args:
            config (ConfigLoader): Configuration object containing output parameters.
        """
        self.output_file = None
        self.writer = None

        self.config = Preprocessor.validate_config(config,"stat")

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
        header = ["date", "fcst_lead"]
        
        if ens:
            header += ["model"]

        for stat in stat_name:
            stat_lower = stat.lower()
            if stat_lower in AVAILABLE_VARS:
                if stat_lower == "quantiles":
                    header += ["25p", "50p", "75p", "IQR", "LW", "UW"]
                else:
                    header.append(stat_lower)

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
