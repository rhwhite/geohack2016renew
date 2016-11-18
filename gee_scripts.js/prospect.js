//---------------// IMPORTS //---------------//
var fusionTable = ee.FeatureCollection("ft:1EMpOeVWKIRau3LGoBmPaezI4_XRHXvAsAOfwu-M"),
    srtm = ee.Image("USGS/SRTMGL1_003"),
    gridmet = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET"),
    PP = ee.FeatureCollection("ft:1HYT3PAAc2JtCfolvBPNqUINBdKmEiPSaL5726fPD");

//---------------// DATA //---------------//
// extract only renewables from data and merge into one featureCollection
var justSolar = PP.filter(ee.Filter.eq('PrimSource','solar'))
var justGeo = PP.filter(ee.Filter.eq('PrimSource','geothermal'));
var justWind = PP.filter(ee.Filter.eq('PrimSource','wind'))
var allRenewables = justSolar.merge(justGeo).merge(justWind);

//---------------// MAP BOUNDARY //---------------//
// import US map boundary
var country = ee.FeatureCollection('ft:1N2LBk4JHwWpOY4d9fobIn27lfnZ5MDy-NoqqRpk', 'geometry');
var usBoundary = country.filter(ee.Filter.eq('ISO_2DIGIT', 'US'));

//---------------// MAP LAYERS //---------------//
// create image collection using image of first variable from satellite data
// windspeed
var windspeed = ee.Image(ee.ImageCollection(gridmet).filterDate('2010-01-01', '2011-01-01')
   .select('vs').mean());
// elevation  
var elevation = ee.Image(srtm).select('elevation');
// slope
var slope = ee.Terrain.slope(elevation);

// collate all variables into one image by adding all bands to first collection
var predictors = (windspeed
    .addBands(elevation)
    .addBands(slope));

// useful list of band names 
var bands = ['vs','elevation', 'slope'];

//---------------// CLASSIFICATION //---------------//
// extract training data from points on map with existing renewable sites
var training = predictors.sampleRegions(allRenewables, ['nameindex'], 30);

// create a trained classifier
var trained = ee.Classifier.randomForest().train(training, 'nameindex', bands);

// classify rest of the map based on bands using the trained classifier
var classified = predictors.select(bands).classify(trained);

// Get a confusion matrix representing resubstitution accuracy.
var trainAccuracy = trained.confusionMatrix();
print('Resubstitution error matrix: ', trainAccuracy);
print('Training overall accuracy: ', trainAccuracy.consumersAccuracy());


//---------------// PRINTING //---------------//

//print(usBoundary)
//print(slope)

//---------------// PLOTTING MAP //---------------//
// mask the classified map of predictions to just the US boundary
var mask = ee.Image.constant(0).int32();
mask = mask.paint(usBoundary, 1);
classified = classified.updateMask(mask)
// plot predicted map!
Map.addLayer(classified, {min: 0, max: 2, palette: ['blue', 'yellow', 'red']},
  'classification');
  
// plot existing renewable sites
Map.addLayer(justGeo,{color:'yellow'},'Geothermal', false);
Map.addLayer(justSolar,{color:'orange'},'Solar', false)
Map.addLayer(justWind,{color:'blue'},'Wind', false)

//---------------// PLOTTING MASKS //---------------//
Map.addLayer(slope.mask(slope.gt(45)), {palette:'gray'}, 'Elevation Mask');
Map.addLayer(elevation.mask(elevation.gt(2000)), {palette:'white'}, 'Elevation Mask');

//---------------// EXPORT PREDICTORS //---------------//
// change conditional to true if you want to export predictor data
if (false) {
Export.table.toDrive({
collection: predictors,
description: 'exportVolumes',
fileFormat: 'CSV'
});
}