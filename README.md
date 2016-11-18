# GeoHackWeek 2016 #ReMap Project

A hack week project to locate optimal sites for renewable energy power plants using random forest classification and Google Earth Engine (GEE).

## Methodology

1. Load satellite and ground based datasets of features considered useful for determining renewable energy potential (eg. solar irradiance, wind speed).
- solar irradiance: GRIDMET: University of Idaho Gridded Surface Meteorological Dataset https://code.earthengine.google.com/dataset/IDAHO_EPSCOR/GRIDMET
    4km resolution, srad: surface downward shortwave radiation (W/m^2)
2. Locate sites of existing renewable energy power plants (solar, wind and geothermal).
3. Extract a list of feature values at pixels where renewable energy plants are located to form a training dataset.
4. Feed the training data to a random forest classifier.
5. Use the trained classifier to predict which of the 3 types of renewable energy would be best suited to land across the US.
6. Mask areas of importance or impracticality (eg. forest canopy, water, steep slopes)

## Google Earth Engine Script
[Click here to view and play with the final version of the script in the GEE code editor.](https://code.earthengine.google.com/2aedec5fe5afc721e827c75dac224167)

[Renewable Prospecting Hackpad](https://hackpad.com/Locating-sites-for-renewable-energy-systems-oQpOwjD8Pts)


