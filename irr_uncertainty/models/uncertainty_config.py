"""This script includes station configuration for modelling uncertainties"""
# Created by A. MATHIEU at 14/02/2024
import pandas as pd

from irr_uncertainty.config import DATA_PATH
from irr_uncertainty.data.station_metadata import stations_bsrn, bsrn_lat_long_alt

UNCERT_PATH = DATA_PATH / "uncertainty"

START_BSRN = pd.to_datetime("20050101").tz_localize("CET")
END_BSRN = pd.to_datetime("20260101").tz_localize("CET")
END_BSRN = pd.to_datetime("20230101").tz_localize("CET")

#TODO: extend to 2026 and add lmp

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

# Arbitrary selected based on missing data
YEARS = {"bud": [2020, 2021, 2022],
         "cab": list(range(2005, 2023)),
         "cam": [2005, 2007, 2009, 2013, 2014],
         "car": list(range(2005, 2011)) + (list(range(2012, 2019))),
         "cnr": list(range(2011, 2015)) + (list(range(2016, 2023))),
         "lin": list(range(2006, 2023)),
         # "lmp": list(range(2021, 2026)),
         "pal": list(range(2008, 2012)) + (list(range(2013, 2023))),
         "pay": [2009] + (list(range(2013, 2023))),
         "tor": list(range(2006, 2022)),
         }

# Arbitrary selected based on missing data
YEARS_5y = {"bud": [2020, 2021, 2022],
            "cab": list(range(2018, 2023)),
            "cam": [2005, 2007, 2009, 2013, 2014],
            "car": (list(range(2014, 2019))),
            "cnr": (list(range(2018, 2023))),
            "lin": list(range(2018, 2023)),
            "pal": list(range(2008, 2012)) + (list(range(2013, 2023))),
            "pay": [2009] + (list(range(2013, 2023))),
            "tor": list(range(2006, 2022)),
            }

### Start to check all station data
# from irr_uncertainty.config import Config
# stations = "bud"
# user, password = Config().bsrn()
# sat_data, insitu_data, solar_position = load_bsrn_data(START_BSRN, END_BSRN, station, user, password)
#
# var = "ghi"
# sat_data[var].plot()
# insitu_data[var].plot()