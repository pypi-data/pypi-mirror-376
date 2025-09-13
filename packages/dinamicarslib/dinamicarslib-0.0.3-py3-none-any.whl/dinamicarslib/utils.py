import pandas as pd
import geopandas as gpd
import pyarrow
from pathlib import Path
from datetime import datetime


def check_extension(path):
    extension = path.suffix
      
    if extension == '.parquet':
        io_function = 'parquet'
        return io_function
    elif extension == '.feather':
        io_function = 'feather'
        return io_function
    else:
        io_function = 'file'
        return io_function



def parse_date(datetime_str:str):
    """Parse da datetime string in the ISO8601 format. 

    Args:
        datetime_str (str): ISO8601 datetime format

    Returns:
       str: datetime in the YYYY-MM-DD-HH-mm-ss format
    """
    if datetime_str:
        return datetime.fromisoformat(datetime_str.replace("Z", "+00:00")).date()
    