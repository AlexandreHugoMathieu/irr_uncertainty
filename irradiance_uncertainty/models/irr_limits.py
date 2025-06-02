"""This script includes the functions to calculate the irradiance physical limits"""
# Created by A. MATHIEU at 12/02/2025
import numpy as np
import pandas as pd

from typing import Union
from pathlib import Path
from pvlib.irradiance import aoi, get_extra_radiation, get_total_irradiance

from irradiance_uncertainty.config import DATA_PATH
from irradiance_uncertainty.data.solar_data import get_solar_position_1m


def get_irr_limits(index_H: pd.DatetimeIndex,
                   lat: Union[int, float],
                   lon: Union[int, float],
                   alt: Union[int, float],
                   ta: Union[pd.Series, float, int] = 12,
                   p: Union[pd.Series, float, int] = None,
                   pkl: bool = True,
                   folder: Union[Path, str] = DATA_PATH / "irr_limits",
                   overwrite: bool = False,
                   resample_freq: str = "H"):
    """
    Computes and optionally saves irradiance limits (GHI, DHI, BHI) for a given location and time period from Long et Shi.[1]

    This function estimates the upper and lower limits of global horizontal irradiance (GHI),
    diffuse horizontal irradiance (DHI), and beam horizontal irradiance (BHI) based on solar position
    and atmospheric conditions. If precomputed values exist, they are loaded from pickle files unless `overwrite=True`.

    :param index_H: Datetime index for the time period of interest. (hourly)
    :param lat: Latitude of the location.
    :param lon: Longitude of the location.
    :param alt: Altitude of the location (meters).
    :param ta: Ambient temperature (default is 12°C).
    :param p: Atmospheric pressure data (optional).
    :param pkl: Boolean flag to enable saving/loading results from pickle files. Default is True.
    :param folder: Path to the directory where pickle files are stored. Default is `DATA_PATH / "irr_limits"`.
    :param overwrite: Boolean flag to force recalculation of limits if set to True. Default is False.
    :param resample_freq: Frequency for resampling data (e.g., 'H' for hourly). Default is 'H'.

    :return: A tuple containing:
        - ghi_limit (pandas DataFrame): Estimated upper and lower limits for GHI.
        - bhi_limit (pandas DataFrame): Estimated upper and lower limits for BHI.
        - dhi_limit (pandas DataFrame): Estimated upper and lower limits for DHI.

    ------
    References

    [1] Charles Long and Yan Shi. “An Automated Quality Assessment and Control Algorithm
    for Surface Radiation Measurements”. In: The Open Atmospheric Science
    Journal 2 (Apr. 2008), pp. 23–37.
    """
    pkl_ghi_file = folder / \
                   f"ghi_limit_{resample_freq}_{lat}_{lon}_{index_H.min().strftime('%Y%m%d')}_{index_H.max().strftime('%Y%m%d')}.pkl"
    pkl_dhi_file = folder / \
                   f"dhi_limit_{resample_freq}_{lat}_{lon}_{index_H.min().strftime('%Y%m%d')}_{index_H.max().strftime('%Y%m%d')}.pkl"
    pkl_bhi_file = folder / \
                   f"bhi_limit_{resample_freq}_{lat}_{lon}_{index_H.min().strftime('%Y%m%d')}_{index_H.max().strftime('%Y%m%d')}.pkl"

    if (pkl and pkl_ghi_file.exists()) and (not overwrite):
        ghi_limit = pd.read_pickle(pkl_ghi_file)
        dhi_limit = pd.read_pickle(pkl_dhi_file)
        bhi_limit = pd.read_pickle(pkl_bhi_file)
    else:
        print('Calculating GHI limits...')
        solar_position_1min = get_solar_position_1m(index_H, lat, lon, alt, ta=ta, p=p, pkl=True)

        # Prepare input variables
        bni_toa = get_extra_radiation(solar_position_1min.index)
        zenith = solar_position_1min["apparent_zenith"].fillna(solar_position_1min["zenith"])
        angle_zenith = np.cos(zenith * np.pi / 180)
        aoi_angle = aoi(0, 180, zenith, solar_position_1min["azimuth"])
        ghi_toa = (bni_toa * np.cos(aoi_angle * np.pi / 180)).clip(lower=0)

        # Prepare TOA
        bni_toa_zenith = (bni_toa * (angle_zenith)).clip(lower=0)
        bni_toa_exp12 = (bni_toa * (angle_zenith ** (1.2))).clip(lower=0)
        bni_toa_exp02_zenith = ((bni_toa * 0.95 * (angle_zenith ** (0.2)) + 10) * angle_zenith).clip(lower=0).fillna(0)

        ghi_limit = pd.DataFrame(index=index_H)
        dhi_limit = pd.DataFrame(index=index_H)
        bhi_limit = pd.DataFrame(index=index_H)

        # GHI limits
        ghi_limit["lower"] = (ghi_toa.resample(resample_freq, label="right").min().reindex(index_H) * 0.03).fillna(0)
        ghi_limit["upper"] = np.array(
            [(ghi_toa.resample(resample_freq, label="right").max().reindex(index_H) * 1).clip(lower=0) + 100,
             (1.5 * bni_toa_exp12.resample(resample_freq, label="right").max().reindex(
                 index_H) + 100).fillna(0),
             (1.2 * bni_toa_exp12.resample(resample_freq, label="right").max().reindex(
                 index_H) + 50).fillna(0)]).min(0)

        # DHI limits
        dhi_limit["lower"] = (ghi_toa.resample(resample_freq, label="right").min().reindex(index_H) * 0.03).fillna(0)
        dhi_limit["upper"] = np.array(
            [(bni_toa.resample(resample_freq, label="right").max().reindex(index_H) * 0.8).clip(lower=0) + 50,
             (0.95 * bni_toa_exp12.resample(resample_freq, label="right").max().reindex(
                 index_H) + 50).fillna(0),
             (0.75 * bni_toa_exp12.resample(resample_freq, label="right").max().reindex(
                 index_H) + 30).fillna(0)]).min(0)

        # BHI
        bhi_limit["lower"] = 0
        bhi_limit["upper"] = np.array([bni_toa_zenith.resample(resample_freq, label="right").max().reindex(index_H),
                                       bni_toa_exp02_zenith.resample(resample_freq, label="right").max().reindex(
                                           index_H)]).min(0)

        ghi_limit = ghi_limit.shift(0)
        bhi_limit = bhi_limit.shift(0)
        dhi_limit = dhi_limit.shift(0)

        if pkl:
            ghi_limit.to_pickle(pkl_ghi_file)
            dhi_limit.to_pickle(pkl_dhi_file)
            bhi_limit.to_pickle(pkl_bhi_file)

    return ghi_limit, bhi_limit, dhi_limit


