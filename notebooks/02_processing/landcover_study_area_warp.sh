declare -a years_past=( $(seq 1992 2019) )
	
for YEAR_past in "${years_past[@]}"; do 
	gdalwarp -overwrite -of Gtiff -co COMPRESS=DEFLATE -co TILED=YES -ot Byte -cutline ../../data/02_intermediate/study_area/study_area.gpkg -crop_to_cutline ../../data/02_intermediate/lc_change/lc_original_${YEAR_past}_masked.tiff ../../data/02_intermediate/lc_change/lc_original_${YEAR_past}_masked_cropped.tiff
done