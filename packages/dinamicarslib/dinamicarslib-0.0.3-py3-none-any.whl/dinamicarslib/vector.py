import pandas as pd
import geopandas as gpd
from utils import *

class GeoSpatialTable(gpd.GeoDataFrame):
    def __init__(headers, data, keyColumns):
        pass

    def prepareTable(self, keyColumns):
        pass


def open_vector_file(file):
    """open a vector file as a geopandas.geoDataframe

    Args:
        file (string): filepath of the vector table

    Returns:
        GeoDataframe: geodataframe
    """
    filepath = Path(file)
    
    io_func = check_extension(path=filepath)

    if io_func == 'file':
        gdf = gpd.read_file(filepath)
        return gdf
    elif io_func == 'parquet':
        gdf = gpd.read_parquet(filepath)
        return gdf
    elif io_func == 'feather':
        gdf = gpd.read_feather(filepath)
        return gdf

def save_vector_file(gdf, file):
    """Save a GeoDataframe as in a file

    Args:
        gdf (_type_): GeoDataFrame object
        file (_type_): destinarion filepath

    Returns:
        None: None
    """
    filepath = Path(file)
    
    io_func = check_extension(path=filepath)

    if io_func == 'file':
        gdf = gdf.to_file(filepath)
        return None
    elif io_func == 'parquet':
        gdf = gdf.to_parquet(filepath)
        return None
    elif io_func == 'feather':
        gdf = gdf.to_feather(filepath)
        return None

def get_atributte_by_location(input_filepath, reference_filepath, how, predicate, cols_to_get):
    
    """Add one or more attibutes columns of refence vector file in the input file using a spatial predicate

    Args:
        input_filepath (_type_): filepath of the input vector file
        reference_filepath (_type_): filepath of the refence vector file
        how (_type_): _description_
        predicate (_type_): spatial predicate
        cols_to_get (_type_): list of columns to get from the refecente vector table

    Returns:
        _type_: _description_
    """

    gdf_left = open_vector_file(input_filepath)
    gdf_right = open_vector_file(reference_filepath)
    
    
    cols_to_get.append(gdf_right.geometry.name)

    gdf_right = gdf_right.loc[:, cols_to_get]
    gdf_join = gdf_left.sjoin(gdf_right,how=how,predicate=predicate)
    gdf_join.drop(columns='index_right')

    return gdf_join


def query_table_by_atributte(dataset_fp, col_name, col_value, query=None):
    dataset = open_vector_file(dataset_fp)

    if query:
        if len(query) > 0:
            query_table=  dataset.query(query)
            return query_table

    query_table = dataset.loc[dataset[col_name]==col_value]

    return query_table

def union_vector_tables(files_table, id_column='id', keep_index=False):
    gdf_list = []
    for file in files_table[1:]:
        gdf = open_vector_file(file[1])
        gdf_list.append(gdf)

    gdf_concat = pd.concat(gdf_list, ignore_index=True)
    gdf_concat[id_column] = gdf_concat.index + 1
    
    return gdf_concat


def create_sample_points(vector_filepath , num_samples):
    """Create random points withim the features of a geospatial table.

    Args:
        vector_filepath (string): filepath of the vector table to create the random points
        num_samples (int): number of points per feature to create

    Returns:
       geodataframe: a geospatial table with geometry column of points type. It has a "polygon_id" columns with the index of the respective polygon of the original table.
    """
    gdf = open_vector_file(vector_filepath)
    samples_per_poly = num_samples
    points = gpd.GeoDataFrame(geometry=gdf.sample_points(size=samples_per_poly, rgn=64))
    points = points.explode(ignore_index=False, index_parts=False)
    points = points.reset_index().rename(columns={'index':'polygon_id'})
    points = points.reset_index().rename(columns={'index':'id'})
    points['id'] += 1
    points_gdf = points.merge(gdf.drop(columns='geometry'), how='left', right_index=True, left_on='polygon_id')
    return points_gdf