def get_poa_limits(tilt, azimuth, solar_position, lat, lon, alt, ta=12, p=None, resample_freq="H"):
    """
   Computes upper and lower plane-of-array (POA) irradiance limits based on GHI, DNI, and DHI.

   This function calculates the expected upper and lower limits of plane-of-array (POA) irradiance
   for a given surface tilt and azimuth, using solar position and irradiance component limits.

   :param tilt: Surface tilt angle (degrees).
   :param azimuth: Surface azimuth angle (degrees).
   :param solar_position: Pandas DataFrame containing solar position data (zenith and azimuth angles).
   :param lat: Latitude of the location.
   :param lon: Longitude of the location.
   :param alt: Altitude of the location (meters).
   :param ta: Ambient temperature (default is 12°C).
   :param p: Atmospheric pressure data (optional).
   :param resample_freq: Frequency for resampling data (e.g., 'H' for hourly). Default is 'H'.

   :return: A tuple containing:
       - poa_upper (pandas DataFrame): Upper limit of POA irradiance.
       - poa_lower (pandas DataFrame): Lower limit of POA irradiance.
   """

    ghi_limit, bhi_limit, dhi_limit = get_irr_limits(solar_position.index, lat, lon, alt, ta, p,
                                                     resample_freq=resample_freq)

    dni_extra = get_extra_radiation(solar_position.index)
    poa_upper = get_total_irradiance(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        dni=dni_extra,
        ghi=ghi_limit["upper"],
        dhi=dhi_limit["upper"],
        dni_extra=dni_extra,
        solar_zenith=solar_position['apparent_zenith'].fillna(solar_position['zenith']),
        solar_azimuth=solar_position['azimuth'], model="haydavies")

    poa_upper_2 = get_total_irradiance(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        dni=0,
        ghi=dhi_limit["upper"],
        dhi=dhi_limit["upper"],
        dni_extra=dni_extra,
        solar_zenith=solar_position['apparent_zenith'].fillna(solar_position['zenith']),
        solar_azimuth=solar_position['azimuth'], model="haydavies")

    for col in poa_upper.columns:
        poa_upper[col] = np.maximum(poa_upper[col], poa_upper_2[col])

    dni_extra = get_extra_radiation(solar_position.index)
    poa_lower = get_total_irradiance(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        dni=0,
        ghi=ghi_limit["lower"],
        dhi=dhi_limit["lower"],
        dni_extra=dni_extra,
        solar_zenith=solar_position['apparent_zenith'].fillna(solar_position['zenith']),
        solar_azimuth=solar_position['azimuth'], model="haydavies")
    poa_lower_2 = get_total_irradiance(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        dni=bhi_limit["lower"],
        ghi=ghi_limit["lower"],
        dhi=0,
        dni_extra=dni_extra,
        solar_zenith=solar_position['apparent_zenith'].fillna(solar_position['zenith']),
        solar_azimuth=solar_position['azimuth'], model="haydavies")

    for col in poa_lower.columns:
        poa_lower[col] = np.minimum(poa_lower[col], poa_lower_2[col])

    return poa_upper, poa_lower


