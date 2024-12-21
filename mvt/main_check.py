
import argparse
from mvt.file_handler import *
from colorama import Fore, Style  

def main_check():

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('file', type=str, help="Path to file")
    args = parser.parse_args()

    file_path = args.file

    file_type = identify_file_type(file_path)
    
    print()
    if file_type == "netcdf":
        print("File type: NetCDF")
        check_netcdf(file_path)
    elif file_type == "grib2":
        print("File type: GRIB2")
        check_grib2(file_path)
    else:
        print(Fore.RED + "Unknown file type. Only NetCDF and GRIB2 are supported." + Style.RESET_ALL)
    
    print()
    print("-"*10)
    print(Fore.GREEN + "File passed check." + Style.RESET_ALL)
    print("-"*10)

    print()


if __name__ == '__main__':
    main_check()