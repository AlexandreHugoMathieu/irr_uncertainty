"""Module to get solar position and in-situ weather station metadata"""
# Created by A. MATHIEU at 25/10/2025
import os
import pandas as pd
import numpy as np

from typing import Union
from pathlib import Path
from pvlib.location import Location
from pvlib.irradiance import get_extra_radiation
from pvlib.tools import cosd

from irradiance_uncertainty.config import DATA_PATH


def get_solar_position_1m(index: pd.Index,
                          lat: Union[int, float],
                          long: Union[int, float],
                          alt: Union[int, float],
                          ta: Union[pd.Series, float] = None,
                          p: Union[pd.Series, float] = None,
                          pkl: bool = False,
                          folder: Union[Path, str] = DATA_PATH / "solar_pos",
                          overwrite: bool = False) -> pd.DataFrame:
    """
    Facitator-function to compute and locally store the sun position DataFrame (function from pvlib) at the 1 minute granularity.
    pvlib function: https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.solarposition.get_solarposition.html

    The pressure and temperature inputs enable to more precisely calculate the "apparent" zenith.
    Otherwise, the pressure is inferred from the altitude and the temperature is equal to 12 by default.

    :param index: hourly "index" datetimes (list of datetimes) for which to get the minute-granularity
    :param lat: Installation latitude [°]
    :param long: Installation longitude [°]
    :param alt: Altitude [°]
    :param ta: Temperature [°C] (timeserie or constant)
    :param p: Pressure [Pa] (timeserie or constant)
    :param pkl: (boolean), if True, stored locally, to make it faster for the next executions
    :param folder: Folder in which to store the pkl files

    :return: pd.DataFrame with 6 columns
        ['apparent_zenith', 'zenith', 'apparent_elevation', 'elevation', 'azimuth', 'equation_of_time']
    """

    # Build the pkl file name string
    start_str = index.min().strftime('%Y%m%d')
    end_str = index.max().strftime('%Y%m%d')
    lat_str = str(round(lat, 2))
    long_str = str(round(long, 2))
    pkl_file = folder / f"solar_position_1m_{lat_str}_{long_str}_{start_str}_{end_str}.pkl"

    if pkl and pkl_file.exists() and not overwrite:
        solar_position_1m = pd.read_pickle(pkl_file)
    else:
        # Build the 1-min index
        start_m = index.min()
        end_m = index.ceil("D").max() + pd.DateOffset(hours=1)
        index_m = pd.date_range(start_m, end_m, freq="min", inclusive="left")

        # Prepare pressure and temperature variables to inject into the pvlib function
        p_m = None
        if not (p is None):
            p_m = p.reindex(index_m).interpolate().ffill() if type(p) == pd.Series else pd.Series(p, index=index_m)

        ta_m = 12
        if not (ta is None):
            ta_m = ta.reindex(index_m).interpolate().ffill() if type(ta) == pd.Series else pd.Series(ta, index=index_m)

        # Generate the 1 minute solar position dataframe
        site = Location(latitude=lat, longitude=long, tz="UTC", altitude=alt)
        solar_position_1m = site.get_solarposition(times=index_m, pressure=p_m, temperature=ta_m)

        # Store locally into pickle file
        if pkl:
            solar_position_1m.to_pickle(pkl_file)

    return solar_position_1m


