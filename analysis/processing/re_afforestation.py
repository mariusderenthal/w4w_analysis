# !/usr/bin/env python3

# libraries ############################################################################################################
import logging
import pathlib
import datetime
import pandas as pd
import geopandas as gpd
import numpy as np
from rasterstats import zonal_stats
import rtree

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
path_anlysis = path_current / 'analysis'
path_data = path_current/'data'
path_data_raw = path_data/'raw'
path_interim = path_data/'interim'
path_output = path_data/'processed'

path_admin = path_data_raw/'admin_areas'/'col_second_level_admin_boundaries'/'col_second_level_admin_boundaries.shp'
path_catch = path_data_raw/'catchment_areas'/'hydrosheds-de3a202db76ddd93c689'/'hybas_sa_lev00_v1c'/'hybas_sa_lev00_v1c.shp'
path_dam = path_data_raw/'dam_locations'/'GRanD_Version_1_3'/'GRanD_dams_v1_3.shp'
path_river = path_interim/'rivers'/'rio_sogamoso.gpkg'

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