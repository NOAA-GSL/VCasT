from mvt.ioc import *
from mvt.parallel import *
import argparse

def main():

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('config_file', type=str, help="Path to YAML file")
    args = parser.parse_args()

    config = PrepIO(args.config_file)

    dates = dates_to_list(config.start_date, config.end_date,config.interval_hours)
    fcst_files, ref_files = files_to_list(config.fcst_file_template, config.ref_file_template, dates, config.shift)
    
    config.open_output_file()

    process_in_parallel(dates, fcst_files, ref_files, config)

    config.close_output_file()

if __name__ == '__main__':
    main()