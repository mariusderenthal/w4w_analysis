# !/usr/bin/env python3

# libraries ############################################################################################################
import logging
import pathlib
import datetime
import pandas as pd
import geopandas as gpd
import numpy as np
import fiona
import rasterio
import rasterio.mask
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


# https://stackoverflow.com/questions/53218931/how-to-unnest-explode-a-column-in-a-pandas-dataframe
def unnesting(df, explode):
    idx = df.index.repeat(df[explode[0]].str.len())
    df1 = pd.concat([
        pd.DataFrame({x: np.concatenate(df[x].values)}) for x in explode], axis=1)
    df1.index = idx

    return df1.join(df.drop(explode, 1), how='left')


# https://stackoverflow.com/questions/52443906/pixel-array-position-to-lat-long-gdal-python
def pixel2coord(x, y, raster):
    xoff, a, b, yoff, d, e = raster.GetGeoTransform()

    xp = a * x + b * y + a * 0.5 + b * 0.5 + xoff
    yp = d * x + e * y + d * 0.5 + e * 0.5 + yoff

    return xp, yp


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
pattern_mask = '*masked.tiff'

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

files_mask_list = list((path_data_inter / 'lc_change').glob(pattern_mask))
files_mask = (path_data_inter / 'lc_change').glob(pattern_reforest)
# process ##############################################################################################################
# sampling for quality check
with fiona.open(path_study_area, "r") as shapefile:
    shapes = [feature["geometry"] for feature in shapefile]

with rasterio.open(path_data_inter / 'lc_change/reforested_03_19.tiff') as src:
    out_image, out_transform = rasterio.mask.mask(src, shapes, crop=True, nodata=-1)
    out_meta = src.meta

out_meta.update({"driver": "GTiff",
                 "height": out_image.shape[1],
                 "width": out_image.shape[2],
                 "transform": out_transform})

with rasterio.open(path_data_inter / 'lc_change/reforested_03_19_study_area.tiff', "w", **out_meta) as dest:
    dest.write(out_image)

# remove first dimension in order to get descriptive values
out_image_mod = np.squeeze(out_image)
# get unique land cover classes and their counts
unique, counts = np.unique(out_image_mod, return_counts=True)
# create dictionary from unique land cover classes and their counts
lc_classes = dict(zip(unique, counts))
# delete entries outside the study area
del lc_classes[-1]

# total amount of pixel
lc_classes_tot = sum(lc_classes.values())
# share of pixel which have not changed over time
lc_classes_no = lc_classes.get(0) / lc_classes_tot
# share of pixel which have changed over time
lc_classes_yes = 1 - lc_classes_no
# total pixels which have changed
lc_classes_yes_tot = int(lc_classes_yes * lc_classes_tot)
# share of each class
lc_classes_10 = lc_classes.get(10) / lc_classes_yes_tot  # cropland rainfed
lc_classes_30 = lc_classes.get(30) / lc_classes_yes_tot  # mosaic cropland
lc_classes_40 = lc_classes.get(40) / lc_classes_yes_tot  # mosaic natural vegetatio
lc_classes_120 = lc_classes.get(120) / lc_classes_yes_tot  # shrubland
lc_classes_180 = lc_classes.get(180) / lc_classes_yes_tot  # shrub herbaceous cover flooded

# create empty data frame to store spectral information
df = pd.DataFrame(columns={'lc': [],
                           # 'Band01': [],
                           # 'Band02': [],
                           })

# create empty data frame to store sample point information
sample_p = pd.DataFrame(columns={'x': [],
                                 'y': [],
                                 'class': []})

# perform stratified random sampling (20/class)
classes = list(lc_classes.keys())
for classy in classes[1:]:
    inds = np.transpose(np.where(out_image_mod == classy))

    if inds.shape[0] >= 20:
        samplesize = 20
    else:
        samplesize = inds.shape[0]

    i = np.random.choice(inds.shape[0], samplesize, replace=False)
    indsselected = inds[i, :]
    lc = out_image_mod[indsselected[:, 0], indsselected[:, 1]]

    # store spectral information in data frame
    df = df.append({'lc': lc,
                    # 'Band06': pixel_v[5]
                    # 'Band07': pixel_v[6],
                    # 'Band08': pixel_v[7],
                    # 'Band09': pixel_v[8],
                    },
                   ignore_index=True)

    # store sample point information in data frame
    sample_p = sample_p.append({'x': indsselected[:, 0],
                                'y': indsselected[:, 1],
                                'class': classy},
                               ignore_index=True)

# unnest/explode spectral information within data frame
df_samples = unnesting(df, ['lc'])

# unnest/explode sample point information within data frame
sample_points = unnesting(sample_p, ['x', 'y'])

ds = gdal.Open(str(path_data_inter / 'lc_change/reforested_03_19_study_area.tiff'))

sample_points['x_coords'], sample_points['y_coords'] = pixel2coord(sample_points['y'], sample_points['x'], ds)
sample_points_gdf = gpd.GeoDataFrame(sample_points,
                                     geometry=gpd.points_from_xy(sample_points.x_coords, sample_points.y_coords))
sample_points_gdf.set_crs(epsg=4326, inplace=True)
sample_points_gdf.to_file(path_data_inter / "sample_points/sample_points_quality_check_20_study_area.gpkg", driver="GPKG")

# exporting ############################################################################################################

# end time-count and print time stats ##################################################################################
end_time = datetime.datetime.now()
diff = end_time - start_time
days, seconds = diff.days, diff.seconds
hours = days * 24 + seconds // 3600
minutes = (seconds % 3600) // 60
seconds = seconds % 60
logging.info(f'The entire process took {days} days, {hours} hours, {minutes} minutes {seconds} seconds')
