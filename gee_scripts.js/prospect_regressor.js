//---------------// IMPORTS //---------------//
var fusionTable = ee.FeatureCollection("ft:1EMpOeVWKIRau3LGoBmPaezI4_XRHXvAsAOfwu-M"),
    srtm = ee.Image("USGS/SRTMGL1_003"),
    gridmet = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET"),
    PP = ee.FeatureCollection("ft:1HYT3PAAc2JtCfolvBPNqUINBdKmEiPSaL5726fPD"),
    landCover2011 = ee.Image("USGS/NLCD/NLCD2011"),
    thermal = ee.Image("users/samhooperstudio/thermal_gradient"),
    pop = ee.Image("users/samhooperstudio/population"),
    reserveland = ee.FeatureCollection("ft:1h1EF1wI96fd9CW-S3LOPP_Pn4UdpmlwroqDE_7wc");
//---------------// PARAMETERS //---------------//
var forestthreshold = 50  // threshold for masking out forest area
var imperviousthreshold = 30 // threshold for masking out impervious areas
var slopeThreshold = 45

//---------------// DATA //---------------//
// extract only renewables from data and merge into one featureCollection
var justSolar = PP.filter(ee.Filter.eq('PrimSource','solar'));
var justGeo = PP.filter(ee.Filter.eq('PrimSource','geothermal'));
var justWind = PP.filter(ee.Filter.eq('PrimSource','wind'));
var allRenewables = justSolar.merge(justGeo).merge(justWind);
var windSample = allRenewables.remap([0, 1, 2], [1, 0, 0], 'nameindex');
var solarSample = allRenewables.remap([0, 1, 2], [0, 1, 0], 'nameindex');
var thermSample = allRenewables.remap([0, 1, 2], [0, 0, 1], 'nameindex');

//---------------// MAP BOUNDARY //---------------//
// import US map boundary
var country = ee.FeatureCollection('ft:1N2LBk4JHwWpOY4d9fobIn27lfnZ5MDy-NoqqRpk', 'geometry');
var usBoundary = country.filter(ee.Filter.eq('ISO_2DIGIT', 'US'));

//---------------// MASKING //---------------//
var openwater = landCover2011.select('landcover').eq(11)
var watermask = openwater.mask(openwater)

var denseforest = landCover2011.select('percent_tree_cover').gt(forestthreshold)
var forestmask = denseforest.mask(denseforest)

var impervious = landCover2011.select('impervious').gt(imperviousthreshold)
var imperviousmask = impervious.mask(impervious)

//---------------// MAP LAYERS //---------------//
// create image collection using image of first variable from satellite data
// windspeed
var windspeed = ee.Image(ee.ImageCollection(gridmet).filterDate('2010-01-01', '2011-01-01')
   .select('vs').mean());
// srad
var srad = ee.Image(ee.ImageCollection(gridmet).filterDate('2010-01-01', '2011-01-01').select('srad').mean());
// elevation  
var elevation = ee.Image(srtm).select('elevation');
// slope
var slope = ee.Terrain.slope(elevation);
//aspect
var aspect = ee.Terrain.aspect(elevation)

// collate all variables into one image by adding all bands to first collection
var predictors = (windspeed
    .addBands(elevation)
    .addBands(srad)
    .addBands(aspect)
    .addBands(slope)
    .addBands(thermal)
    .addBands(pop)
    );

// useful list of band names
var bands = ['vs',
            'srad',
            'elevation',
            'aspect',
            'slope',
            'b1',
            'b1_1'
            ];
            
//---------------// CLASSIFICATION //---------------//
// extract training data from points on map with existing renewable sites
var trainingAll = predictors.sampleRegions(allRenewables, ['nameindex'], 30);
var trainingWind = predictors.sampleRegions(windSample, ['nameindex'], 30);
var trainingSolar = predictors.sampleRegions(solarSample, ['nameindex'], 30);
var trainingTherm = predictors.sampleRegions(thermSample, ['nameindex'], 30);

// create a trained classifier
var trainedAll = ee.Classifier.randomForest({numberOfTrees:500, bagFraction:0.63, outOfBagMode:true})
  .train(trainingAll, 'nameindex', bands);
