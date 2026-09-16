"""This module analyze CAMS error on PV-live stations"""
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd

from global_land_mask import globe
from geopandas import GeoDataFrame
from shapely import Polygon
from shapely.geometry import Point
from tqdm import tqdm

from irr_uncertainty.config import DATA_PATH, Config
from irr_uncertainty.data.station_metadata import stations_pv_live, bsrn_lat_long_alt, bsrn_name, stations_bsrn
from irr_uncertainty.data.irr_data import ghi_dhi_bhi_pvgis_2015, load_bsrn_data
from irr_uncertainty.models.uncertainty_config import euro_stations, YEARS, START_BSRN, END_BSRN
from irr_uncertainty.utils import  plot_kt_kt,  calculate_kt_kpis