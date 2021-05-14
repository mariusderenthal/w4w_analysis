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
def get_files(patterns):
    all_files = []
    for pat in patterns:
        all_files.extend(path_landcover_92_19.glob(pat))
    return all_files
# folder path ##########################################################################################################
path_current = pathlib.Path.cwd()
path_src = path_current / 'src'
path_notebooks = path_current / 'notebooks'
path_data = path_current/'data'
path_data_raw = path_data/'01_raw'
path_data_inter = path_data/'02_intermediate'
path_data_output = path_data/'03_processed'

# study areas
path_munic = path_data_inter / 'study_area/municipalties_SA.gpkg'
path_catch = path_data_inter / 'study_area/catchments_SA.gpkg'
path_river = path_data_inter / 'study_area/river_buffer.gpkg'

# landcover
path_landcover_92_19 = path_data_raw / 'LC_CCI_ESA_COL'

# global variables #####################################################################################################
file_format = '*.tif'
pattern_data = ('*v2.0.7.crop*', '*v2.1.1*')
pattern_qa = '*qualityflag*'

files_all = path_landcover_92_19.glob(file_format)
files_all_list = list(path_landcover_92_19.glob(file_format))

files_data_list = get_files(pattern_data)
files_data = (y for y in files_data_list)

files_qa = path_data.glob(pattern_qa)
files_qa_list = list(path_landcover_92_19.glob(pattern_qa))

# process ##############################################################################################################
# most important land cover classes in study area
# calculate count of each base land cover for each polygon
dict_lc = {}
for year in range(1992, 2020):
    # input Raster
    pathlib_to_tif = [lc for lc in files_data_list if str(year) in str(lc)]
    stats = zonal_stats(str(path_munic),
                        str(pathlib_to_tif[0]),
                        categorical=True,
                        copy_properties=True,
                        geojson_out=True)

    # transform geojson to dataframe
    df = pd.DataFrame(stats)
    df2 = pd.json_normalize(df['properties'])
    # add year
    df2['year'] = year
    # add data to list
    dict_lc[year] = df2.copy()

    logging.info(f"Done calculating base land cover count for {str(year)}")

# concat all years to one dataframe
df_lc = pd.concat(dict_lc.values(), ignore_index=True)
del dict_lc
# replace na wit 0
lc_classes = [10, 11, 30, 40, 50, 60, 100, 110, 120, 130, 160, 170, 180, 190, 210]
df_lc[lc_classes] = df_lc[lc_classes].fillna(0).astype(np.int64)

# calculte percentage of base land cover types
df_lc["Rainfed shrub crops"] = df_lc[10] / df_lc[lc_classes].sum(axis=1)
df_lc["Rainfed herbaceous crops"] = df_lc[11] / df_lc[lc_classes].sum(axis=1)
df_lc["Cultivated and managed terrestrial areas"] = df_lc[30] / df_lc[lc_classes].sum(axis=1)
df_lc["Natural and semi-natural primarily terrestrial vegetation"] = df_lc[40] / df_lc[lc_classes].sum(axis=1)
df_lc["Broadleaved evergreen closed to open trees"] = df_lc[50] / df_lc[lc_classes].sum(axis=1)
df_lc["Broadleaved deciduous closed to open trees"] = df_lc[60] / df_lc[lc_classes].sum(axis=1)
df_lc["Closed to open trees"] = df_lc[100] / df_lc[lc_classes].sum(axis=1)
df_lc["Herbaceous closed to open vegetation"] = df_lc[110] / df_lc[lc_classes].sum(axis=1)
df_lc["Broadleaved closed to open shrubland"] = df_lc[120] / df_lc[lc_classes].sum(axis=1)
df_lc["Herbaceous closed to very open vegetation"] = df_lc[130] / df_lc[lc_classes].sum(axis=1)
df_lc["Closed to open (100-40%) broadleaved trees on temporarily flooded land"] = df_lc[160] / df_lc[lc_classes].sum(axis=1)
df_lc["Closed to open (100-40%) broadleaved trees on permanently flooded land"] = df_lc[170] / df_lc[lc_classes].sum(axis=1)
df_lc["Closed to open shrubs on permanently flooded land"] = df_lc[180] / df_lc[lc_classes].sum(axis=1)
df_lc["Artificial surfaces and associated areas"] = df_lc[190] / df_lc[lc_classes].sum(axis=1)
df_lc["Natural water bodies"] = df_lc[210] / df_lc[lc_classes].sum(axis=1)

df_lc.rename(columns={1: 'agriculture',
                      2: 'veg_terrestrial',
                      3: 'veg_aqua',
                      4: 'artificial',
                      5: 'bare',
                      6: 'water_ice',
                      0: 'unknown'}, inplace=True)

# exporting ############################################################################################################
# end time-count and print time stats ##################################################################################
end_time = datetime.datetime.now()
diff = end_time - start_time
days, seconds = diff.days, diff.seconds
hours = days * 24 + seconds // 3600
minutes = (seconds % 3600) // 60
seconds = seconds % 60
logging.info(f'The entire process took {days} days, {hours} hours, {minutes} minutes {seconds} seconds')