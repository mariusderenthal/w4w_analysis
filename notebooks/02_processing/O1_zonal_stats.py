# !/usr/bin/env python3

# libraries ############################################################################################################
import logging
import pathlib
import datetime
import pandas as pd
import geopandas as gpd
import numpy as np
from rasterstats import zonal_stats

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
path_study_area = path_data_inter / 'study_area/study_area.gpkg'

# landcover
path_landcover_92_19 = path_data_raw / 'LC_CCI_ESA_COL'
# global variables #####################################################################################################
file_format = '*.tif'
pattern_data = ('*v2.0.7.crop*', '*v2.1.1*')
pattern_qa = '*qualityflag*'
pattern_reforest = '*reforest.tiff*'
pattern_deforest = '*deforest.tiff*'
pattern_mask = '*masked_cropped.tiff'

files_all = path_landcover_92_19.glob(file_format)
files_all_list = list(path_landcover_92_19.glob(file_format))

files_data_list = get_files(pattern_data)
files_data = (y for y in files_data_list)

files_qa = path_data.glob(pattern_qa)
files_qa_list = list(path_landcover_92_19.glob(pattern_qa))

files_reforest_list = list((path_data_inter / 'lc_change').glob(pattern_reforest))
files_reforest = (path_data_inter / 'lc_change').glob(pattern_reforest)

files_deforest_list = list((path_data_inter / 'lc_change').glob(pattern_deforest))
files_deforest = (path_data_inter / 'lc_change').glob(pattern_deforest)

files_mask_list = list((path_data_inter / 'lc_change').glob(pattern_mask))
files_mask = (path_data_inter / 'lc_change').glob(pattern_mask)

years = [str(i) for i in range(2004, 2020)]
files_mask_list_sp = [s for s in files_mask_list if any(xs in str(s) for xs in years)]

# global variables #####################################################################################################
'''
file_format = '*.tif'
pattern_data = ('*v2.0.7.crop*', '*v2.1.1*')
pattern_qa = '*qualityflag*'

files_all = path_landcover_92_19.glob(file_format)
files_all_list = list(path_landcover_92_19.glob(file_format))

files_data_list = get_files(pattern_data)
files_data = (y for y in files_data_list)

files_qa = path_data.glob(pattern_qa)
files_qa_list = list(path_landcover_92_19.glob(pattern_qa))
'''
file_format = '*.tiff'
pattern_base = '*base*'
pattern_change = '*binary*'
pattern_veg = '*veg*'

#files_all = path_output.glob(pattern_base)

#files_all_base = list(path_output.glob(pattern_base))
#files_all_change = list(path_output.glob(pattern_change))
#files_all_veg = list(path_output.glob(pattern_veg))
# process #############################################################################################################
# load catchments
dam_catch = gpd.read_file(path_study_area)
dam_catch.to_crs(epsg=3116, inplace=True)

