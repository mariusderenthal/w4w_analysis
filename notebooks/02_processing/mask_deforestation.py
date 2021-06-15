# !/usr/bin/env python3

# libraries ############################################################################################################
import logging
import pathlib
import datetime
import numpy as np
import rasterio
import rasterio.mask

import geopandas as gpd
from osgeo import gdal

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


def make_raster(in_ds, fn, data, data_type, nr_bands, nodata=None):
    driver = gdal.GetDriverByName('GTiff')
    out_ds = driver.Create(fn, in_ds.RasterXSize, in_ds.RasterYSize, nr_bands, data_type,
                           ['COMPRESS=DEFLATE',
                            'PREDICTOR=2',
                            'TILED=YES'])
    out_ds.SetProjection(in_ds.GetProjection())
    out_ds.SetGeoTransform(in_ds.GetGeoTransform())
    out_ds.GetRasterBand(1).WriteArray(data[0])
    out_ds.FlushCache()
    out_ds = None
    return out_ds


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

# palm oil
path_palm_rspo = path_data_raw / 'palm_oil' / 'Agro-industry' / 'Agro-industry.shp'
path_palm_planted = path_data_raw / 'palm_oil' / 'plantations_v1_3_dl.gdb'

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

years = [str(i) for i in range(1992, 2016)]
files_reforest_list_sp = [s for s in files_reforest_list if any(xs in str(s) for xs in years)]
files_deforest_list_sp = [s for s in files_deforest_list if any(xs in str(s) for xs in years)]

plantation_area = 0.025628368675795276
# load data ############################################################################################################
# palm areas areas
logging.info("loading planted trees")
# fiona.listlayers(path_palm_planted)
palm_planted = gpd.read_file(path_palm_planted, driver='FileGDB', layer='col_plant')
# palm_planted.to_crs(epsg=3116, inplace=True)

# filter plantation
logging.info("filter plantation")
plantation = palm_planted.loc[palm_planted['Shape_Area'] == plantation_area]
del palm_planted
# process ##############################################################################################################
# deforestation from 1992 - 2016
array_list = [read_file(x) for x in files_deforest_list_sp]

# summarize afforestation in one raster
deforestation_92_16 = np.sum(array_list, axis=0)
np.unique(deforestation_92_16)
del array_list

with rasterio.open(files_reforest_list[0]) as src:
    meta = src.meta

with rasterio.open(path_data_inter / 'lc_change/deforested_92_16.tiff', 'w', **meta) as dst:
    dst.write(deforestation_92_16.astype(rasterio.int16), 1)


with rasterio.open(path_data_inter / 'lc_change/deforested_92_16.tiff') as src:
    out_image, out_transform = rasterio.mask.mask(src, plantation.geometry, crop=False, nodata=-1)
    out_meta = src.meta

out_meta.update({"driver": "GTiff",
                 "height": out_image.shape[1],
                 "width": out_image.shape[2],
                 "transform": out_transform})

# reclassify crop classes back to forest class
out_image[np.where(out_image > 0)] = 1000
out_image[np.where(out_image == -1)] = 0
with rasterio.open(path_data_inter / 'lc_change/deforested_92_16_plantantion.tiff', "w", **out_meta) as dest:
    dest.write(out_image)

# create binary change raster without modifying original classes
for year in range(1992, 2020):
    # input Raster
    raster_old_path = [lc for lc in files_data_list if str(year) in str(lc)]

    # open raster files
    raster_old = gdal.Open(str(raster_old_path[0]))
    raster_old_data = raster_old.GetRasterBand(1).ReadAsArray().astype(int)

    # identify deforested areas
    lc_mask = raster_old_data + out_image

    # reclassify to forest classes
    lc_mask[np.where(lc_mask >= 1000)] = 50

    # add dimension in order to export
    lc_mask = np.reshape(lc_mask, newshape=(1, raster_old.RasterYSize, raster_old.RasterXSize))
    make_raster(in_ds=raster_old,
                fn=str(path_data_inter / f'lc_change/lc_original_{str(year)}_masked.tiff'),
                data=lc_mask,
                data_type=gdal.GDT_Int16,
                nr_bands=1,
                nodata=None)

    # logging info
    logging.info(f"Done masking {str(year)}")

# exporting ############################################################################################################

# end time-count and print time stats ##################################################################################
end_time = datetime.datetime.now()
diff = end_time - start_time
days, seconds = diff.days, diff.seconds
hours = days * 24 + seconds // 3600
minutes = (seconds % 3600) // 60
seconds = seconds % 60
logging.info(f'The entire process took {days} days, {hours} hours, {minutes} minutes {seconds} seconds')
