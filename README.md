# GeoHackWeek 2016 #ReMap Project

A hack week project to locate optimal sites for renewable energy power plants using random forest classification and Google Earth Engine (GEE).

## Methodology

1. Load satellite and ground based datasets of features considered useful for determining renewable energy potential (eg. solar irradiance, wind speed).

	* solar irradiance.
	[GRIDMET: University of Idaho Gridded Surface Meteorological Dataset](https://code.earthengine.google.com/dataset/IDAHO_EPSCOR/GRIDMET), 4km resolution, srad: surface downward shortwave radiation (W/m^2)
	
	* wind
	[GRIDMET: University of Idaho Gridded Surface Meteorological Dataset](https://code.earthengine.google.com/dataset/IDAHO_EPSCOR/GRIDMET), 4km resolution, vs: wind velocity at 10 m (m/s)
	
	* Interval Corrected Thermal Gradient for the USA
	From: http://schemas.usgin.org/models/
	Thermal gradient measurement for the depth interval with corrected temperature and terrain corrections applied. Units are °C/km. The csv file was imported and converted to a .shp in QGIS, then interpolated using kernel density using ArcGIS to produce a raster dataset.
	* Population data
	From esri templates (included with ArcGIS software) with 1990 census data as point data. The shapefile was interpolated using IDW in ArcGIS to produce a raster (.tif).
	
	* Geothermal Proceptivity
	From http://www.nrel.gov/gis/data_geothermal.html
	
	* GCS_North_American_1983. This dataset was used for reference purposes only and does not appear in GEE.

2. Locate sites of existing renewable energy power plants (solar, wind and geothermal).
	Power plant locations (U.S.A) were sourced from: http://www.eia.gov/maps/layer_info-m.php. The columns retained for this study are station id, lat, long, solar_MW, wind_MW and geo_MW and a new column powerplant_MW that lists the maximum MW (Mega-Watt) value of the three and so shows where there is a powerplant of this type and the MW. The csv file was converted to a shapefile (.shp) using QGIS and interpolated using IDW in ArcGIS to produce a raster (.tif).

	To upload to GEE, the shp file was read into Google Earth Pro, and save as a kml file. This was read into Google Drive as a Fusion Table. NOTE: in order to work correctly in GEE, columns with 'location' data type that are not lat or lon (e.g. State, City) are removed from the Fusion Table. This Fusion Table can then be read into GEE.
	
3. Extract a list of feature values at pixels where renewable energy plants are located to form a training dataset.
	* GEE prospector.js:  
	`var training = predictors.sampleRegions(allRenewables, ['nameindex'], 30);`
4. Feed the training data to a random forest classifier.
	* GEE prospector.js:  
	`var bands_more = ['vs',
            'srad',
            'elevation',
            'aspect',
            'slope',
            'b1',
            'b1_1'
            ];`  
	* GEE prospector.js:  
	`var trained_more = ee.Classifier.randomForest({numberOfTrees:500, bagFraction:0.63, outOfBagMode:true}).train(training, 'nameindex', bands_more);`
5. Use the trained classifier to predict which of the 3 types of renewable energy would be best suited to land across the US.
	* GEE prospector.js:  
	`var classified_more = predictors.select(bands_more).classify(trained_more);`
6. Mask U.S. and areas of importance or impracticality (eg. forest canopy, water, steep slopes, indian reserves, impervious surface (i.e. cities)
	* U.S. boundaries:  
		GEE prospector.js:  
		`var mask = ee.Image.constant(0).int32();  
		mask = mask.paint(usBoundary, 1);  
		classified_more = classified_more.updateMask(mask);`  
	* Forest canopy, water, impervious surfaces:  
		from [USGS/NLCD/NLCD2011](https://code.earthengine.google.com/dataset/USGS/NLCD)  
		GEE prospector.js examples:  
		`Map.addLayer(slope.mask(slope.gt(slopeThreshold)), {palette:'gray'}, 'Slope Mask');`  
		`Map.addLayer(forestmask,{palette:'088d00'},'Forest Mask 50%',false);`  
		`Map.addLayer(watermask,{palette:'94BFFF'},'Water Mask');`  
		`Map.addLayer(reserveland,{color:'purple',opacity:0},'Reserve Mask',false);`  		

## Google Earth Engine Script
[Click here to view and play with the final version of the script in the GEE code editor.](https://code.earthengine.google.com/2aedec5fe5afc721e827c75dac224167)

[Renewable Prospecting Hackpad](https://hackpad.com/Locating-sites-for-renewable-energy-systems-oQpOwjD8Pts)


