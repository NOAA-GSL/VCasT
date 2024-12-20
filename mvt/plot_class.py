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
        else:
            print("Invalid plot type. Please specify 'performance_diagram'.")
            return

        self.finalize_and_save_plot()
