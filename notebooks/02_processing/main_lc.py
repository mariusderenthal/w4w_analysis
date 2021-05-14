# !/usr/bin/env python3

# libraries ############################################################################################################
import logging
import pathlib
import datetime
import pandas as pd
import geopandas as gpd
import numpy as np
from rasterstats import zonal_stats
#import rtree

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
path_data = path_current / 'data'
path_data_raw = path_data / '01_raw'
path_data_inter = path_data / '02_intermediate'
path_data_output = path_data / '03_processed'

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
pattern_reforest = '*reforest*'

files_all = path_landcover_92_19.glob(file_format)
files_all_list = list(path_landcover_92_19.glob(file_format))

files_data_list = get_files(pattern_data)
files_data = (y for y in files_data_list)

files_qa = path_data.glob(pattern_qa)
files_qa_list = list(path_landcover_92_19.glob(pattern_qa))

files_reforest_list = list((path_data_inter / 'lc_change').glob(pattern_reforest))
files_reforest = (path_data_inter / 'lc_change').glob(pattern_reforest)

# process ##############################################################################################################
# most important land cover classes in study area
# calculate count of each base land cover for each polygon
dict_lc = {}
for year in range(1992, 2020):
    # input Raster
    pathlib_to_tif = [lc for lc in files_data_list if str(year) in str(lc)]
    stats = zonal_stats(str(path_catch),                                        # Pick study area
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
del df2
del df

# replace na wit 0
lc_classes = [10, 11, 30, 40, 50, 60, 100, 110, 120, 130, 160, 170, 180, 190, 210]
df_lc[lc_classes] = df_lc[lc_classes].fillna(0).astype(np.int64)

# sumamrize classes 10 and 11
df_lc[10] = df_lc[10] + df_lc[11]
del df_lc[11]

# update lc_classes
lc_classes.remove(11)

# calculte total pixel count
df_lc["pixel_count"] = df_lc[lc_classes].sum(axis=1)

# calculte percentage of base land cover types
df_lc["cropland_rainfed_share"] = df_lc[10] / df_lc[lc_classes].sum(axis=1)
# df_lc["Rainfed herbaceous crops"] = df_lc[11] / df_lc[lc_classes].sum(axis=1)
df_lc["mosaic_cropland_share"] = df_lc[30] / df_lc[lc_classes].sum(axis=1)
df_lc["mosaic_natural_vegetation_share"] = df_lc[40] / df_lc[lc_classes].sum(axis=1)
df_lc["tree_cover_evergreen_share"] = df_lc[50] / df_lc[lc_classes].sum(axis=1)
df_lc["tree_cover_deciduous_share"] = df_lc[60] / df_lc[lc_classes].sum(axis=1)
df_lc["mosaic_tree_and_shrub_share"] = df_lc[100] / df_lc[lc_classes].sum(axis=1)
df_lc["mosaic_herbaceous_share"] = df_lc[110] / df_lc[lc_classes].sum(axis=1)
df_lc["shrubland_share"] = df_lc[120] / df_lc[lc_classes].sum(axis=1)
df_lc["grassland_share"] = df_lc[130] / df_lc[lc_classes].sum(axis=1)
df_lc["tree_cover_flooded_fresh_share"] = df_lc[160] / df_lc[lc_classes].sum(axis=1)
df_lc["tree_cover_flooded_saline_share"] = df_lc[170] / df_lc[lc_classes].sum(axis=1)
df_lc["shrub_herbaceous_cover_flooded_share"] = df_lc[180] / df_lc[lc_classes].sum(axis=1)
df_lc["urban_areas_share"] = df_lc[190] / df_lc[lc_classes].sum(axis=1)
df_lc["water_bodies_share"] = df_lc[210] / df_lc[lc_classes].sum(axis=1)

df_lc.rename(columns={10: 'cropland_rainfed',
                      # 11: 'Herbaceous cover',
                      # 12: 'Tree or shrub cover',
                      # 20: 'Cropland irrigated or post-flooding',
                      30: 'mosaic_cropland',
                      40: 'mosaic_natural_vegetation',
                      50: 'tree_cover_evergreen',
                      60: 'tree_cover_deciduous',
                      # 61: 'Tree cover broadleaved deciduous closed (>40%)',
                      # 62: 'Tree cover broadleaved deciduous open (15-40%)',
                      # 70: 'Tree cover needleleaved evergreen closed to open (>15%)',
                      # 71: 'Tree cover needleleaved evergreen closed (>40%)',
                      # 72: 'Tree cover needleleaved evergreen open (15-40%)',
                      # 80: 'Tree cover needleleaved deciduous closed to open (>15%)',
                      # 81: 'Tree cover needleleaved deciduous closed (>40%)',
                      # 82: 'Tree cover needleleaved deciduous open (15-40%)',
                      # 90: 'Tree cover mixed leaf type (broadleaved and needleleaved)',
                      100: 'mosaic_tree_and_shrub',
                      110: 'mosaic_herbaceous',
                      120: 'shrubland',
                      # 121: 'Shrubland evergreen',
                      # 122: 'Shrubland deciduous',
                      130: 'grassland',
                      # 140: 'Lichens and mosses',
                      # 150: 'Sparse vegetation (tree shrub herbaceous cover) (<15%)',
                      # 151: 'Sparse tree (<15%)',
                      # 152: 'Sparse shrub (<15%)',
                      # 153: 'Sparse herbaceous cover (<15%)',
                      160: 'tree_cover_flooded_fresh',
                      170: 'tree_cover_flooded_saline',
                      180: 'shrub_herbaceous_cover_flooded',
                      190: 'urban_areas',
                      # 200: 'Bare areas',
                      # 201: 'Consolidated bare areas',
                      # 202: 'Unconsolidated bare areas',
                      210: 'water_bodies',
                      # 220: 'Permanent snow and ice',
                      }, inplace=True)

dict_reforest = {}
for year in range(1992, 2019):
    # input Raster
    pathlib_to_tif = [lc for lc in files_reforest_list if str(f"change_{year}_") in str(lc)]
    stats = zonal_stats(str(path_catch),                                        # Pick study area
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
    dict_reforest[year] = df2.copy()

    logging.info(f"Done re- and afforestation count for {str(year)}")

# concat all years to one dataframe
df_reforest = pd.concat(dict_reforest.values(), ignore_index=True)
del dict_reforest
del df2
del df

# replace na wit 0
del df_reforest[0]
reforest_classes = [10, 30, 40, 110, 120, 130, 180, 210]
df_reforest[reforest_classes] = df_reforest[reforest_classes].fillna(0)

# calculte total reforested count
df_reforest["reforest_count"] = df_reforest[reforest_classes].sum(axis=1)
# calculte percentage of re- and afforestation sources
df_reforest["cropland_rainfed_reforest"] = df_reforest[10] / df_reforest[reforest_classes].sum(axis=1)
df_reforest["mosaic_cropland_reforest"] = df_reforest[30] / df_reforest[reforest_classes].sum(axis=1)
df_reforest["mosaic_natural_vegetation_reforest"] = df_reforest[40] / df_reforest[reforest_classes].sum(axis=1)
df_reforest["mosaic_herbaceous_reforest"] = df_reforest[110] / df_reforest[reforest_classes].sum(axis=1)
df_reforest["shrubland_reforest"] = df_reforest[120] / df_reforest[reforest_classes].sum(axis=1)
df_reforest["grassland_reforest"] = df_reforest[130] / df_reforest[reforest_classes].sum(axis=1)
df_reforest["shrub_herbaceous_cover_flooded_reforest"] = df_reforest[180] / df_reforest[reforest_classes].sum(axis=1)
df_reforest["water_bodies_reforest"] = df_reforest[210] / df_reforest[reforest_classes].sum(axis=1)

df_reforest.iloc[:, -8:] = df_reforest.iloc[:, -8:].fillna(0)

# join data frames
df_lc_reforest = pd.merge(df_lc, df_reforest[[# 'buffer', 'MPIO_CCDGO', 'year',
                                              'HYBAS_ID', 'year','MPIO_CCDGO',
                                              'cropland_rainfed_reforest',
                                              'mosaic_cropland_reforest',
                                              'mosaic_natural_vegetation_reforest',
                                              'mosaic_herbaceous_reforest',
                                              'shrubland_reforest',
                                              'grassland_reforest',
                                              'shrub_herbaceous_cover_flooded_reforest',
                                              'water_bodies_reforest',
                                              'reforest_count'
                                              ]],
                          how='left',
                          left_on=[#'buffer', 'MPIO_CCDGO', 'year',
                                   'HYBAS_ID', 'year','MPIO_CCDGO',
                                   ],
                          right_on=[#'buffer', 'MPIO_CCDGO', 'year',
                                    'HYBAS_ID', 'year','MPIO_CCDGO',
                                    ])

df_lc_reforest['reforest_rate'] = df_lc_reforest["reforest_count"] / df_lc_reforest["pixel_count"]

# join data with geometry
logging.info("add geometry information")
# load catchments
#study_area = gpd.read_file(path_river)
study_area = gpd.read_file(path_catch)

df_lc_reforest_geom = pd.merge(df_lc_reforest, study_area[[#'buffer', 'MPIO_CCDGO', 'geometry',
                                                          'HYBAS_ID', 'geometry', 'MPIO_CCDGO'
                                                          ]],
                               how='left',
                               left_on=[#'buffer', 'MPIO_CCDGO',
                                        'HYBAS_ID', 'MPIO_CCDGO'
                                        ],
                               right_on=[#'buffer', 'MPIO_CCDGO'
                                         'HYBAS_ID', 'MPIO_CCDGO'
                                         ])

df_lc_reforest_geom = gpd.GeoDataFrame(df_lc_reforest_geom, geometry='geometry')
df_lc_reforest_geom.columns

# exporting ############################################################################################################
df_lc_reforest_geom.to_file(path_data_inter / "df_lc_reforest_geom_catch.gpkg", driver="GPKG")
df_lc_reforest.to_csv(path_data_inter / "df_lc_reforest_catch.csv")
# end time-count and print time stats ##################################################################################
end_time = datetime.datetime.now()
diff = end_time - start_time
days, seconds = diff.days, diff.seconds
hours = days * 24 + seconds // 3600
minutes = (seconds % 3600) // 60
seconds = seconds % 60
logging.info(f'The entire process took {days} days, {hours} hours, {minutes} minutes, {seconds} seconds')