def poa_limit_adj(poag, poab, poagrd, poa_upper=None, poa_lower=None, tilt=None, azimuth=None, solar_position=None):
    """
    This function ensures that the global POA irradiance (poag) remains within the calculated upper and lower
    physical limits. It also adjusts the diffuse and beam components accordingly.

    :param poag: Pandas Series of global POA irradiance values.
    :param poab: Pandas Series of direct POA irradiance values.
    :param poagrd: Pandas Series of ground-reflected POA irradiance values.
    :param poa_upper: Optional dataframe containing upper POA irradiance limits. If None, computed using `poa_limit`.
    :param poa_lower: Optional dataframe containing lower POA irradiance limits. If None, computed using `poa_limit`.
    :param tilt: Surface tilt angle (degrees). Required if `poa_upper` and `poa_lower` are not provided.
    :param azimuth: Surface azimuth angle (degrees). Required if `poa_upper` and `poa_lower` are not provided.
    :param solar_position: Pandas DataFrame containing solar position data (zenith and azimuth angles).
                           Required if `poa_upper` and `poa_lower` are not provided.

    :return: A tuple containing:
        - poa_scn_new (Pandas Series): Adjusted global POA irradiance.
        - poad_scn_new (Pandas Series): Adjusted diffuse POA irradiance.
        - poab_scn_new (Pandas Series): Adjusted direct POA irradiance.
        - poagrd_scn_new (Pandas Series): Unchanged ground-reflected POA irradiance.
    """

    if poa_upper is None or poa_lower is None:
        # Physical limits
        poa_upper, poa_lower = get_poa_limits(tilt, azimuth, solar_position)

    poa_scn_new = poag.clip(lower=poa_lower["poa_global"], upper=poa_upper["poa_global"])
    poad_scn_new = (poag - poab - poagrd).clip(lower=poa_lower["poa_diffuse"])
    poab_scn_new = (poa_scn_new - poad_scn_new - poagrd)  # readjustment if necessary
    poagrd_scn_new = poagrd

    return poa_scn_new, poad_scn_new, poab_scn_new, poagrd_scn_new