var trainedWind = ee.Classifier.randomForest({numberOfTrees:500, bagFraction:0.63, outOfBagMode:true})
  .setOutputMode('REGRESSION')
  .train(trainingWind, 'nameindex', bands);
var trainedSolar = ee.Classifier.randomForest({numberOfTrees:500, bagFraction:0.63, outOfBagMode:true})
  .setOutputMode('REGRESSION')
  .train(trainingSolar, 'nameindex', bands);
var trainedTherm = ee.Classifier.randomForest({numberOfTrees:500, bagFraction:0.63, outOfBagMode:true})
  .setOutputMode('REGRESSION')
  .train(trainingTherm, 'nameindex', bands);

// classify rest of the map based on bands using the trained classifier
var classifiedAll = predictors.select(bands).classify(trainedAll);
var classifiedWind = predictors.select(bands).classify(trainedWind);
var classifiedSolar = predictors.select(bands).classify(trainedSolar);
var classifiedTherm = predictors.select(bands).classify(trainedTherm);

// Build a composite of the max suitability for all three types
/*var suitability = ee.Image(classifiedWind)
  .addBands(classifiedSolar)
  .addBands(classifiedTherm)
  .reduce('max');*/
var suitability = classifiedAll
  .where(classifiedAll.eq(0), classifiedWind)
  .where(classifiedAll.eq(1), classifiedSolar)
  .where(classifiedAll.eq(2), classifiedTherm);


// Get a confusion matrix representing resubstitution accuracy.
var trainAccuracy = trainedAll.confusionMatrix();
print('Resubstitution error matrix: ', trainAccuracy);
print('Training user accuracy: ', trainAccuracy.consumersAccuracy());
print('Training producer accuracy: ', trainAccuracy.producersAccuracy());
print('Training overall accuracy: ', trainAccuracy.accuracy());
print('Kappa: ', trainAccuracy.kappa())



//---------------// PRINTING //---------------//

//print(usBoundary)
//print(slope)

//---------------// PLOTTING MAP //---------------//
// mask the classified map of predictions to just the US boundary
var mask = ee.Image.constant(0).int32();
mask = mask.paint(usBoundary, 1);
//classified = classified.updateMask(mask)
classifiedAll = classifiedAll.updateMask(mask);
classifiedWind = classifiedWind.updateMask(mask);
classifiedSolar = classifiedSolar.updateMask(mask);
classifiedTherm = classifiedTherm.updateMask(mask);
suitability = suitability.updateMask(mask);
// plot predicted map!
//Map.addLayer(classified, {min: 0, max: 2, palette: ['blue', 'yellow', 'red']},
//  'classification');
//Map.addLayer(classified_more, {min: 0, max: 2, palette: ['blue', 'yellow', 'red']},
// 'classification_more');
Map.addLayer(classifiedWind, {min:0, max:1}, 'wind suitability', false);
Map.addLayer(classifiedSolar, {min:0, max:1}, 'solar suitability', false);
Map.addLayer(classifiedTherm, {min:0, max:1}, 'geothermal suitability', false);
Map.addLayer(suitability, {min:0, max:1}, 'suitability');
Map.addLayer(classifiedAll, {min: 0, max: 2, palette: ['blue', 'yellow','red'], opacity:0.5}, 'classification_more');
// plot existing renewable sites
Map.addLayer(justGeo,{color:'yellow'},'Geothermal', false);
Map.addLayer(justSolar,{color:'orange'},'Solar', false);
Map.addLayer(justWind,{color:'blue'},'Wind', false);

//---------------// PLOTTING MASKS //---------------//
Map.addLayer(slope.mask(slope.gt(slopeThreshold)), {palette:'gray'}, 'Elevation Mask');
//Map.addLayer(elevation.mask(elevation.gt(2000)), {palette:'white'}, 'Elevation Mask');
Map.addLayer(forestmask,{},'Forest Mask', false);
Map.addLayer(imperviousmask,{},'Impervious Mask', false);
Map.addLayer(watermask,{palette:'9bbff4'},'Water Mask');
Map.addLayer(reserveland,{color:'purple',opacity:0},'Reserve Mask',false)


//---------------// EXPORT PREDICTORS //---------------//
// change conditional to true if you want to export predictor data
if (false) {
Export.table.toDrive({
collection: training,
description: 'trainingData',
fileFormat: 'CSV'
});
}