# calculate count of each base land cover for each polygon
dict_lc = {}
for year in range(1992, 2020):
    # input Raster
    pathlib_to_tif = [lc for lc in files_mask_list if str(year) in str(lc)]
    stats = zonal_stats(str(path_study_area),
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
df_lc[[10, 11, 30, 40, 50,120, 160, 170, 180, 210, 0, 100, 110, 130, 190]] = df_lc[[10, 11, 30, 40, 50,120, 160, 170, 180, 210, 0, 100, 110, 130, 190]].fillna(0)
# calculte percentage of base land cover types
df_lc["crop_share"] = df_lc[10] / (df_lc[10] + df_lc[11] + df_lc[30] + df_lc[40] + df_lc[50] + df_lc[120] + df_lc[160]+ df_lc[170] + df_lc[180] + df_lc[210] + df_lc[0] + df_lc[100] + df_lc[110] + df_lc[130]+ df_lc[190])
df_lc["herb_share"] = df_lc[11] / (df_lc[10] + df_lc[11] + df_lc[30] + df_lc[40] + df_lc[50] + df_lc[120] + df_lc[160]+ df_lc[170] + df_lc[180] + df_lc[210] + df_lc[0] + df_lc[100] + df_lc[110] + df_lc[130]+ df_lc[190])
df_lc["mosaic_crop_share"] = df_lc[30] / (df_lc[10] + df_lc[11] + df_lc[30] + df_lc[40] + df_lc[50] + df_lc[120] + df_lc[160]+ df_lc[170] + df_lc[180] + df_lc[210] + df_lc[0] + df_lc[100] + df_lc[110] + df_lc[130]+ df_lc[190])
df_lc["mosaic_natural_share"] = df_lc[40] / (df_lc[10] + df_lc[11] + df_lc[30] + df_lc[40] + df_lc[50] + df_lc[120] + df_lc[160]+ df_lc[170] + df_lc[180] + df_lc[210] + df_lc[0] + df_lc[100] + df_lc[110] + df_lc[130]+ df_lc[190])
df_lc["tree_share"] = df_lc[50] / (df_lc[10] + df_lc[11] + df_lc[30] + df_lc[40] + df_lc[50] + df_lc[120] + df_lc[160]+ df_lc[170] + df_lc[180] + df_lc[210] + df_lc[0] + df_lc[100] + df_lc[110] + df_lc[130]+ df_lc[190])
df_lc["shrubland_share"] = df_lc[120] / (df_lc[10] + df_lc[11] + df_lc[30] + df_lc[40] + df_lc[50] + df_lc[120] + df_lc[160]+ df_lc[170] + df_lc[180] + df_lc[210] + df_lc[0] + df_lc[100] + df_lc[110] + df_lc[130]+ df_lc[190])
df_lc["tree_flood_fresh_share"] = df_lc[160] / (df_lc[10] + df_lc[11] + df_lc[30] + df_lc[40] + df_lc[50] + df_lc[120] + df_lc[160]+ df_lc[170] + df_lc[180] + df_lc[210] + df_lc[0] + df_lc[100] + df_lc[110] + df_lc[130]+ df_lc[190])
df_lc["tree_flood_saline_share"] = df_lc[170] / (df_lc[10] + df_lc[11] + df_lc[30] + df_lc[40] + df_lc[50] + df_lc[120] + df_lc[160]+ df_lc[170] + df_lc[180] + df_lc[210] + df_lc[0] + df_lc[100] + df_lc[110] + df_lc[130]+ df_lc[190])
df_lc["shrub_flooded_share"] = df_lc[180] / (df_lc[10] + df_lc[11] + df_lc[30] + df_lc[40] + df_lc[50] + df_lc[120] + df_lc[160]+ df_lc[170] + df_lc[180] + df_lc[210] + df_lc[0] + df_lc[100] + df_lc[110] + df_lc[130]+ df_lc[190])
df_lc["water_share"] = df_lc[210] / (df_lc[10] + df_lc[11] + df_lc[30] + df_lc[40] + df_lc[50] + df_lc[120] + df_lc[160]+ df_lc[170] + df_lc[180] + df_lc[210] + df_lc[0] + df_lc[100] + df_lc[110] + df_lc[130]+ df_lc[190])
df_lc["outside_share"] = df_lc[0] / (df_lc[10] + df_lc[11] + df_lc[30] + df_lc[40] + df_lc[50] + df_lc[120] + df_lc[160]+ df_lc[170] + df_lc[180] + df_lc[210] + df_lc[0] + df_lc[100] + df_lc[110] + df_lc[130]+ df_lc[190])
df_lc["mosaic_tree_share"] = df_lc[100] / (df_lc[10] + df_lc[11] + df_lc[30] + df_lc[40] + df_lc[50] + df_lc[120] + df_lc[160]+ df_lc[170] + df_lc[180] + df_lc[210] + df_lc[0] + df_lc[100] + df_lc[110] + df_lc[130]+ df_lc[190])
df_lc["mosaic_herb_share"] = df_lc[110] /(df_lc[10] + df_lc[11] + df_lc[30] + df_lc[40] + df_lc[50] + df_lc[120] + df_lc[160]+ df_lc[170] + df_lc[180] + df_lc[210] + df_lc[0] + df_lc[100] + df_lc[110] + df_lc[130]+ df_lc[190])
df_lc["grassland_share"] = df_lc[130] / (df_lc[10] + df_lc[11] + df_lc[30] + df_lc[40] + df_lc[50] + df_lc[120] + df_lc[160]+ df_lc[170] + df_lc[180] + df_lc[210] + df_lc[0] + df_lc[100] + df_lc[110] + df_lc[130]+ df_lc[190])
df_lc["urban_share"] = df_lc[190] / (df_lc[10] + df_lc[11] + df_lc[30] + df_lc[40] + df_lc[50] + df_lc[120] + df_lc[160]+ df_lc[170] + df_lc[180] + df_lc[210] + df_lc[0] + df_lc[100] + df_lc[110] + df_lc[130]+ df_lc[190])

df_lc.rename(columns={10: 'crop',
                      11: 'herb',
                      30: 'mosaic_crop',
                      40: 'mosaic_natural',
                      50: 'tree',
                      120: 'shrubland',
                      160: 'tree_flood_fresh',
                      170: 'tree_flood_saline',
                      180: 'shrub_flooded',
                      210: 'water',
                      0: 'unknown',
                      100: 'mosaic_tree',
                      110: 'mosaic_herb',
                      130: 'grassland',
                      190: 'urban'}, inplace=True)

df_lc.to_csv(path_data_output /"df_lc.csv")