def solarpos(index: pd.Index,
             lat: Union[int, float],
             long: Union[int, float],
             alt: Union[int, float],
             ta: Union[pd.Series, float] = None,
             p: Union[pd.Series, float] = None,
             interpolate: bool = True,
             overwrite: bool = False,
             freq: str = "H") -> pd.DataFrame:
    """
    Facitator-function to compute and locally store the sun position DataFrame (function from pvlib) .
    pvlib function: https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.solarposition.get_solarposition.html

    The pressure and temperature inputs enable to more precisely calculate the "apparent" zenith.
    Otherwise, the pressure is inferred from the altitude and the temperature is equal to 12 by default.

    :param index: hourly "index" datetimes (list of datetimes) for which to get the minute-granularity
    :param lat: Installation latitude [°]
    :param long: Installation longitude [°]
    :param alt: Altitude [°]
    :param ta: Temperature [°C] (timeserie or constant)
    :param p: Pressure [Pa] (timeserie or constant)
    :param pkl: (boolean), if True, stored locally, to make it faster for the next executions
    :param folder: Folder in which to store the pkl files

    :return: pd.DataFrame with 6 columns
    ['apparent_zenith', 'zenith', 'apparent_elevation', 'elevation', 'azimuth', 'equation_of_time']
    """

    # Build the pkl file name string
    start_str = index.min().strftime('%Y%m%d')
    end_str = index.max().strftime('%Y%m%d')
    lat_str = str(round(lat, 2))
    long_str = str(round(long, 2))
    solar_pos_pkl = DATA_PATH / "solar_pos" / f"solar_position_{freq}_{lat_str}_{long_str}_{start_str}_{end_str}.pkl"

    if os.path.exists(solar_pos_pkl) and not overwrite:
        solar_position_freq = pd.read_pickle(solar_pos_pkl)
    else:
        # Fetch the 1-min solar position and average it over the provided frequency
        solar_position = get_solar_position_1m(index, lat, long, alt, ta=ta, p=p, overwrite=overwrite)

        # End of time integration (end-of-time convention)
        solar_position_freq = solar_position.resample(freq, label="right").mean()

        # Save it for next time
        solar_position_freq.to_pickle(solar_pos_pkl)

    if interpolate:
        solar_position_freq = solar_position_freq.reindex(index).interpolate().bfill(limit=1)

    return solar_position_freq


def stations_bsrn():
    """
    Get irradiance weather in-situ station meta data

    The CSV file is imported from https://github.com/AssessingSolar/solarstations/blob/main/solarstations.csv and stored locally
    """

    path = DATA_PATH / "bsrn_data" / "solarstations_v2.csv"
    if os.path.exists(path):
        data = pd.read_csv(path)
    else:
        data = pd.read_csv(
            "https://raw.githubusercontent.com/AssessingSolar/solarstations/refs/heads/main/solarstations.csv")
        data.to_csv(path)
    return data


def bsrn_lat_long_alt(station):
    """Get Latitude, Longitude and Altitude of BSRN station from its 3-letter abbreviation"""
    meta_data = stations_bsrn()
    meta_station = meta_data.loc[meta_data["Abbreviation"].str.lower() == station].copy().astype("str").iloc[0]
    lat, lon, alt = float(meta_station.loc["Latitude"]), float(meta_station.loc["Longitude"]), float(
        meta_station.loc["Elevation"])
    return lat, lon, alt


def bsrn_name(station):
    """Get BSRN station name from its 3-letter abbreviation"""
    meta_data = stations_bsrn()
    meta_station = meta_data.loc[meta_data["Abbreviation"].str.lower() == station].copy().astype("str").iloc[0]
    name = str(meta_station.loc["Station name"])
    return name


def get_filter_v2(data_h, solar_position):
    """
    Apply the three components consistency tests of Ineichen's study (section 4.3) [1] which notably includes
    the global comparison test from Long and Shi [2]

    :param data_h: pd.DataFrame containing hourly solar irradiance data.
        Required columns: ['ghi', 'dhi', 'dni', 'bhi']
    :param solar_position: pd.DataFrame containing solar position data.
        Required columns: ['apparent_elevation', 'elevation', 'apparent_zenith', 'zenith']

    :return: pd.Series (bool), where True indicates that the row passed all quality filters.

    References
    ----------
    .. [1] Ineichen Pierre, Long term HelioClim-3 global, beam and diffuse irradiance validation, 2016.
    .. [2] C. Long, Y. Shi, The Open Atmospheric Science Journal 2008, 2, 23–37
    """

    elevation = solar_position["apparent_elevation"].fillna(solar_position["elevation"]).replace(0, np.nan)
    zenith = solar_position["apparent_zenith"].fillna(solar_position["zenith"]).replace(0, np.nan)
    sin_h = np.sin(elevation * np.pi / 180)
    bni = data_h["dni"] * sin_h
    sum_direct_diffuse = (data_h["dhi"] + bni).replace(0, np.nan)

    filter_50 = (sum_direct_diffuse > 50)  # W/m2
    h_15 = (elevation >= 15) & filter_50
    h_0 = (elevation < 15) & (elevation >= -3) & filter_50

    # Sum direct and diffuse: consistent with global irradiance (BSRN quality control)
    consistency = pd.Series(False, index=data_h.index)
    consistency.loc[h_0] = (data_h.loc[h_0, "ghi"] / sum_direct_diffuse.loc[h_0]).abs().between(0.85, 1.15)
    consistency.loc[h_15] = (data_h.loc[h_15, "ghi"] / sum_direct_diffuse.loc[h_15]).abs().between(0.92, 1.08)

    dni_extra = get_extra_radiation(data_h.index)
    ghi_extra = cosd(zenith) * dni_extra

    # Direct/Diffuse/Global index consistency test (SERI quality control)
    kd = data_h["dhi"] / ghi_extra.replace(0, np.nan)
    kb = data_h["bhi"] / ghi_extra.replace(0, np.nan)
    k = data_h["ghi"] / ghi_extra.replace(0, np.nan)
    k_filter = (k - kd - kb).between(-0.03, 0.03) & filter_50

    # Direct beam limit test (closure equation)
    blimit = 1.1 * data_h["dni"] + 50
    bn_calc = (data_h["ghi"] - data_h["dhi"]) / sin_h  # dni * sin(h) = ghi - dhi
    bcalc_filter = ((data_h["dni"] + abs(data_h["dni"] - bn_calc)) < blimit) & filter_50

    # All filters are combined
    filter = k_filter & consistency & bcalc_filter

    return filter


