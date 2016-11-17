import glob
import time
import os
import sys
import shutil
import pandas as pd
import numpy as np
import cPickle as pickle
from osgeo import gdal

import randomforest as forest

def main(params):

    t0 = time.time()
    print 'Predicting Random Forest... %s\n' % time.ctime(t0)

    # Set optional params to default:
    split_predictors = False

    # Read params and make variables from text
    inputs = forest.read_params(params)
    for i in inputs:
        exec ("{0} = str({1})").format(i, inputs[i])

    # Check that variables were specified in params
    try:
        nodata = int(nodata)
        str_check = train_params, rf_path, in_raster, out_dir
    except NameError as e:
        missing_var = str(e).split("'")[1]
        msg = "Variable '%s' not specified in param file:\n%s" % (missing_var, params)
        raise NameError(msg)

    # Raise an error if the var_txt path doesn't exist. Otherwise, just read it in
    train_dict = forest.read_params(train_params)
    train_txt_bn = os.path.basename(train_dict['var_txt'][:-1])
    var_txt = os.path.join(os.path.dirname(rf_path), train_txt_bn)
    if not os.path.exists(var_txt):
        print ''
        msg = 'Could not find var_txt:\n%s\n' % var_txt
        raise IOError(msg)
    df_var = pd.read_csv(var_txt, sep='\t', index_col='var_name')

    # Make sure vars are sorted alphabetically since they were for training
    pred_vars  = sorted(df_var.index)
    df_var = df_var.reindex(pred_vars)

    #out_dir = os.path.dirname(out_raster)
    if not os.path.exists(out_dir): os.mkdir(out_dir)
    else: print ('WARNING: out_dir already exists:\n%s\nAny existing files ' + \
    'will be overwritten...\n') % out_dir
    shutil.copy2(params, out_dir)

    # Load the Random Forest model
    print 'Loading the RandomForest model from \n%s... \n%s\n' % (rf_path, time.ctime(time.time()))
    with open(rf_path) as f:
        rf_model = pickle.load(f)
    n_features = rf_model.n_features_
    n_vars = len(df_var)
    if n_features != n_vars:
        print ''
        msg = ('Number of features of the Random Forest model does not match the number of variables in df_var.' +\
            '\nPath of Random Forest model: {0}\nPath of var_txt: {1}').format(rf_path, var_txt)
        raise KeyError(msg)

    # Predict
    'Predicting with %s processors... %s' % (rf_model.n_jobs, time.ctime(time.time()))
    t1 = time.time()
    ar_predictors, nodata_mask = forest.get_predictors(df_var, nodata)
    # If the predictions are too large (i.e. cause memory errors), split the predictor array into pieces and predict
    #   separately, then stack them back together
    if split_predictors:
        split_predictors = int(split_predictors)
        predictions = []
        for i, p in enumerate(np.array_split(ar_predictors, split_predictors)):
            t1 = time.time()
            print '\nPredicting for %s of %s pieces of the final array...' % (i + 1, split_predictors)
            predictions.append(rf_model.predict(p))
            print '%.1f minutes' % ((time.time() - t1)/60)
        predictions = np.concatenate(predictions)
        print ''
    else:
        print 'Predicting in one chunk...'
        predictions = rf_model.predict(ar_predictors)
    ar_prediction = np.full(nodata_mask.shape[0], nodata, dtype=np.float32)
    ar_prediction[nodata_mask] = predictions
    del ar_predictors, predictions

    # Get raster info
    ds = gdal.Open(in_raster)
    tx = ds.GetGeoTransform()
    rows = ds.RasterYSize
    cols = ds.RasterXSize
    prj = ds.GetProjection()
    driver = gdal.GetDriverByName('gtiff')
    ul_x, x_res, _, ul_y, _, y_res = tx
    ds = None

    # Save the prediction array to disk
    stamp = os.path.basename(out_dir)
    out_path = os.path.join(out_dir, 'final_%s.tif' % stamp)
    ar_prediction = ar_prediction.reshape(rows, cols)
    forest.array_to_raster(ar_prediction, tx, prj, driver, out_path, gdal.GDT_Float32, nodata)

    if 'test_samples' and 'inventory_txt' in locals():
        df_test = pd.read_csv(test_samples, sep='\t', index_col='obs_id')
        rmse, rmse_true, rmse_false = forest.calc_rmse(ar_prediction, df_test,
                                                       train_dict['target_col'].replace('"',''), nodata)
        auc = forest.calc_auc(ar_prediction, df_test,
                              train_dict['target_col'].replace('"',''), nodata, out_dir)
        df_inv = pd.read_csv(inventory_txt, sep='\t', index_col='stamp')
        df_inv.ix[stamp, ['auc', 'rmse', 'rmse_true', 'rmse_false']] = auc, rmse, rmse_true, rmse_false
        df_inv.to_csv(inventory_txt, sep='\t')
        print ''
        print 'AUC ................... ', auc
        print 'RMSE .................. ', rmse
        print 'RMSE of true values ... ', rmse_true
        print 'RMSE of false values .. ', rmse_false
    else:
        print '\nEither "test_samples" or "inventory_txt" was not specified.' +\
            ' This model will not be evaluated...'


    print '\nTotal runtime: %.1f minutes' % ((time.time() - t0)/60)


if __name__ == '__main__':
    params = sys.argv[1]
    sys.exit(main(params))




