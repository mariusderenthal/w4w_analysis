
# !/usr/bin/env python3

# libraries ############################################################################################################
import logging
import pathlib
import datetime
import richdem as rd

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

# dem
path_dem = path_data_inter / 'dem/srtm_22_11_resample.tif'


# global variables #####################################################################################################

# process ##############################################################################################################
dem = rd.LoadGDAL(str(path_dem))
slope = rd.TerrainAttribute(dem, attrib='slope_riserun')
aspect = rd.TerrainAttribute(dem, attrib='aspect')
curvature = rd.TerrainAttribute(dem, attrib='curvature')
# exporting ############################################################################################################
rd.SaveGDAL(str(path_data_inter/'dem/srtm_22_11_resample_slope.tif'), slope)
rd.SaveGDAL(str(path_data_inter/'dem/srtm_22_11_resample_aspect.tif'), aspect)
rd.SaveGDAL(str(path_data_inter/'dem/srtm_22_11_resample_curvature.tif'), curvature)

# end time-count and print time stats ##################################################################################
end_time = datetime.datetime.now()
diff = end_time - start_time
days, seconds = diff.days, diff.seconds
hours = days * 24 + seconds // 3600
minutes = (seconds % 3600) // 60
seconds = seconds % 60
logging.info(f'The entire process took {days} days, {hours} hours, {minutes} minutes {seconds} seconds')
