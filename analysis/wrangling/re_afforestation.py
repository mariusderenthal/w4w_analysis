# !/usr/bin/env python3

# libraries ############################################################################################################
import logging
import pathlib
import datetime
#from osgeo import gdal
import numpy as np

# settings #############################################################################################################
# set logging config
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d, %b, %Y, %H:%M:%S',
                    # filename = 'tidy_data.log'
                    )

# set time count
start_time = datetime.datetime.now()
logging.info("Starting process")


# functions ############################################################################################################
# folder path ##########################################################################################################
path_current = pathlib.Path.cwd()
path_project = path_current.parent.parent
path_data = path_project / 'data'
path_data_raw = path_data / 'raw'
path_interim = path_data / 'interim'
path_output = path_data / 'processed'

# admin level
path_admin = path_data_raw / 'landcover' / 'LC_CCI_ESA_COL'
# global variables #####################################################################################################
# process ##############################################################################################################
# most important land cover classes in study area

# exporting ############################################################################################################
# end time-count and print time stats ##################################################################################
end_time = datetime.datetime.now()
diff = end_time - start_time
days, seconds = diff.days, diff.seconds
hours = days * 24 + seconds // 3600
minutes = (seconds % 3600) // 60
seconds = seconds % 60
logging.info(f'The entire process took {days} days, {hours} hours, {minutes} minutes {seconds} seconds')