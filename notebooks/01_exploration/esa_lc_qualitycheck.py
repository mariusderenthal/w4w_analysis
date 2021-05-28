# !/usr/bin/env python3

# libraries ############################################################################################################
import logging
import pathlib
import datetime
import numpy as np
import rasterio

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


def read_file(file):
    with rasterio.open(file) as src:
        return src.read(1)


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
pattern_reforest = '*reforest.tiff*'
pattern_deforest = '*deforest.tiff*'

files_all = path_landcover_92_19.glob(file_format)
files_all_list = list(path_landcover_92_19.glob(file_format))

files_data_list = get_files(pattern_data)
files_data = (y for y in files_data_list)

files_qa = path_data.glob(pattern_qa)
files_qa_list = list(path_landcover_92_19.glob(pattern_qa))

files_reforest_list = list((path_data_inter / 'lc_change').glob(pattern_reforest))
files_reforest = (path_data_inter / 'lc_change').glob(pattern_reforest)

files_deforest_list = list((path_data_inter / 'lc_change').glob(pattern_deforest))
files_deforest = (path_data_inter / 'lc_change').glob(pattern_reforest)

years = [str(i) for i in range(2004, 2020)]
files_reforest_list_sp = [s for s in files_reforest_list if any(xs in str(s) for xs in years)]
files_deforest_list_sp = [s for s in files_deforest_list if any(xs in str(s) for xs in years)]
# process #############################################################################################################
'''
# Read metadata of first file
with rasterio.open(files_reforest_list[0]) as src0:
    meta = src0.meta

# Update meta to reflect the number of layers
meta.update(count=len(files_reforest_list))

# Read each layer and write it to stack
with rasterio.open('reforest_stack.tif', 'w', **meta) as dst:
    for id, layer in enumerate(files_reforest_list, start=1):
        with rasterio.open(layer) as src1:
            dst.write_band(id, src1.read(1))
'''
# Check for double afforestation
# Read all data as a list of numpy arrays
array_list = [read_file(x) for x in files_reforest_list_sp]
# reclassify classes
array_list = [year + 2000 for year in array_list]
array_list = [np.where(year == 2000, 0, year) for year in array_list]
# Perform sum calculation
double_aff = np.sum(array_list, axis=0)
# reclassify classes
double_aff[np.where(double_aff < 4000)] = 0
double_aff[np.where(double_aff > 4000)] = 1
del array_list

# Check for double deforestation
# Read all data as a list of numpy arrays
array_list = [read_file(x) for x in files_deforest_list_sp]
# reclassify classes
array_list = [year + 2000 for year in array_list]
array_list = [np.where(year == 2000, 0, year) for year in array_list]
# Perform sum calculation
double_def = np.sum(array_list, axis=0)
# reclassify classes
double_def[np.where(double_def < 4000)] = 0
double_def[np.where(double_def > 4000)] = 1
del array_list

# Check where de and afforestation have taken place
# Read all data as a list of numpy arrays
array_list = [read_file(x) for x in files_reforest_list_sp]
# reclassify classes
array_list = [year + 2000 for year in array_list]
array_list = [np.where(year == 2000, 0, year) for year in array_list]
# Perform sum calculation
double_aff = np.sum(array_list, axis=0)
# reclassify classes
double_aff[np.where(double_aff > 0)] = 1
del array_list
# Read all data as a list of numpy arrays
array_list = [read_file(x) for x in files_deforest_list_sp]
# reclassify classes
array_list = [year + 2000 for year in array_list]
array_list = [np.where(year == 2000, 0, year) for year in array_list]
# Perform sum calculation
double_def = np.sum(array_list, axis=0)
# reclassify classes
double_def[np.where(double_def > 0)] = 1
del array_list
# combine de and afforested pixels
de_and_aff = double_aff + double_def

# afforestation from 2003 - 2019
array_list = [read_file(x) for x in files_reforest_list_sp]
# summarize afforestation in one raster
afforestation = np.sum(array_list, axis=0)
np.unique(afforestation)
del array_list

# exporting ############################################################################################################
# Get metadata from one of the input files
with rasterio.open(files_reforest_list[0]) as src:
    meta = src.meta

with rasterio.open(path_data_inter / 'lc_change/double_reforested_03_19.tiff', 'w', **meta) as dst:
    dst.write(double_aff.astype(rasterio.int16), 1)

with rasterio.open(path_data_inter / 'lc_change/double_deforested_03_19.tiff', 'w', **meta) as dst:
    dst.write(double_def.astype(rasterio.int16), 1)

with rasterio.open(path_data_inter / 'lc_change/de_and_aff_03_19.tiff', 'w', **meta) as dst:
    dst.write(de_and_aff.astype(rasterio.int16), 1)

with rasterio.open(path_data_inter / 'lc_change/reforested_03_19.tiff', 'w', **meta) as dst:
    dst.write(afforestation.astype(rasterio.int16), 1)

# end time-count and print time stats ##################################################################################
end_time = datetime.datetime.now()
diff = end_time - start_time
days, seconds = diff.days, diff.seconds
hours = days * 24 + seconds // 3600
minutes = (seconds % 3600) // 60
seconds = seconds % 60
logging.info(f'The entire process took {days} days, {hours} hours, {minutes} minutes {seconds} seconds')
