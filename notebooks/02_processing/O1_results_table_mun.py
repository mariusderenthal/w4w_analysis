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
pattern_mask = '*_reforest_masked_copped.tiff'


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
study_area = gpd.read_file(path_study_area)


# calculate count of each base land cover for each polygon
dict_lc = {}
for year in range(1992, 2019):
    # input Raster
    pathlib_to_tif = [lc for lc in files_mask_list if str(f'change_{year}') in str(lc)]
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

# delete shrubland
df_lc.drop(df_lc.columns[len(df_lc.columns)-2], axis=1, inplace=True)
# replace na with 0
df_lc[[10, 30, 40,120]] = df_lc[[10, 30, 40,120]].fillna(0)
# delete years I am not interested in
df_lc = df_lc[~df_lc.iloc[:, 8].between(1990, 2003, inclusive=False)]

# sum up total numbet of afforested cells
df_lc['total_change_cells'] = (df_lc[10] + df_lc[30] + df_lc[40]+ df_lc[120])


# read original land cover data
df_lc_lf_orig = pd.read_csv(path_data_output / "df_lc.csv")

# sum up total count of cells
df_lc_lf_orig['total_sa_orig'] = df_lc_lf_orig['crop'] + df_lc_lf_orig['herb'] + df_lc_lf_orig['mosaic_crop'] +\
                                 df_lc_lf_orig['mosaic_natural'] + df_lc_lf_orig['tree'] + df_lc_lf_orig['shrubland'] +\
                                 df_lc_lf_orig['grassland'] +\
                                 df_lc_lf_orig['tree_flood_fresh'] + df_lc_lf_orig['tree_flood_saline'] + \
                                 df_lc_lf_orig['shrub_flooded'] + df_lc_lf_orig['water'] + \
                                 df_lc_lf_orig['unknown'] + df_lc_lf_orig['mosaic_tree'] + \
                                 df_lc_lf_orig['mosaic_herb'] + df_lc_lf_orig['urban']

# sum up total count of cells which are eligible for afforestation
df_lc_lf_orig['total_available_orig'] = df_lc_lf_orig['crop'] + df_lc_lf_orig['herb'] + df_lc_lf_orig['mosaic_crop'] +\
                                 df_lc_lf_orig['mosaic_natural'] + df_lc_lf_orig['shrubland']

df_lc_lf_orig = df_lc_lf_orig[~df_lc_lf_orig.iloc[:, 23].between(1990, 2003, inclusive=False)]

# merge two dataframes
df_lc_lf_orig['MPIO_CCDGO']=df_lc_lf_orig['MPIO_CCDGO'].astype(int)
df_lc['MPIO_CCDGO']=df_lc['MPIO_CCDGO'].astype(int)
df_lc_lf_orig['year']=df_lc_lf_orig['year'].astype(int)
df_lc['year']=df_lc['year'].astype(int)

df = pd.merge(df_lc,df_lc_lf_orig[['MPIO_CCDGO','year','total_sa_orig','total_available_orig']], on=['MPIO_CCDGO','year'],how='left')


df['change_hectar'] = df['total_change_cells'] * 9
df['change_tot_per'] = df['total_change_cells'] / df['total_sa_orig']
df['change_available_per'] = df['total_change_cells'] / df['total_available_orig']

df.to_csv(path_data_output /"O1_results_table_mun.csv")
