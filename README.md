# GeoHackWeek 2016 #ReMap Project

A hack week project to locate optimal sites for renewable energy power plants using random forest classification and Google Earth Engine (GEE).

## Methodology

1. Load satellite and ground based datasets of features considered useful for determining renewable energy potential (eg. solar irradiance, wind speed).
	1.1 solar irradiance.
	GRIDMET: University of Idaho Gridded Surface Meteorological Dataset https://code.earthengine.google.com/dataset/IDAHO_EPSCOR/GRIDMET
	4km resolution, srad: surface downward shortwave radiation (W/m^2)
	Power Plant Locations (U.S.A.)
	1.2 Power plant locations were sourced from: http://www.eia.gov/maps/layer_info-m.php
	The columns retained for this study are station id, lat, long, solar_MW, wind_MW and geo_MW and a new column powerplant_MW that lists the maximum MW (Mega-Watt) value of the three and so just shows where there is a powerplant of this type and the MW. 
	1.3 Population data
	From esri templates (included with ArcGIS software) with 1990 census data as point data
	1.4 Geothermal Proceptivity
	From http://www.nrel.gov/gis/data_geothermal.html
	This dataset is a qualitative assessment of geothermal potential (Enhanced Geothermal System EGS) for the US based on Levelized Cost of Electricity, with CLASS 1 being most favorable, and CLASS 5 being least favorable. This dataset does not include shallow EGS resources located near hydrothermal sites or USGS assessment of undiscovered hydrothermal resources. The source data for deep EGS includes temperature at depth from 3 to 10 km provided by Southern Methodist University Geothermal Laboratory (Blackwell & Richards, 2009) and analyses (for regions with temperatures equal to or greater than 150Â°C) performed by NREL (2009). CLASS 999 regions have temperatures less than 150Â°C at 10 km depth and were not assessed for deep EGS potential. Temperature at depth data for deep EGS in Alaska and Hawaii not available.
	GCS_North_American_1983
	1.5 Interval Corrected Thermal Gradient for the USA
	From: http://schemas.usgin.org/models/
	Thermal gradient measurement for the depth interval with corrected temperature and terrain corrections applied. Units are °C/km. 

2. Locate sites of existing renewable energy power plants (solar, wind and geothermal).
3. Extract a list of feature values at pixels where renewable energy plants are located to form a training dataset.
4. Feed the training data to a random forest classifier.
5. Use the trained classifier to predict which of the 3 types of renewable energy would be best suited to land across the US.
6. Mask areas of importance or impracticality (eg. forest canopy, water, steep slopes)

## Google Earth Engine Script
[Click here to view and play with the final version of the script in the GEE code editor.](https://code.earthengine.google.com/2aedec5fe5afc721e827c75dac224167)

[Renewable Prospecting Hackpad](https://hackpad.com/Locating-sites-for-renewable-energy-systems-oQpOwjD8Pts)


