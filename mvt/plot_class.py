import yaml
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

class Plot:
    def __init__(self, config_file):
        """
        Initialize the Plot class with a YAML configuration file.
        """
        with open(config_file, 'r') as file:
            self.config = yaml.safe_load(file)

        self.plot_type = self.config.get("plot_type", "performance_diagram")
        self.title = self.config.get("plot_title", "Default Plot")
        self.legend_title = self.config.get("legend_title", "Legend")
        self.output_file = self.config.get("output_filename", "output.png")
        self.input_files = self.config.get("input_files", [])
        self.labels = self.config.get("labels", [])
        self.colors = self.config.get("line_color", [])
        self.markers = self.config.get("line_marker", [])
        self.line_styles = self.config.get("line_type", [])
        self.line_widths = self.config.get("line_width", [])
        self.var_name = self.config.get("var_name", "RMSE")
        self.date_col = "DATE"
        self.y_label = self.config.get("y_label", "Value")
        self.reference_std = self.config.get("reference_std", 2)

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
            self.input_files, self.labels, self.colors, self.markers, self.line_styles, self.line_widths
        ):
            df = pd.read_csv(file)
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
        for file in self.input_files:
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
        for file, label, color, marker in zip(self.input_files, self.labels, self.colors, self.markers):
            df = pd.read_csv(file)

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


    def finalize_and_save_plot(self):
        """
        Finalize and save the plot.
        """
        self.ax.legend(loc='lower right', title=self.legend_title, fontsize='medium', shadow=True)
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
        else:
            print("Invalid plot type. Please specify 'performance_diagram'.")
            return

        self.finalize_and_save_plot()
