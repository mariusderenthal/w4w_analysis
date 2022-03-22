# !/usr/bin/env python3

# libraries ############################################################################################################
import logging
import pathlib
import datetime
from osgeo import gdal
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
def get_files(patterns, data_path):
    all_files = []
    for pat in patterns:
        all_files.extend(data_path.glob(pat))
    return all_files


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

# landcover
path_landcover_92_19 = path_data_raw / 'LC_CCI_ESA_COL'
# global variables #####################################################################################################
file_format = '*.tif'
pattern_data = ('*v2.0.7.crop*', '*v2.1.1*')
pattern_qa = '*qualityflag*'
pattern_mask = '*masked_cropped.tiff'

files_all = path_landcover_92_19.glob(file_format)
files_all_list = list(path_landcover_92_19.glob(file_format))

files_data_list = get_files(pattern_data, path_landcover_92_19)
files_data = (y for y in files_data_list)

files_qa = path_data.glob(pattern_qa)
files_qa_list = list(path_landcover_92_19.glob(pattern_qa))

files_mask_list = list((path_data_inter / 'lc_change').glob(pattern_mask))
files_mask = (path_data_inter / 'lc_change').glob(pattern_mask)

# process #############################################################################################################
# create binary change raster without modifying original classes
for year in range(1992, 2019):
    # input Raster
    raster_old_path = [lc for lc in files_data_list if str(year) in str(lc)]
    raster_new_path = [lc for lc in files_data_list if str(year + 1) in str(lc)]

    # open raster files
    raster_old = gdal.Open(str(raster_old_path[0]))
    raster_new = gdal.Open(str(raster_new_path[0]))

    # read bands as matrix arrays
    raster_old_data = raster_old.GetRasterBand(1).ReadAsArray().astype(int)
    raster_new_data = raster_new.GetRasterBand(1).ReadAsArray().astype(int)

    # reclassify crop classes
    raster_old_data[np.where(raster_old_data == 11)] = 10
    raster_new_data[np.where(raster_new_data == 11)] = 10

    # reclassify forest classes
    raster_old_data[np.where(raster_old_data == 50)] = 5000
    raster_new_data[np.where(raster_new_data == 50)] = 5000

    # create a land cover change image
    lcChange = raster_new_data - raster_old_data

    # reclassify
    lcChange[np.where(lcChange < 4000)] = 0
    lcChange = 5000 - lcChange
    lcChange[np.where(lcChange == 5000)] = 0

    # add dimension in order to export
    lcChange = np.reshape(lcChange, newshape=(1, raster_old.RasterYSize, raster_old.RasterXSize))
    make_raster(in_ds=raster_old,
                fn=str(path_data_inter / f'lc_change/landcover_change_{str(year)}_{str(year + 1)}_reforest.tiff'),
                data=lcChange,
                data_type=gdal.GDT_Int16,
                nr_bands=1,
                nodata=None)

    # logging info
    logging.info(f"Done processing re- and afforestation from {str(year)} to {str(year + 1)}")

# create binary change raster without modifying original classes (from masked and cropped maps)
for year in range(1992, 2019):
    # input Raster
    raster_old_path = [lc for lc in files_mask_list if str(year) in str(lc)]
    raster_new_path = [lc for lc in files_mask_list if str(year + 1) in str(lc)]

    # open raster files
    raster_old = gdal.Open(str(raster_old_path[0]))
    raster_new = gdal.Open(str(raster_new_path[0]))

    # read bands as matrix arrays
    raster_old_data = raster_old.GetRasterBand(1).ReadAsArray().astype(int)
    raster_new_data = raster_new.GetRasterBand(1).ReadAsArray().astype(int)

    # reclassify crop classes
    raster_old_data[np.where(raster_old_data == 11)] = 10
    raster_new_data[np.where(raster_new_data == 11)] = 10

    # reclassify forest classes
    raster_old_data[np.where(raster_old_data == 50)] = 5000
    raster_new_data[np.where(raster_new_data == 50)] = 5000

    # create a land cover change image
    lcChange = raster_new_data - raster_old_data

    # reclassify
    lcChange[np.where(lcChange < 4000)] = 0
    lcChange = 5000 - lcChange
    lcChange[np.where(lcChange == 5000)] = 0

    # add dimension in order to export
    lcChange = np.reshape(lcChange, newshape=(1, raster_old.RasterYSize, raster_old.RasterXSize))
    make_raster(in_ds=raster_old,
                fn=str(path_data_inter / f'lc_change/landcover_change_{str(year)}_{str(year + 1)}_reforest_masked_copped.tiff'),
                data=lcChange,
                data_type=gdal.GDT_Int16,
                nr_bands=1,
                nodata=None)

    # logging info
    logging.info(f"Done processing re- and afforestation from {str(year)} to {str(year + 1)} masked and cropped")

# exporting ##########################lc_original_##################################################################################
# end time-count and print time stats ##################################################################################
end_time = datetime.datetime.now()
diff = end_time - start_time
days, seconds = diff.days, diff.seconds
hours = days * 24 + seconds // 3600
minutes = (seconds % 3600) // 60
seconds = seconds % 60
logging.info(f'The entire process took {days} days, {hours} hours, {minutes} minutes {seconds} seconds')
