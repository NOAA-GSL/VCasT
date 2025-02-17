import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from .base_plot import BasePlot
import numpy as np

class LinePlot(BasePlot):
    def __init__(self, config):
        super().__init__(config)

    def setup_plot(self):
        """
        Set up the base line plot.
        """
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.ax.set_title(self.config.plot_title, fontsize=16, fontweight="bold")
        self.ax.set_xlabel(self.config.x_label, fontsize=12)
        self.ax.set_ylabel(self.config.y_label, fontsize=12)

        for i, var in enumerate(self.config.vars):
            var_dict = vars(var)  # Convert ConfigObject to a dictionary
            for var, file in var_dict.items():
        
                # Load data (assuming tab-separated values)
                data = pd.read_csv(file, sep="\t")
                is_date = False
                if "date" in data.columns:
                    is_date = True
                break

        if is_date:
            # Set the x-axis to use date formatting (assumes x-axis values are datetime)
            self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
            self.fig.autofmt_xdate()  # Automatically rotate date labels for readability

        if self.config.ylim:
            self.ax.set_ylim(self.config.ylim)

        # Set y-ticks if provided
        if self.config.yticks:
            self.ax.set_yticks(self.config.yticks)

        if self.config.grid:
            self.ax.grid(True, linestyle="--", alpha=0.6)

    def add_lines(self):
        """
        Add lines to the plot.
        """
        for i, var in enumerate(self.config.vars):
            var_dict = vars(var)  # Convert ConfigObject to a dictionary
            for var, file in var_dict.items():
                # Load data (assuming tab-separated values)
                data = pd.read_csv(file, sep="\t")
    
                # Handle the unique grouping (if applicable)
                if self.config.unique is not None:
                    if self.config.unique in data.columns:
                        values = np.unique(data[self.config.unique])                            
                        if i < len(values):  # Ensure index is within bounds
                            data = data[data[self.config.unique] == values[i-1]]
                        else:
                            raise IndexError(f"Index {i} out of bounds for unique values in {self.config.unique}.")
    
                # Determine x-axis values based on 'date' or 'fcst_lead'
                if "date" in data.columns:
                    dates = pd.to_datetime(data["date"])
                    x_values = mdates.date2num(dates)
                elif "fcst_lead" in data.columns:
                    x_values = pd.to_numeric(data["fcst_lead"], errors="coerce").astype("Int64")
                else:
                    raise ValueError(f"Neither 'date' nor 'fcst_lead' columns found in the file {file}.")

                # Ensure the variable exists in the DataFrame
                if var not in data.columns:
                    raise ValueError(f"Variable '{var}' not found in the file {file}.")
        
                # Extract Y-axis values
                y_values = data[var]

                # Set x-ticks if provided
                if self.config.xticks:
                    custom_xticks = [x_values[i] for i in self.config.xticks if i < len(x_values)]
                    self.ax.set_xticks(custom_xticks)
        
                # Set x-axis limits if provided
                if self.config.xlim:
                    self.ax.set_xlim(x_values[self.config.xlim[0]], x_values[self.config.xlim[1]])

                self.ax.plot(
                    x_values, y_values,
                    color=self.config.line_color[i],
                    marker=self.config.line_marker[i],
                    linestyle=self.config.line_type[i],
                    linewidth=self.config.line_width[i],
                    label=self.config.labels[i]
                )

    def get_x_values(self, data):
        """
        Determine x-axis values based on 'date' or 'fcst_lead'.
        """
        if "date" in data.columns:
            dates = pd.to_datetime(data["date"])
            return mdates.date2num(dates)
        elif "fcst_lead" in data.columns:
            return pd.to_numeric(data["fcst_lead"], errors="coerce").astype("Int64")
        else:
            raise ValueError("No valid x-axis column found.")

    def plot(self):
        self.setup_plot()
        self.add_lines()
        self.finalize_and_save()
