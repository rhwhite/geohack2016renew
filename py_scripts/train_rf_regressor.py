import os
import sys
import shutil
import re
import fnmatch
import pandas as pd
import numpy as np
from datetime import datetime

import randomforest as forest

def main(params):

    # Read params and make variables from text
    inputs = forest.read_params(params)
    for i in inputs:
        exec ("{0} = str({1})").format(i, inputs[i])

    # Check that variables were specified in params
    try:
        str_check = sample_txt, target_col, var_txt, out_dir
    except NameError as e:
        print ''
        missing_var = str(e).split("'")[1]
        msg = "Variable '%s' not specified in param file:\n%s" % (missing_var, params)
        raise NameError(msg)

    # Make optional numeric arguments numeric
    if 'n_trees' in locals():
        n_trees = int(n_trees)
    else:
        n_trees = 50
    if 'n_jobs' in locals():
        n_jobs = int(n_jobs)
    else:
        n_jobs = 12
    if 'max_depth' in locals():
        max_depth = int(max_depth)
    else:
        max_depth=None

    # Raise an error if var_txt doesn't exist. Otherwise, just read it in
    if not os.path.exists(var_txt):
        print ''
        msg = 'var_text path specified does not exist:\n%s\n\n' % var_txt
        raise IOError(msg)
    df_var = pd.read_csv(var_txt, sep='\t', index_col='var_name')

    # Make the output directory
    now = datetime.now()
    date_str = str(now.date()).replace('-','')
    time_str = str(now.time()).replace(':','')[:4]
    stamp = '{0}_{1}_{2}'.format('susceptibility', date_str, time_str)
    out_dir = os.path.join(out_dir, stamp)
    os.makedirs(out_dir) # With a timestamp in dir, no need to check if it already exists
    shutil.copy2(params, out_dir) #Copy the params so the parameters used are saved
    #shutil.copy2(var_txt, out_dir)

    # Read in training samples
    df_train = pd.read_csv(sample_txt, sep='\t', index_col='obs_id')

    # Check that df_train has exactly the same columns as variables specified in df_vars
    train_columns = df_train.columns.tolist()
    unmatched_vars = [v for v in df_var.index if v not in train_columns]
    if len(unmatched_vars) != 0:
        unmatched_str = '\n'.join(unmatched_vars)
        msg = 'Columns not in sample_txt but specified in params:\n' + unmatched_str
        raise NameError(msg)

    # Sort the predictors in alphabetical order so that train columns can be in the same order as the predict array when
    #   predicting later on
    predict_cols = sorted(np.unique([c for c in df_train.columns for v in df_var.index if v in c]))
    df_var = df_var.sort_index()

    x_train = df_train.reindex(columns=predict_cols)
    y_train = df_train[target_col]
    rf_model = forest.train_rf_regressor(x_train, y_train,
                                         ntrees=n_trees,
                                         njobs=n_jobs,
                                         max_depth=max_depth)

    df_var['importance'] = rf_model.feature_importances_
    rf_path = os.path.join(out_dir, 'regressor_model_%s' % stamp)
    forest.save_rfmodel(rf_model, rf_path)
    oob_score = round(rf_model.oob_score_, 3)
    out_var_txt = os.path.join(out_dir, os.path.basename(var_txt))
    df_var.to_csv(out_var_txt, sep='\t')

    # Record params in inventory text file
    df_inv = pd.read_csv(inventory_txt, sep='\t')
    col_str = re.sub('[\]\[\'\"]', '', str(predict_cols))
    raster_res = sample_txt.split('_')[-2].replace('m','')
    df_inv = df_inv.append(pd.DataFrame([[stamp, oob_score, '', '', '', '', len(df_train), raster_res, col_str]],
                                        columns=df_inv.columns),
                           ignore_index=True)
    existing_models = fnmatch.filter(os.listdir(os.path.dirname(out_dir)), 'susc*')
    df_inv = df_inv[df_inv.stamp.isin(existing_models)]
    df_inv.to_csv(inventory_txt, sep='\t', index=False)


    print 'Random Forest Regressor model written to:\n', rf_path
    print '\nOOB score: ', oob_score
    print 'Relative importance:'
    print df_var.importance


if __name__ == '__main__':
    params = sys.argv[1]
    sys.exit(main(params))



