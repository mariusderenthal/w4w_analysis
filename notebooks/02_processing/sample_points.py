# !/usr/bin/env python3

# libraries ############################################################################################################
import logging
import pathlib
import datetime
import pandas as pd
import geopandas as gpd
import numpy as np
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
# process ##############################################################################################################
# create empty data frame to store spectral information
df = pd.DataFrame(columns={'lc': [],
                           # 'Band01': [],
                           # 'Band02': [],
                           })

# create empty data frame to store sample point information
sample_p = pd.DataFrame(columns={'x': [],
                                 'y': [],
                                 'class': [],
                                 'year': []})

classes = [10, 30, 40, 120, 50]
for year in range(2003, 2020):

    year_lc_path = [lc for lc in files_mask_list if str(year) in str(lc)]
    # open raster files
    year_lc = gdal.Open(str(year_lc_path[0]))

    # read bands as matrix arrays
    year_lc_data = year_lc.GetRasterBand(1).ReadAsArray().astype(int)

    # get unique land cover classes and their counts
    # unique, counts = np.unique(year_lc_data, return_counts=True)
    # create dictionary from unique land cover classes and their counts
    # lc_classes = dict(zip(unique, counts))

    # reclassify crop classes
    year_lc_data[np.where(year_lc_data == 11)] = 10

    for classy in classes:
        inds = np.transpose(np.where(year_lc_data == classy))

        samplesize = inds.shape[0]

        i = np.random.choice(inds.shape[0], samplesize, replace=False)
        indsselected = inds[i, :]
        lc = year_lc_data[indsselected[:, 0], indsselected[:, 1]]

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
                                    'class': classy,
                                    'year': year},
                                   ignore_index=True)

    # logging info
    logging.info(f"Done creating points for classes 10, 30, 40 in {str(year)}")

# unnest/explode spectral information within data frame
df_samples = unnesting(df, ['lc'])

# unnest/explode sample point information within data frame
sample_points = unnesting(sample_p, ['x', 'y'])

sample_points['x_coords'], sample_points['y_coords'] = pixel2coord(sample_points['y'], sample_points['x'], year_lc)
sample_points_gdf = gpd.GeoDataFrame(sample_points,
                                     geometry=gpd.points_from_xy(sample_points.x_coords, sample_points.y_coords))
sample_points_gdf.set_crs(epsg=4326, inplace=True)

# sample_points_gdf.to_file(path_data_inter / "sample_points/sample_points_first_draft.gpkg", driver="GPKG")

# get afforestation info
sample_points_gdf['count'] = sample_points_gdf.groupby(['x', 'y'])['x'].transform('size')
sample_points_gdf['year'] = sample_points_gdf['year'].astype(int)

# remove plots which inlcude other classes
sample_points_gdf = sample_points_gdf[(sample_points_gdf['count'] == 17)]

# remove plots which are only forest
mask = (sample_points_gdf['class'] == 50)
sample_points_gdf_valid = sample_points_gdf[(sample_points_gdf['class'] == 50)]
sample_points_gdf.loc[mask, 'count_forest'] = sample_points_gdf_valid.groupby(['x', 'y'])['class'].transform('count')
sample_points_gdf = sample_points_gdf[(sample_points_gdf['count_forest'] != 17)]

# add plot id
sample_points_gdf['plot_id'] = sample_points_gdf.groupby(['x', 'y']).ngroup().add(1)

# get plot id where there is forest at some point in time
plot_candidates = sample_points_gdf.loc[sample_points_gdf['count_forest'] >= 1]['plot_id'].unique()

# change forest values so it becomes the biggest
sample_points_gdf['class_re'] = sample_points_gdf['class'].map({50: 5000, 10: 1, 30: 1, 40: 1, 120: 1})
sample_points_gdf['afforestation'] = 0
sample_points_gdf.reset_index(drop=True, inplace=True)

dn = []
for plot_id in plot_candidates:
    mask = sample_points_gdf['plot_id'] == plot_id
    plots_valid = sample_points_gdf[(sample_points_gdf['plot_id'] == plot_id)]
    plots_valid['diff'] = plots_valid['class_re'].diff()

    year_afforestation = plots_valid[(plots_valid['diff'] > 0)]['year']

    if year_afforestation.size == 0:
        continue
    else:
        year_afforestation = year_afforestation.values[0] - 1
        ids = sample_points_gdf.loc[mask].year == year_afforestation
        ids = ids[ids].index.values[0]
        dn.append(ids)

sample_points_gdf.loc[dn, 'afforestation'] = 1

# exporting ############################################################################################################
sample_points_gdf.to_file(path_data_inter / "sample_points/sample_points_v2.gpkg", driver="GPKG")
sample_points_gdf.to_csv(path_data_inter / "sample_points/sample_points_v2.csv")

# end time-count and print time stats ##################################################################################
end_time = datetime.datetime.now()
diff = end_time - start_time
days, seconds = diff.days, diff.seconds
hours = days * 24 + seconds // 3600
minutes = (seconds % 3600) // 60
seconds = seconds % 60
logging.info(f'The entire process took {days} days, {hours} hours, {minutes} minutes {seconds} seconds')
