# !/usr/bin/env python3

# libraries ############################################################################################################
import logging
import pathlib
import datetime
import geopandas as gpd

# settings #############################################################################################################
# set logging config
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d, %b, %Y, %H:%M:%S',
                    # filename = 'tidy_data.log'
                    )

# set time count
start_time = datetime.datetime.now()
logging.info("starting process")


# functions ############################################################################################################
# source: https://automating-gis-processes.github.io/site/notebooks/L2/calculating-distances.html
def calculate_distance(row, dest_geom, src_col='geometry', target_col='distance'):
    """
    Calculates the distance between Point geometries.

    Parameters
    ----------
    dest_geom : shapely.Point
       A single Shapely Point geometry to which the distances will be calculated to.
    src_col : str
       A name of the column that has the Shapely Point objects from where the distances will be calculated from.
    target_col : str
       A name of the target column where the result will be stored.

    Returns
    -------

    Distance in kilometers that will be stored in 'target_col'.
    """

    # Calculate the distances
    dist = row[src_col].centroid.distance(dest_geom)

    # Convert into kilometers
    dist_km = dist / 1000

    # Assign the distance to the original data
    row[target_col] = dist_km
    return row


# folder path ##########################################################################################################
path_current = pathlib.Path.cwd()
path_src = path_current / 'src'
path_notebooks = path_current / 'notebooks'
path_data = path_current / 'data'
path_data_raw = path_data / '01_raw'
path_data_inter = path_data / '02_intermediate'
path_data_output = path_data / '03_processed'

path_admin = path_data_raw / 'admin_areas' / 'col_second_level_admin_boundaries' / 'col_second_level_admin_boundaries.shp'
path_catch = path_data_raw / 'catchment_areas' / 'hydrosheds-de3a202db76ddd93c689' / 'hybas_sa_lev00_v1c' / 'hybas_sa_lev00_v1c.shp'
path_dam = path_data_raw / 'dam_locations' / 'GRanD_Version_1_3' / 'GRanD_dams_v1_3.shp'
path_river = path_data_inter / 'rivers' / 'rio_sogamoso.gpkg'

path_palm_rspo = path_data_raw / 'palm_oil' / 'Agro-industry' / 'Agro-industry.shp'
path_palm_planted = path_data_raw / 'palm_oil' / 'plantations_v1_3_dl.gdb'

# global variables #####################################################################################################
# admin areas
department_dic = {'Santander': 68}
department_ids = ['68']
municipaltiy_dic = {'Puerto Wilches': '68575',
                    'Sabana de Torres': '68655',
                    'Barrancabermeja': '68081',
                    # 'SAN VICENTE DE CHUCURI':   68689
                    }
municipaltiy_ids = ['68575', '68655', '68081']

palm_oil_buffer = 25

# load data ############################################################################################################
# admin areas
logging.info("loading admin area data")
admin_a = gpd.read_file(path_admin)
admin_a.to_crs(epsg=3116, inplace=True)

'''
# catchment areas
logging.info("loading catchment area data")
catchment_SA = gpd.read_file(path_catch)
catchment_SA.to_crs(epsg=3116, inplace=True)
'''
# river
logging.info("loading river data")
river = gpd.read_file(path_river)
river.to_crs(epsg=3116, inplace=True)

# rspo palm oil plantatiosn
logging.info("loading rspo palm oil plantations")
palm_rspo = gpd.read_file(path_palm_rspo)
palm_rspo.to_crs(epsg=3116, inplace=True)

# planted trees
logging.info("loading planted trees")
# fiona.listlayers(path_palm_planted)
palm_planted = gpd.read_file(path_palm_planted, driver='FileGDB', layer='col_plant')
palm_planted.to_crs(epsg=3116, inplace=True)
# process ##############################################################################################################
# filter municipalities
logging.info("filter municipalities")
municipalties = admin_a[admin_a['MPIO_CCDGO'].isin(municipaltiy_ids)]
del admin_a

# select palm oil columns
palm_rspo = palm_rspo[['Group_', 'Company', 'Plantation', 'RSPOCert', 'MemberYear', 'GlobalID', 'geometry']]
palm_planted = palm_planted[['org_name', 'common_name', 'plant_ag', 'size', 'ownership', 'year', 'geometry']]

# clip rspo palm oil areas with municipalities
logging.info("clip palm oil data  with municipalities")
palm_rspo_SA = gpd.overlay(palm_rspo, municipalties[['MPIO_CNM_1', 'geometry']], how='intersection')
del palm_rspo
palm_planted_SA = gpd.overlay(palm_planted, municipalties[['MPIO_CNM_1', 'geometry']], how='intersection')
del palm_planted

# combine palm oil data
palm_oil_SA = gpd.overlay(palm_rspo_SA, palm_planted_SA, how='union')
del palm_rspo_SA, palm_planted_SA

# buffer palm oil data with 2500 meters
palm_oil_SA_2500 = gpd.GeoDataFrame(palm_oil_SA.geometry.buffer(2500)).rename(columns={0: 'geometry'}).set_geometry(
    'geometry')
palm_oil_SA_2500 = palm_oil_SA_2500.dissolve()
palm_oil_SA_2500 = palm_oil_SA_2500.explode()
palm_oil_SA_2500.reset_index(inplace=True, drop=True)

# select only the exterior
# palm_oil_SA_2500['geometry'] = palm_oil_SA_2500.exterior

logging.info("create 25km buffer around river and clip with municiplaities")
river_25000 = gpd.GeoDataFrame(river.geometry.buffer(25000)).rename(columns={0: 'geometry'}).set_geometry('geometry')
river_buffered = gpd.overlay(river_25000, municipalties, how='intersection')

