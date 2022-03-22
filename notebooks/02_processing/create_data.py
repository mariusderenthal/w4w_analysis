# !/usr/bin/env python3

# libraries ############################################################################################################
import logging
import pathlib
import datetime
import pandas as pd
import geopandas as gpd
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
def min_distance(point, lines):
    return lines.distance(point).min()


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
path_river = path_data_inter / 'rivers/rio_sogamoso.gpkg'
path_study_area = path_data_inter / 'study_area/study_area.gpkg'

# landcover
path_landcover_92_19 = path_data_raw / 'LC_CCI_ESA_COL'

# ofertas ambiental igac
path_oferta_ambiental = path_data_raw / 'igac/ofertas_ambiental.gpkg'

# points
path_points = path_data_inter / 'sample_points/sample_points_v2.gpkg'

# dem
path_alt = path_data_inter /    'dem/srtm_22_11_resample.tif'
path_slope = path_data_inter /  'dem/srtm_22_11_resample_slope.tif'
path_curv = path_data_inter /   'dem/srtm_22_11_resample_curvature.tif'
path_aspect = path_data_inter / 'dem/srtm_22_11_resample_aspect.tif'

# soil
path_awcts = path_data_inter /  'soil/AWCtS_M_sl4_250m_ll.crop_resample.tif'
path_wwp = path_data_inter /    'soil/WWP_M_sl4_250m_ll.crop_resample.tif'
path_orcdrc = path_data_inter / 'soil/ORCDRC_M_sl4_250m_ll.crop_resample.tif'
path_phinox = path_data_inter / 'soil/PHIHOX_M_sl4_250m_ll.crop_resample.tif'

# distance pop
path_dis_pop = path_data_raw / 'access/2015_accessibility_to_cities_v1.0/2015_accessibility_to_cities_v1.0_crop_resamp.tif'

# distance roads
path_roads = path_data_inter / 'roads/osm_roads.gpkg'
path_vias = path_data_inter / 'roads/vias_santander.gpkg'

# palm_oil
path_palm_oil = path_data_raw / 'palm_oil/Universal_Mill_List-shp/Universal_Mill_List.shp'

# global variables #####################################################################################################
# process ##############################################################################################################
logging.info("Load points")
points = gpd.read_file(path_points)
logging.info("Load study area")
study_area = gpd.read_file(path_study_area)

'''
# read study area and use negative buffer in order to only get point which actually have neighbours
logging.info("Filter points with buffer process")
study_area = gpd.read_file(path_study_area)
study_area.to_crs(epsg=3116, inplace=True)
study_area = study_area.dissolve()
exter_poly = Polygon(np.array(study_area.exterior)[0])
study_area = gpd.GeoDataFrame({'geometry': exter_poly, 'df1': [1]})

study_area_buffer = gpd.GeoDataFrame(study_area.buffer(-450)).rename(columns={0: 'geometry'}).set_geometry('geometry')
study_area_buffer.set_crs(epsg=3116, inplace=True)
study_area_buffer.to_crs(epsg=4326, inplace=True)
# study_area_buffer.to_file(path_data_inter / "study_area/study_area_buffer.gpkg", driver="GPKG")
points_buffer = gpd.clip(points, study_area_buffer)
# points_buffer.to_file(path_data_inter / "sample_points/sample_points_buffer.gpkg", driver="GPKG")
del points, study_area
'''
points_buffer = points
# get altitude, slope, aspect and curvature info for each point
logging.info("Get altitude, slope, aspect and curvature info per point")
points_buffer.index = range(len(points_buffer))
coords = [(x, y) for x, y in zip(points_buffer.x_coords, points_buffer.y_coords)]

altitude = rasterio.open(path_alt)
points_buffer['altitude'] = [x[0] for x in altitude.sample(coords)]
del altitude

slope = rasterio.open(path_slope)
points_buffer['slope'] = [x[0] for x in slope.sample(coords)]
del slope

curv = rasterio.open(path_curv)
points_buffer['curvature'] = [x[0] for x in curv.sample(coords)]
del curv

aspect = rasterio.open(path_aspect)
points_buffer['aspect'] = [x[0] for x in aspect.sample(coords)]
del aspect

# get soil attributes info for each point
logging.info("Get soil info per point")

AWcTS = rasterio.open(path_awcts)
points_buffer['AWcTS'] = [x[0] for x in AWcTS.sample(coords)]
del AWcTS

WWP = rasterio.open(path_wwp)
points_buffer['WWP'] = [x[0] for x in WWP.sample(coords)]
del WWP

ORCDRC = rasterio.open(path_orcdrc)
points_buffer['ORCDRC'] = [x[0] for x in ORCDRC.sample(coords)]
del ORCDRC

PHIHOX = rasterio.open(path_phinox)
points_buffer['PHIHOX'] = [x[0] for x in PHIHOX.sample(coords)]
del PHIHOX

# get distance to populated center 2015 info for each point
logging.info("Get distance to populated center 2015 per point")
dist_pop = rasterio.open(path_dis_pop)
points_buffer['dist_pop'] = [x[0] for x in dist_pop.sample(coords)]
del dist_pop

