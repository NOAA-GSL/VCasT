import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
from vcast.io import ConfigLoader

class Plot:
    def __init__(self, config_file):
        """
        Initialize the Plot class with a YAML configuration file.
        """
        config = ConfigLoader(config_file)

        self.plot_type = config.plot_type
        self.title = config.plot_title
        self.legend_title = config.legend_title
        self.output_file = config.output_filename
        self.vars_dict = config.vars
        self.unique = config.unique  
        self.labels = config.labels
        self.colors = config.line_color
        self.markers = config.line_marker
        self.line_styles = config.line_type
        self.line_widths = config.line_width
        self.date_col = "date"
        self.x_label = config.x_label
        self.y_label = config.y_label
        self.xlim = config.xlim
        self.ylim = config.ylim
        self.grid = config.grid
        self.yticks = config.yticks
        self.xticks = config.xticks

        # Ensure the vars dictionary is formatted correctly
        # if not isinstance(self.vars_dict, list) or not all(isinstance(item, dict) for item in self.vars_dict):
        #     raise ValueError("Invalid format for 'vars' in YAML. Expected a list of dictionaries.")

        # Check that all lists are of the same length
        num_files = len(self.vars_dict)
        if not (len(self.labels) == len(self.colors) == len(self.markers) == len(self.line_styles) == len(self.line_widths) == num_files):
            # Debugging: Print all relevant variables
            print("Labels:", self.labels)
            print("Colors:", self.colors)
            print("Markers:", self.markers)
            print("Line Styles:", self.line_styles)
            print("Line Widths:", self.line_widths)
            print("Number of Files:", num_files)

            raise ValueError("Mismatch in number of input files and line properties in YAML configuration.")

    def setup_performance_diagram(self):
        """
        Set up the base grid for the Performance Diagram.
        """
        x = np.linspace(0.01, 1, 100)
        y = np.linspace(0.01, 1, 100)
        X, Y = np.meshgrid(x, y)
        CSI_levels = [0.1, 0.25, 0.5, 0.6, 0.75, 1.0]
        CSI = (X * Y) / (X + Y - X * Y)
    
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
    
        # Shade CSI regions with different gray levels
        shades = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4]  # Shades for CSI levels
        for i, level in enumerate(CSI_levels[:-1]):
            self.ax.contourf(
                X, Y, CSI, levels=[level, CSI_levels[i + 1]], colors=[str(shades[i])], alpha=0.8
            )
    
        # Plot CSI contour lines
        contour = self.ax.contour(X, Y, CSI, levels=CSI_levels, colors="black", linestyles="solid")
        self.ax.clabel(contour, fmt="%.2f", inline=True, fontsize=10, colors="black")
        self.ax.text(1.05, 0.5, "CSI Curves", rotation=270, fontsize=12, va="center", color="black")
    
        # Add frequency bias (FBIAS) lines
        FB_values = [0.1, 0.25, 0.5, 1, 2, 4, 10]
        for FB in FB_values:
            fb_y = np.minimum(1, FB * x)
            self.ax.plot(x, fb_y, linestyle="--", color="black", linewidth=0.8)
    
            # Add value labels for FBIAS lines at the end
            end_x = x[np.where(fb_y < 1)[0][-1]]  # The last valid x-coordinate
            end_y = fb_y[np.where(fb_y < 1)[0][-1]]  # The corresponding y-coordinate
            self.ax.text(
                end_x + 0.02, end_y, f"{FB:.1f}", fontsize=10, color="black", ha="left", va="center"
            )
    
        # Add plot title and labels
        self.ax.set_title(self.title, fontsize=16)
        self.ax.set_xlabel("Success Ratio (1 - FAR)", fontsize=12)
        self.ax.set_ylabel("Probability of Detection (POD)", fontsize=12)
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.grid(True, linestyle="--", alpha=0.5)


    def add_to_performance_diagram(self):
        """
        Add data from files to the Performance Diagram.
        """
        for file, label, color, marker, line_style, line_width in zip(
            self.vars, self.labels, self.colors, self.markers, self.line_styles, self.line_widths
        ):
            df = pd.read_csv(file,sep="\t")
            df = df.dropna(subset=['POD', 'SR', 'CSI', 'FBIAS'])
            self.ax.plot(
                df['SR'], df['POD'], label=label, color=color, marker=marker,
                linestyle=line_style, linewidth=line_width, alpha=0.8
            )

    def setup_taylor_diagram(self):
        """
        Set up the base grid for the Taylor Diagram (first quarter only).
        """
        self.fig = plt.figure(figsize=(8, 8))
        self.ax = self.fig.add_subplot(111, polar=True)
        self.get_std_max()

        # Set up polar axes for the first quarter
        self.ax.set_theta_direction(1)  # Clockwise direction
        self.ax.set_theta_offset(0)  # Start at 0 degrees for correlation of 0

        # Correlation grid (dotted blue lines) and ticks
        corr_ticks = np.linspace(0.0, 1.0, 11)  # Correlation from 0 to 1 with 0.1 step
        corr_angles = np.arccos(corr_ticks)  # Convert correlation to angles
        self.ax.set_xticks(corr_angles)
        self.ax.set_xticklabels([f"{corr:.1f}" for corr in corr_ticks], fontsize=10)

        # Add dotted blue lines for correlation grid
        for angle in corr_angles:
            self.ax.plot([angle, angle], [0, self.std_max + 0.5], linestyle='--', color='lightblue', alpha=0.7, linewidth=0.6)

        # Standard deviation arcs
        stddev_arcs = np.arange(0.5, self.std_max + 0.6, 0.5)
        for std in stddev_arcs:
            t = np.linspace(0, np.pi / 2, 100)
            r = np.full_like(t, std)
            self.ax.plot(t, r, linestyle='--', color='lightblue', alpha=0.7, linewidth=0.6)

        # Add markers for every 0.05 correlation at the plot limit
        corr_markers = np.linspace(0.0, 0.99, 100)  # Correlation from 0 to 1 with 0.05 step
        corr_marker_angles = np.arccos(corr_markers)
        plot_limit = self.std_max # Get the maximum radius of the plot
        for angle in corr_marker_angles:
            self.ax.plot(
                [angle, angle], 
                [plot_limit - 0.05, plot_limit],  # Place markers exactly at the plot limit
                color='black', alpha=1, linewidth=1.2
            )

        corr_markers = np.linspace(0.0, 0.95, 20)  # Correlation from 0 to 1 with 0.05 step
        corr_marker_angles = np.arccos(corr_markers)
        plot_limit = self.std_max # Get the maximum radius of the plot
        for angle in corr_marker_angles:
            self.ax.plot(
                [angle, angle], 
                [plot_limit - 0.1, plot_limit],  # Place markers exactly at the plot limit
                color='black', alpha=1, linewidth=1.2
            )

        corr_markers = np.linspace(0.0, 0.9, 10)  # Correlation from 0 to 1 with 0.05 step
        corr_marker_angles = np.arccos(corr_markers)
        plot_limit = self.std_max  # Get the maximum radius of the plot
        for angle in corr_marker_angles:
            self.ax.plot(
                [angle, angle], 
                [plot_limit - 0.15, plot_limit],  # Place markers exactly at the plot limit
                color='black', alpha=1, linewidth=1.2
            )

        # Add labels for standard deviation and correlation
        self.ax.text(np.pi / 4, self.std_max * 1.1, "Correlation", fontsize=12, ha="center", va="center", rotation=-45)
        self.ax.text(0, self.std_max / 2, "Standard Deviation", fontsize=12, ha="center", va="center", transform=self.ax.transData + plt.matplotlib.transforms.ScaledTranslation(0, -0.45, self.fig.dpi_scale_trans))
        self.ax.text(0, 0, "Standard Deviation", fontsize=12, ha="center", va="center", rotation = 90, transform=self.ax.transData + plt.matplotlib.transforms.ScaledTranslation(-0.45, self.std_max / 2 + 1.2, self.fig.dpi_scale_trans))

        # Title for the plot
        self.ax.set_title(self.title, fontsize=16, pad=20)

        # Limit the angular range to the first quarter
        self.ax.set_thetamin(0)   # 0 degrees
        self.ax.set_thetamax(90)  # 90 degrees
        self.ax.grid(False)  # Disable the grid lines

    def get_std_max(self):

        std_max = 0
        for file in self.vars:
            df = pd.read_csv(file)

            # Extract standard deviation and correlation from the file
            stddev = df['STDEV'].values

            if np.max(stddev) > std_max:
                std_max = np.max(stddev)

        self.std_max = std_max


    def add_to_taylor_diagram(self):
        """
        Add data from input files to the Taylor Diagram.
        """
        for file, label, color, marker in zip(self.vars, self.labels, self.colors, self.markers):
            df = pd.read_csv(file,sep="\t")

            # Extract standard deviation and correlation from the file
            stddev = df['STDEV'].values
            correlation = df['CORR'].values            

            # Convert correlation to polar angles
            angles = np.arccos(correlation)

            # Plot the points on the Taylor Diagram
            self.ax.scatter(angles, stddev, label=label, color=color, marker=marker, s=20)

            self.ax.set_rmax(self.std_max)

            # Get the ticks automatically set on the horizontal axis
            stddev_ticks = self.ax.get_yticks()[:-1]
            
            # Vertical axis (top side)
            for std in stddev_ticks:
                if std > 0:  # Avoid placing a tick at zero if unnecessary
                    self.ax.text(
                        np.pi / 2, std, f"{std}", ha="center", va="center",
                        transform=self.ax.transData + plt.matplotlib.transforms.ScaledTranslation(-0.15, 0, self.fig.dpi_scale_trans)
                    )

    def setup_line_plot(self):
        """
        Prepares an XY plot using parameters from a YAML configuration file.
        Does not draw the lines—just sets up the figure, axes, labels, and axis limits/ticks.
        """
        try:
            # Create figure and axis
            self.fig, self.ax = plt.subplots(figsize=(10, 8))
    
            # Set title and labels
            self.ax.set_title(self.title, fontsize=14)
            self.ax.set_xlabel(self.x_label, fontsize=12)
            self.ax.set_ylabel(self.y_label, fontsize=12)
    
            for i, var_dict in enumerate(self.vars_dict):
                var_dict_as_dict = vars(var_dict)  # Convert ConfigObject to a dictionary
                for var, file in var_dict_as_dict.items():
            
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
    
            if hasattr(self, "ylim") and self.ylim:
                self.ax.set_ylim(self.ylim)
    
            # Set y-ticks if provided
            if hasattr(self, "yticks") and self.yticks:
                self.ax.set_yticks(self.yticks)
   
            # Enable grid if requested
            if hasattr(self, "grid") and self.grid:
                self.ax.grid(True, linestyle="--", alpha=0.6)
    
        except Exception as e:
            raise RuntimeError(f"Error in `setup_line_plot`: {str(e)}")

    def add_lines_to_plot(self):
        """
        Adds lines to the provided Matplotlib axis object based on YAML configuration.
        """
        try:

            # Loop through each variable and its associated file
            for i, var_dict in enumerate(self.vars_dict):
                var_dict_as_dict = vars(var_dict)  # Convert ConfigObject to a dictionary
                for var, file in var_dict_as_dict.items():
            
                    # Load data (assuming tab-separated values)
                    data = pd.read_csv(file, sep="\t")
        
                    # Handle the unique grouping (if applicable)
                    if self.unique is not None:
                        if self.unique in data.columns:
                            values = np.unique(data[self.unique])                            
                            if i < len(values):  # Ensure index is within bounds
                                data = data[data[self.unique] == values[i-1]]
                            else:
                                raise IndexError(f"Index {i} out of bounds for unique values in {self.unique}.")
        
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
                    if hasattr(self, "xticks") and self.xticks:
                        custom_xticks = [x_values[i] for i in self.xticks if i < len(x_values)]
                        self.ax.set_xticks(custom_xticks)
        
                    # Set x-axis limits if provided
                    if hasattr(self, "xlim") and self.xlim:
                        self.ax.set_xlim(x_values[self.xlim[0]], x_values[self.xlim[1]])
        
                    # Plot the line
                    self.ax.plot(
                        x_values, y_values,
                        color=self.colors[i],
                        marker=self.markers[i],
                        linestyle=self.line_styles[i],
                        linewidth=self.line_widths[i],
                        label=f"{self.labels[i]}"
                    )
    
        except Exception as e:
            raise RuntimeError(f"Error in `add_lines_to_plot`: {str(e)}")



    def finalize_and_save_plot(self):
        """
        Finalize and save the plot.
        """
        self.ax.legend(title=self.legend_title, fontsize='medium', shadow=True)
        plt.savefig(self.output_file, bbox_inches='tight')
        plt.close()
        print(f"Plot saved to {self.output_file}")

    def plot(self):
        """
        Generate the plot based on the configuration.
        """
        if self.plot_type == "performance_diagram":
            self.setup_performance_diagram()
            self.add_to_performance_diagram()
        elif self.plot_type == "taylor_diagram":
            self.setup_taylor_diagram()
            self.add_to_taylor_diagram()            
        elif self.plot_type == "line":
            self.setup_line_plot()
            self.add_lines_to_plot()
        else:
            print("Invalid plot type. Please specify 'performance_diagram, taylor_diagram or line'.")
            return

        self.finalize_and_save_plot()
