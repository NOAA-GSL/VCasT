import os
import csv
from vcast.stat import AVAILABLE_VARS

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
        self.open_output_file(config.output_dir, config.output_filename, config.stat_name)

    def open_output_file(self, output_dir, output_filename, stat_name):
        """
        Opens the output file for writing.

        Args:
            output_dir (str): Directory where the output file will be saved.
            output_filename (str): Name of the output file.
            stat_name (list): List of statistical variables to include in the header.

        Returns:
            None
        """
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_filename)
        self.output_file = open(output_path, 'w', newline='')
        self.writer = csv.writer(self.output_file, delimiter="\t")

        # Prepare the header row
        header = ["date"]
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

    def close_output_file(self):
        """
        Closes the output file if it is open.
        """
        if self.output_file:
            self.output_file.close()
            self.output_file = None
            self.writer = None
