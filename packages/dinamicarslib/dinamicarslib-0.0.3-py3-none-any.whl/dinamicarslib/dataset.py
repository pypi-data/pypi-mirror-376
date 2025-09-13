try:
    dinamica.inputs
except:
    from dinamicaClass import dinamicaClass
    dinamica = dinamicaClass({})

import geopandas as gpd
import pandas as pd
import numpy as np
import xarray as xr
from dinamicarslib.vector import *
from sklearn.model_selection import train_test_split





def create_dataset(points_fp, variables_fp):
    """Create a trainning dataset of a Machine Learning model, the dataset consist of a table with one column for each variable with it's variable value.

    Args:
        points_fp (string): filepath of the input vector file to use as samples
        variables_fp (_type_): _description_

    Returns:
        _type_: _description_
    """

    samples_points = open_vector_file(points_fp)
    iterable = samples_points.get_coordinates()
    x_points = xr.DataArray(iterable.x, dims=('points',))
    y_points = xr.DataArray(iterable.y, dims=('points',))
    for var in variables_fp[1:]:
        print(var)
        band_name = var[0]
        ds = rioxarray.open_rasterio(var[1], masked=True, chuncks='auto').assign_coords(band_name=band_name)
        values = ds.sel(x=x_points, y=y_points, method="nearest")
        samples_points.loc[:, band_name] = values.compute().values[0]

    return samples_points




def create_samples_filename(base_folder, suffix, file_extension='.parquet', make_child_dirs=True):

    all_samples_dir = base_folder.joinpath('samples')
    test_samples_dir = base_folder.joinpath('test')
    train_samples_dir = base_folder.joinpath('train')
    
    if make_child_dirs:
        #All samples
        os.makedirs(all_samples_dir, exist_ok=True)
        #Test set
        os.makedirs(test_samples_dir, exist_ok=True)
        #Train samples
        os.makedirs(train_samples_dir, exist_ok=True)

    #Create file names
    all_samples = all_samples_dir.joinpath(suffix).with_suffix(file_extension)
    test_samples = test_samples_dir.joinpath(suffix).with_suffix(file_extension)
    train_samples = train_samples_dir.joinpath(suffix).with_suffix(file_extension)
    
    return all_samples, train_samples, test_samples

def split_dataset(dataset_fp, class_column, out_base_folder, suffix=None, test_size=0.3, random_state=0, stratify=False, grouped=False, group_cols=None):

    dataset = open_vector_file(dataset_fp)

    if grouped:
        if  isinstance(group_cols, list):
            unique_polygons = list(dataset.groupby(group_cols).groups.keys())
            samples_train, samples_test = train_test_split(unique_polygons, test_size=test_size ,random_state=0) #split train and test

            train_points = dataset.loc[dataset[group_cols].apply(tuple,axis=1).isin(samples_train)]
            test_points = dataset.loc[dataset[group_cols].apply(tuple,axis=1).isin(samples_test)]
        else:
            unique_polygons = dataset.loc[:,group_cols].unique()
            samples_train, samples_test = train_test_split(unique_polygons, test_size=test_size ,random_state=0) #split train and test

            train_points = dataset.loc[dataset[group_cols].isin(samples_train)]
            test_points = dataset.loc[dataset[group_cols].isin(samples_test)]
    else:
        unique_polygons = dataset.index
        samples_train, samples_test = train_test_split(unique_polygons, test_size=test_size ,random_state=0) #split train and test

        train_points = dataset.loc[dataset[group_cols].isin(samples_train)]
        test_points = dataset.loc[dataset[group_cols].isin(samples_test)]





    train_fp, test_fp = create_samples_filename(out_base_folder)
    


    train_points.to_parquet(train_fp)
    test_points.to_parquet(test_fp)

    
    
if __name__ == "__main__":
    points_fp = dinamica.inputs['s1']
    variables = dinamica.inputs['t1']

    dataset = create_dataset(points_fp, variables)
    out_filepath = dinamica.inputs['s2']
    dataset.to_parquet(out_filepath)

    print(dataset.head())
    print(dataset.info())