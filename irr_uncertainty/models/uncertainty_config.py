"""This script includes station configuration for modelling uncertainties"""
# Created by A. MATHIEU at 14/02/2024
import pandas as pd

from irr_uncertainty.config import DATA_PATH
from irr_uncertainty.data.solar_data import stations_bsrn, bsrn_lat_long_alt

UNCERT_PATH = DATA_PATH / "uncertainty"

START_BSRN = pd.to_datetime("20050101").tz_localize("CET")
END_BSRN = pd.to_datetime("20230101").tz_localize("CET")

meta_stations = stations_bsrn()

euro_stations = []
for station in meta_stations.loc[
    meta_stations["Network"].fillna("").str.contains("BSRN"), "Abbreviation"].dropna().str.lower():
    lat, lon, alt = bsrn_lat_long_alt(station)
    if (lat > 35) & (lat < 60) & (lon > -20) & (lon < 40):
        euro_stations += [station]

euro_stations = sorted(euro_stations)
#### Remove some stations
# son: peculiar local conditions (snowy-4000m location)
# MRS: no BHI
# LMP: not enough data
euro_stations = [st for st in euro_stations if (st != "son") & (st != "mrs") & (st != "lmp")]