# clip river buffer with palm oil areas
study_area = gpd.overlay(river_buffered, palm_oil_SA_2500, how='intersection', keep_geom_type=False)
study_area = study_area.explode()
study_area.reset_index(inplace=True, drop=True)

# study_area_ex = gpd.clip(palm_oil_SA_2500, river_buffered.exterior)
# study_area['geometry'] = palm_oil_SA_2500.explode().area/1000000

# select only the biggest polygons
mask = study_area.area / 1000000 > 100  # metres squared
study_area = study_area.loc[mask]

'''
# clip catchment areas with municipalities
logging.info("clip catchment areas with municipalities")
catchment_SA = gpd.overlay(catchment_SA, municipalties, how='intersection')

# create multiple buffers around river and clip with municiplaities
logging.info("create multiple buffers around river and clip with municiplaities")
# buffers = [500, 2000, 5000, 10000, 100000]
river_500 = gpd.GeoDataFrame(river.geometry.buffer(500)).rename(columns={0: 'geometry'}).set_geometry('geometry')
river_2000 = gpd.GeoDataFrame(river.geometry.buffer(2000)).rename(columns={0: 'geometry'}).set_geometry('geometry')
river_5000 = gpd.GeoDataFrame(river.geometry.buffer(5000)).rename(columns={0: 'geometry'}).set_geometry('geometry')
river_10000 = gpd.GeoDataFrame(river.geometry.buffer(10000)).rename(columns={0: 'geometry'}).set_geometry('geometry')
river_25000 = gpd.GeoDataFrame(river.geometry.buffer(25000)).rename(columns={0: 'geometry'}).set_geometry('geometry')
river_50000 = gpd.GeoDataFrame(river.geometry.buffer(50000)).rename(columns={0: 'geometry'}).set_geometry('geometry')
river_150000 = gpd.GeoDataFrame(river.geometry.buffer(150000)).rename(columns={0: 'geometry'}).set_geometry('geometry')

river_150000 = gpd.overlay(river_150000, river_50000, how='difference')
river_50000 = gpd.overlay(river_50000, river_25000, how='difference')
river_25000 = gpd.overlay(river_25000, river_10000, how='difference')
river_10000 = gpd.overlay(river_10000, river_5000, how='difference')
river_5000 = gpd.overlay(river_5000, river_2000, how='difference')
river_2000 = gpd.overlay(river_2000, river_500, how='difference')

river_150000['buffer'] = 150000
river_50000['buffer'] = 50000
river_25000['buffer'] = 25000
river_10000['buffer'] = 10000
river_5000['buffer'] = 5000
river_2000['buffer'] = 2000
river_500['buffer'] = 500

riverList = [river_500, river_2000, river_5000, river_10000, river_25000, river_50000,
             river_150000]  # List of your dataframes
river_buffered = pd.concat(riverList)
river_buffered = gpd.overlay(river_buffered, municipalties, how='intersection')
'''

# reproject to 4326
logging.info("reproject output files to 4326")
study_area.to_crs(epsg=4326, inplace=True)
# municipalties.to_crs(epsg=4326, inplace=True)
# catchment_SA.to_crs(epsg=4326, inplace=True)
# river_buffered.to_crs(epsg=4326, inplace=True)
'''
river_buffered = gpd.GeoDataFrame(columns=['geometry'])
for b in buffers:
    data = river.geometry.buffer(b)
    river_buffered = river_buffered.append(data.geometry, ignore_index=True)

river_buffered.columns = ['nothing', 'geometry']
river_buffered = river_buffered.set_geometry("geometry")
del river_buffered['nothing']
river_buffered.set_crs(epsg=3116, inplace=True)
for index in reversed(river_buffered.index._range):
    river_buffered.iloc[index] = gpd.overlay(river_buffered.iloc[index], river_buffered.iloc[index-1], how='difference')

river_buffered = gpd.overlay(river_buffered, river_buffered, how='symmetric_difference')
gdf.set_geometry(gdf.difference(intersection)).append(summed, ignore_index=True)
'''
# delete unnecessary columns
useless_cols = ['DPTO_CNMBR', 'MPIO_CNMBR', 'MPIO_CRSLC', 'MPIO_NANO', 'OBJECTID',
                'NEXT_SINK', 'MAIN_BAS', 'ENDO', 'COAST', 'PFAF_1', 'PFAF_2', 'PFAF_3', 'PFAF_4']

# municipalties = municipalties[municipalties.columns[~municipalties.columns.isin(useless_cols)]]
study_area = study_area[study_area.columns[~study_area.columns.isin(useless_cols)]]
# catchment_SA = catchment_SA[catchment_SA.columns[~catchment_SA.columns.isin(useless_cols)]]
# river_buffered = river_buffered[river_buffered.columns[~river_buffered.columns.isin(useless_cols)]]

# exporting ############################################################################################################
study_area.to_file(path_data_inter / "study_area/study_area.gpkg", driver="GPKG")
# catchment_SA.to_file(path_data_inter / "study_area/catchments_SA.gpkg", driver="GPKG")
# river_buffered.to_file(path_data_inter / "study_area/river_buffer.gpkg", driver="GPKG")
# municipalties.to_file(path_data_inter / "study_area/municipalties_SA.gpkg", driver="GPKG")

# end time-count and print time stats ##################################################################################
end_time = datetime.datetime.now()
diff = end_time - start_time
days, seconds = diff.days, diff.seconds
hours = days * 24 + seconds // 3600
minutes = (seconds % 3600) // 60
seconds = seconds % 60
logging.info(f'The entire process took {days} days, {hours} hours, {minutes} minutes {seconds} seconds')
