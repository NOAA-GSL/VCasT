
import argparse
from mvt.stat_handler import *

def main_conv():

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('file', type=str, help="Path to file")
    args = parser.parse_args()

    file_path = args.file

    rs = ReadStat(file_path)

    

if __name__ == '__main__':
    main_conv()