# get municpalties attributes info for each point
logging.info("Get municpalties info per point")
municipality = gpd.read_file(path_munic)
municipality = municipality[['MPIO_CNM_1', 'geometry']]
points_buffer = gpd.sjoin(points_buffer, municipality, op='within')
del municipality

# get oferta ambiental info for each point
logging.info("Get oferta ambiental info per point")
oferta_ambiental = gpd.read_file(path_oferta_ambiental)
oferta_ambiental = oferta_ambiental[['Oferta_Amb', 'geometry']]
oferta_ambiental.to_crs(epsg=4326, inplace=True)
del points_buffer['index_right']
points_buffer = gpd.sjoin(points_buffer, oferta_ambiental, op='within')
del oferta_ambiental

# get distance to river info for each point
logging.info("Get distance to river per point")
river = gpd.read_file(path_river)
river.to_crs(epsg=3116, inplace=True)
points_buffer.to_crs(epsg=3116, inplace=True)
river.sindex
points_buffer.sindex

points_buffer['dist_river'] = points_buffer.geometry.apply(min_distance, args=(river,))
del river

# get distance to oil palm mill info for each point
logging.info("Get distance to palm oil info per point")
palm_oil = gpd.read_file(path_palm_oil)
palm_oil_SA = gpd.clip(palm_oil, study_area)
palm_oil_SA.to_crs(epsg=3116, inplace=True)

points_buffer['dist_po_mill'] = points_buffer.geometry.apply(min_distance, args=(palm_oil_SA,))
del palm_oil, palm_oil_SA

# get distance to closest osm street info for each point
logging.info("Get distance to closest street per point")
osm_streets = gpd.read_file(path_roads)
osm_streets_SA = gpd.clip(osm_streets, study_area)
osm_streets_SA.to_crs(epsg=3116, inplace=True)

points_buffer['dist_road_osm'] = points_buffer.geometry.apply(min_distance, args=(osm_streets_SA,))
del osm_streets, osm_streets_SA

# get distance to closest via info for each point
logging.info("Get distance to closest street per point")
vias_streets = gpd.read_file(path_vias)
vias_streets_SA = gpd.clip(vias_streets, study_area)
vias_streets_SA.to_crs(epsg=3116, inplace=True)

points_buffer['dist_road_vias'] = points_buffer.geometry.apply(min_distance, args=(vias_streets_SA,))
del vias_streets, vias_streets_SA

points_buffer['dist_road'] = points_buffer[['dist_road_osm','dist_road_vias']].min(axis=1)


# get distance to nearest afforested in previous year
logging.info("Get distance to nearest afforested cell per point")
for year in range(2004, 2020):
    mask = (points_buffer['year'] == year)
    points_buffer_valid = points_buffer[(points_buffer['year'] == year)]
    past = points_buffer[(points_buffer['year'] == year - 1) & (points_buffer['afforestation'] == 1)]
    points_buffer.loc[mask, 'dist_afforestation'] = points_buffer_valid.geometry.apply(min_distance, args=(past,))
    logging.info(f"Get distance to afforestation for year {year}/{year - 1}")

# get landcover share infor per point
logging.info("Get landcover share in queens neighbourhood")
# Create a buffered polygon layer from your plot location points
points_buffer_poly = points_buffer.copy()
points_buffer_poly["geometry"] = points_buffer.geometry.buffer(450)
del points_buffer['index_right']
del points_buffer_poly['index_right']

dn = []
for year in range(2003, 2020):
    # filter year
    polys = points_buffer_poly[points_buffer_poly['year'] == year]
    points = points_buffer[points_buffer['year'] == year]

    # perform sjoin
    poly_point = gpd.sjoin(polys, points[['geometry', 'class']], op='contains')

    # data wrangling
    poly_point_pivot = pd.pivot_table(poly_point, index=poly_point.index, columns='class_right',
                                      aggfunc={'class_right': len})
    poly_point_pivot.columns = poly_point_pivot.columns.droplevel()

    result = polys.merge(poly_point_pivot, how='left', on=poly_point_pivot.index)
    dn.append(result)
    logging.info(f'Done getting neighbours for {year}')

df = pd.concat(dn)
df.reset_index(drop=True, inplace=True)
df.loc[df['class'] == '10', '10'] = df['10'] - 1
df.loc[df['class'] == '30', '30'] = df['30'] - 1
df.loc[df['class'] == '40', '40'] = df['40'] - 1
df.loc[df['class'] == '50', '50'] = df['50'] - 1
df.loc[df['class'] == '120', '120'] = df['120'] - 1

df['neigh_tot'] = df.iloc[:, -5:].sum(axis=1)

# tidy data
logging.info("Tidy dat before export")
del df['key_0'], df['class_re']
df["geometry"] = df.geometry.centroid

# exporting ############################################################################################################
df.to_file(path_data_output / "sample_points/sample_points_0311.gpkg", driver="GPKG")
df.to_csv(path_data_output / "sample_points/sample_points_0311.csv")

# end time-count and print time stats ##################################################################################
end_time = datetime.datetime.now()
diff = end_time - start_time
days, seconds = diff.days, diff.seconds
hours = days * 24 + seconds // 3600
minutes = (seconds % 3600) // 60
seconds = seconds % 60
logging.info(f'The entire process took {days} days, {hours} hours, {minutes} minutes {seconds} seconds')
