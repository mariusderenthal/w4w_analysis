gdalwarp -tr 0.002777777777777999495 0.002777777777777999495 -tap -r bilinear ../../data/01_raw/soil/AWCtS_M_sl4_250m_ll.crop.tif ../../data/02_intermediate/soil/AWCtS_M_sl4_250m_ll.crop_resample.tif -overwrite
gdalwarp -tr 0.002777777777777999495 0.002777777777777999495 -tap -r bilinear ../../data/01_raw/soil/WWP_M_sl4_250m_ll.crop.tif ../../data/02_intermediate/soil/WWP_M_sl4_250m_ll.crop_resample.tif -overwrite
gdalwarp -tr 0.002777777777777999495 0.002777777777777999495 -tap -r bilinear ../../data/01_raw/soil/ORCDRC_M_sl4_250m_ll.crop.tif ../../data/02_intermediate/soil/ORCDRC_M_sl4_250m_ll.crop_resample.tif -overwrite
gdalwarp -tr 0.002777777777777999495 0.002777777777777999495 -tap -r bilinear ../../data/01_raw/soil/PHIHOX_M_sl4_250m_ll.crop.tif ../../data/02_intermediate/soil/PHIHOX_M_sl4_250m_ll.crop_resample.tif -overwrite

