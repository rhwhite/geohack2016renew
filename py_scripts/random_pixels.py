import sys
import os
import time
import pandas as pd
from datetime import datetime

import randomforest as forest
import test_n_trees as test


def read_params(txt):
    ''' Return a dictionary from parsed parameters in txt '''
    d = {}

    # Read in the text file
    try:
        with open(txt) as f:
            input_vars = [line.split(";") for line in f]
    except:
        print 'Problem reading parameter file: ', txt
        return None

    # Set the dictionary key to whatever is left of the ";" and the val
    #   to whatever is to the right. Strip whitespace too.
    for var in input_vars:
        if len(var) == 2:
            d[var[0].replace(" ", "")] = \
                '"{0}"'.format(var[1].strip(" ").replace("\n", ""))

    print 'Parameters read from:\n', txt, '\n'
    return d


def main(params):

    t0 = time.time()
    inputs = read_params(params)
    for var in inputs:
        exec ("{0} = str({1})").format(var, inputs[var])

    out_dir = os.path.dirname(out_txt)
    if not os.path.exists(out_dir):
        print 'WARNING: output directory does not exist. Creating new directory:\n', out_dir
        os.makedirs(out_dir)

    # Make optional numeric arguments numeric
    if 'data_band' in locals():
        data_band = int(data_band)
    else:
        data_band = 1
    '''if 'nodata' in locals():
        nodata = int(nodata)
    else:
        nodata = None'''
    if 'pct_train' in locals():
        pct_train = float(pct_train)
    else:
        pct_train = None

    # Check that all required params were specified
    try:
        bin_list = [b.split(':') for b in bins.split(',')]
        bins = [(int(mn), int(mx)) for mn, mx in bin_list]
        n_samples = int(n_samples)
        nodata = int(nodata)
        str_check = raster_path, col_name, out_txt
    except NameError as e:
        missing_var = str(e).split("'")[1]
        msg = "Variable '%s' not specified in param file:\n%s" % (missing_var, params)
        raise NameError(msg)

    # Get training and testing samples
    df_train, df_test, raster_res = forest.get_stratified_sample(raster_path, col_name, data_band, n_samples, bins, pct_train, nodata)
    df_train['obs_id'] = df_train.index

    # Write samples to text file
    now = datetime.now()
    date_str = str(now.date()).replace('-', '')
    time_str = str(now.time()).replace(':', '')[:4]
    stamp = '{0}_{1}_{2}_{3}m'.format(len(df_train), date_str, time_str, int(raster_res))
    out_txt = out_txt.replace('.txt', stamp + '.txt')
    bn = os.path.basename(out_txt)
    out_dir = os.path.join(os.path.dirname(out_txt), bn[:-4])
    out_txt = os.path.join(out_dir, bn)
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    df_train.to_csv(out_txt, sep='\t', index=False)
    print 'Samples written to:\n', out_txt, '\n'

    if 'var_txt' in locals():
        df_var = pd.read_csv(var_txt, sep='\t', index_col='var_name')
        df_predictors = df_train.copy()
        df_predictors = forest.sample_predictors(df_predictors,
                                                 df_var, nodata)
        df_predictors.to_csv(out_txt.replace('.txt', '_predictors.txt'), sep='\t', index=False)

    # If pct train was specified, then there should be some testing samples so write them to disk
    if pct_train:
        df_test['obs_id'] = df_test.index
        test_txt = out_txt.replace('%s.txt' % stamp, '_test_%s.txt' % stamp)
        df_test.to_csv(test_txt, sep='\t', index=False)
        print 'Test samples written to:\n', test_txt, '\n'

    if 'test_n_trees_params' in locals():
        if not 'var_txt' in locals():
            print 'Cannot test number of trees because no predictors were sampled. Try specifying a var_txt path.'
        x_train = df_predictors[df_var.index]
        y_train = df_predictors[col_name]
        test_params = forest.read_params(test_n_trees_params)
        max_trees = int(test_params['max_trees'].replace('"',''))
        step = int(test_params['step'].replace('"',''))
        test.test(out_dir, x_train, y_train, max_trees, step)

    print 'Total time for sampling predictors: %.1f seconds' % (time.time() - t0)

if __name__ == '__main__':
    params = sys.argv[1]
    sys.exit(main(params))
