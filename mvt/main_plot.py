from mvt.plot_class import *
import argparse

def main_plot():

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('config_file', type=str, help="Path to YAML file")
    args = parser.parse_args()

    plot = Plot(args.config_file)
    plot.plot()

if __name__ == '__main__':
    main_plot()