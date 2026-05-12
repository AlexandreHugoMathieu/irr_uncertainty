"""Module to get solar position and in-situ weather station metadata"""
# Created by A. MATHIEU at 25/10/2025
import os
import pandas as pd
import numpy as np

from typing import Union
from pathlib import Path
from pvlib.location import Location
from pvlib.irradiance import get_extra_radiation, get_total_irradiance, aoi_projection, aoi
from pvlib.tools import cosd

from irr_uncertainty.config import DATA_PATH


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
        solar_position_1m = get_solar_position_1m(index, lat, long, alt, ta=ta, p=p, overwrite=overwrite)

        # End of time integration (start-of-time convention)
        solar_position_freq = solar_position_1m.resample(freq).mean()

        # Save it for next time
        solar_position_freq.to_pickle(solar_pos_pkl)

    if interpolate:
        solar_position_freq = solar_position_freq.reindex(index).interpolate().bfill(limit=1)

    return solar_position_freq


def get_poaextra(index: pd.Index,
           lat: Union[int, float],
           long: Union[int, float],
           alt: Union[int, float] = None,
           tilt: Union[int, float] = 25,
           surface_azimuth: Union[int, float] = 180,
           solar_position_1m: pd.DataFrame = None,
           dni_extra_1m: pd.Series = None,
           ta: Union[pd.Series, float] = None,
           p: Union[pd.Series, float] = None,
           overwrite: bool = False,
           freq: str = "H") -> pd.DataFrame:
    # Build the pkl file name string
    start_str = index.min().strftime('%Y%m%d')
    end_str = index.max().strftime('%Y%m%d')
    lat_str = str(round(lat, 2))
    long_str = str(round(long, 2))
    tilt_str = str(round(tilt, 2))
    surface_azimuth_str = str(round(surface_azimuth, 2))
    aoi_pos_pkl = DATA_PATH / "aoi" / f"aoi_{freq}_{lat_str}_{long_str}_{tilt_str}_{surface_azimuth_str}_{start_str}_{end_str}.pkl"
    solar_pos_pkl = DATA_PATH / "poaextra" / f"poaextra_{freq}_{lat_str}_{long_str}_{tilt_str}_{surface_azimuth_str}_{start_str}_{end_str}.pkl"

    # Compute AOI angle
    if os.path.exists(aoi_pos_pkl) and not overwrite:
        aoi_angle = pd.read_pickle(aoi_pos_pkl)

    else:
        if solar_position_1m is None:
            # Fetch the 1-min solar position and average it over the provided frequency
            solar_position_1m = get_solar_position_1m(index, lat, long, alt, ta=ta, p=p, overwrite=overwrite)
        zenith_1m = solar_position_1m["apparent_zenith"].fillna(solar_position_1m["zenith"])

        if dni_extra_1m is None:
            dni_extra_1m = get_extra_radiation(solar_position_1m.index)
        aoi_angle = aoi(tilt, surface_azimuth, zenith_1m, solar_position_1m["azimuth"])

    # Check if poa_extra is not already computed
    if os.path.exists(solar_pos_pkl) and not overwrite:
        poa_extra = pd.read_pickle(solar_pos_pkl)

    else:
        poa_extra_1m = dni_extra_1m * np.maximum(cosd(aoi_angle), 0.065)
        # location = Location(lat, long, altitude=alt)
        # clearsky = location.get_clearsky(solar_position_1m.index)
        # poa_cs_1m = get_total_irradiance(
        #     surface_tilt=tilt,
        #     surface_azimuth=surface_azimuth,
        #     solar_zenith=zenith_1m,
        #     solar_azimuth=solar_position_1m["azimuth"],
        #     dni=clearsky['dni'],
        #     ghi=clearsky['ghi'],
        #     dhi=clearsky['dhi'],
        #     dni_extra=dni_extra_1m,
        #     model="haydavies"
        # )

        # Start-of-time integration
        # poa_cs = poa_cs_1m.resample(freq).mean().reindex(index)
        # poa_cs.to_pickle(solar_pos_pkl)
        poa_extra = poa_extra_1m.resample(freq).mean().reindex(index)
        poa_extra.to_pickle(solar_pos_pkl)

    return poa_extra, aoi_angle


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
    dni_extra = get_extra_radiation(data_h.index)
    ghi_extra = cosd(zenith) * dni_extra

    sin_h = np.sin(elevation * np.pi / 180)
    bni = data_h["dni"] * sin_h
    sum_direct_diffuse = (data_h["dhi"] + bni).replace(0, np.nan)

    # Basic filter to dissociate elevation with a minimum irradiance level
    filter_50 = (sum_direct_diffuse > 50)  # W/m2
    h_15 = (elevation >= 15) & filter_50
    h_0 = (elevation < 15) & (elevation >= -3) & filter_50

    # Sum direct and diffuse: consistent with global irradiance (BSRN quality control)
    consistency = pd.Series(False, index=data_h.index)
    consistency.loc[h_0] = (data_h.loc[h_0, "ghi"] / sum_direct_diffuse.loc[h_0]).abs().between(0.85, 1.15)
    consistency.loc[h_15] = (data_h.loc[h_15, "ghi"] / sum_direct_diffuse.loc[h_15]).abs().between(0.92, 1.08)

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