def stations_pv_live():
    """
    PV-live station metadata

    Manually written from https://zenodo.org/records/7311989 (metadatafile)
    """
    stations = pd.DataFrame(
        columns=['ID', 'Station name', 'Latitude', 'Longitude', 'Altitude'],
        data=[
            [1, 'Wendlingen', 48.667, 9.399, 276],
            [2, 'Stuttgart', 48.83, 9.196, 294],
            [3, 'St. Leon-Rot', 49.245, 8.641, 108],
            [4, 'Ketsch', 49.356, 8.532, 102],
            [5, 'Freiburg', 48.009, 7.835, 256],
            [6, 'Mahlberg', 48.28, 7.787, 170],
            [7, 'Murr', 48.968, 9.263, 212],
            [8, 'Fünfstetten', 48.837, 10.773, 504],
            [9, 'Freudenstadt', 48.459, 8.425, 669],
            [10, 'Karlsruhe', 49.008, 8.344, 115],
            [11, 'Oberndorf', 48.298, 8.552, 667],
            [12, 'Ulm', 48.422, 10.006, 552],
            [13, 'Bad Rappenau', 49.268, 9.059, 288],
            [14, 'Offenburg', 48.473, 7.939, 151],
            [15, 'Grünstadt', 49.562, 8.188, 157],
            [16, 'Löffingen', 47.885, 8.4, 745],
            [17, 'Aitrach', 47.927, 10.09, 601],
            [18, 'Neusass', 49.612, 9.35, 441],
            [19, 'Tuttlingen', 47.957, 8.78, 649],
            [20, 'Hechingen', 48.36, 8.966, 490],
            [21, 'Leutkirch', 47.836, 9.988, 648],
            [22, 'Königsbronn', 48.751, 10.169, 637],
            [23, 'Lörrach', 47.613, 7.655, 284],
            [24, 'Ingoldingen', 47.996, 9.699, 573],
            [25, 'Eberbach', 49.465, 8.987, 137],
            [26, 'Zwiefaltendorf', 48.207, 9.513, 523],
            [27, 'Krautheim', 49.396, 9.605, 382],
            [28, 'Pforzheim', 48.899, 8.746, 312],
            [29, 'Weikersheim', 49.457, 9.889, 370],
            [30, 'Konstanz', 47.674, 9.163, 402],
            [31, 'Leibertingen', 48.064, 9.068, 763],
            [32, 'Crailsheim', 49.132, 10.054, 416],
            [33, 'Ravensburg', 47.786, 9.608, 432],
            [34, 'Herdwangen-Schönach', 47.854, 9.137, 660],
            [35, 'Schwäbisch Hall', 49.117, 9.774, 399],
            [36, 'Baden-Baden', 48.787, 8.189, 127],
            [37, 'Neubulach', 48.649, 8.654, 621],
            [38, 'Waldshut-Tiengen', 47.624, 8.255, 345],
            [39, 'Schwäbisch Gmünd', 48.803, 9.8, 326],
            [40, 'Berghülen', 48.455, 9.778, 667]
        ])
    stations = stations.set_index("ID")
    return stations


def pvlive_lat_long_alt(station):
    """Get Latitude, Longitude and Altitude of a PV station from its ID-number"""
    stations = stations_pv_live()
    lat, long, alt = stations.loc[station, "Latitude"], stations.loc[station, "Longitude"], \
                     stations.loc[station, "Altitude"]
    return lat, long, alt
