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
#source: https://automating-gis-processes.github.io/site/notebooks/L2/calculating-distances.html
def calculate_distance(row, dest_geom, src_col='geometry', target_col='distance'):
    """
    Calculates the distance between Point geometries.

    Parameters
    ----------
    dest_geom : shapely.Point
       A single Shapely Point geometry to which the distances will be calculated to.
    src_col : str
       A name of the column that has the Shapely Point objects from where the distances will be calculated from.
    target_col : str
       A name of the target column where the result will be stored.

    Returns
    -------

    Distance in kilometers that will be stored in 'target_col'.
    """

    # Calculate the distances
    dist = row[src_col].centroid.distance(dest_geom)

    # Convert into kilometers
    dist_km = dist / 1000

    # Assign the distance to the original data
    row[target_col] = dist_km
    return row
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
# admin areas
department_dic = {'Santander': 68}
department_ids = ['68']
municipaltiy_dic = {'Puerto Wilches':           '68575',
                    'Sabana de Torres':         '68655',
                    'Barrancabermeja':          '68081',
                    #'SAN VICENTE DE CHUCURI':   68689
                    }
municipaltiy_ids = ['68575', '68655', '68081']




#Hybas
#Distance to dam
#Buffer to river - buffer
# segementID == 15 & elev_m <= 230
#Distance to river

# load data ############################################################################################################
# admin areas
logging.info("loading admin area data")
admin_a = gpd.read_file(path_admin)
municipalties = admin_a[admin_a['MPIO_CCDGO'].isin(municipaltiy_ids)]
del admin_a

# catchment areas
logging.info("loading catchment area data")
catchment_SA = gpd.read_file(path_catch)
catchment_SA_ = gpd.overlay(catchment_SA, municipalties, how='intersection')

# process ##############################################################################################################
# exporting ############################################################################################################
municipalties.to_file(path_interim / "study_area/municipalties_SA.gpkg", driver="GPKG")
catchment_SA_.to_file(path_interim / "study_area/catchments_SA.gpkg", driver="GPKG")

# end time-count and print time stats ##################################################################################
end_time = datetime.datetime.now()
diff = end_time - start_time
days, seconds = diff.days, diff.seconds
hours = days * 24 + seconds // 3600
minutes = (seconds % 3600) // 60
seconds = seconds % 60
logging.info(f'The entire process took {days} days, {hours} hours, {minutes} minutes {seconds} seconds')