"""This script includes the function to apply the decomposition model"""
# Created by A. MATHIEU at 15/03/2023
import numpy as np
import pandas as pd

from pvlib import tools
from pvlib.irradiance import get_extra_radiation, get_total_irradiance, dni
from pvlib.tools import cosd

from irr_uncertainty.data.solar_data import get_solar_position_1m, get_poaextra


def apply_diffuse(kd, ghi, zenith, max_zenith):
    """
    Compute the diffuse horizontal irradiance (DHI) and direct normal irradiance (DNI) from
    the diffuse fraction (kd) and global horizontal irradiance (GHI).

    Copied from pvlib

    :param kd: Diffuse fraction.
    :param ghi: Global horizontal irradiance (W/m²).
    :param zenith: Solar zenith angle (degrees).
    :param max_zenith: Maximum allowable zenith angle before DNI is set to 0.
    :param datetime_or_doy (pd.DatetimeIndex): Day of year or datetime index.

    :return:tuple: (DNI, DHI) in W/m².
    """
    dhi = kd * ghi

    dni = (ghi - dhi) / tools.cosd(zenith)
    bad_values = (zenith > max_zenith) | (ghi < 0) | (dni < 0)
    dni = np.where(bad_values, 0, dni)
    # ensure that closure relationship remains valid
    dhi = np.where(bad_values, ghi, dhi)

    return dni, dhi


def erbs_simple(kt):
    """
    Compute the diffuse fraction (kd) using the Erbs model based on the clearness index (Kt).

    Copied from pvlib.

    :param kt (numeric): Clearness index.

    :return: Diffuse fraction (kd).
    """
    # For Kt <= 0.22, set the diffuse fraction
    kd = 1 - 0.09 * kt

    # For Kt > 0.22 and Kt <= 0.8, set the diffuse fraction
    kd = np.where((kt > 0.22) & (kt <= 0.8),
                  0.9511 - 0.1604 * kt + 4.388 * kt ** 2 -
                  16.638 * kt ** 3 + 12.336 * kt ** 4,
                  kd)

    # For Kt > 0.8, set the diffuse fraction
    kd = np.where(kt > 0.8, 0.165, kd)

    if type(kt) is pd.Series:
        kd = pd.Series(kd, index=kt.index)

    return kd


def get_kt(ghi, lat, lon, alt, ta=None, p=None, return_ghiextra_elev=False, max_clearness_index=2):
    """Compute the reference satellite clearness index"""

    solar_position_1m = get_solar_position_1m(ghi.index, lat, lon, alt, ta=ta, p=p, pkl=True)
    zenith_1m = solar_position_1m["apparent_zenith"].fillna(solar_position_1m["zenith"])
    elevation_1m = solar_position_1m["apparent_elevation"].fillna(solar_position_1m["elevation"])
    dni_extra_1m = get_extra_radiation(solar_position_1m.index)
    ghi_extra_1m = dni_extra_1m * np.maximum(cosd(zenith_1m), 0)
    i0h = dni_extra_1m * np.maximum(cosd(zenith_1m), 0.065)

    # Compute kt
    kt = ghi / i0h.resample("H").mean().reindex(ghi.index)
    kt = np.maximum(kt, 0)
    kt_ts = np.minimum(kt, max_clearness_index)

    if return_ghiextra_elev:
        # start of time integration
        dni_extra = dni_extra_1m.resample("H").mean().reindex(ghi.index)
        ghi_extra = ghi_extra_1m.resample("H").mean().reindex(ghi.index)
        elevation = elevation_1m.resample("H").mean().reindex(ghi.index)

        return kt_ts, ghi_extra, dni_extra, elevation
    else:
        return kt_ts


def get_kpoa(times, lat, lon, alt, tilt, surface_azimuth, ta=None, p=None, poa=None, ghi=None):
    solar_position_1m = get_solar_position_1m(times, lat, lon, alt, ta=ta, p=p, pkl=True)
    zenith_1m = solar_position_1m["apparent_zenith"].fillna(solar_position_1m["zenith"])
    dni_extra_1m = get_extra_radiation(solar_position_1m.index)

    poa_extra, aoi_angle = get_poaextra(times, lat, lon, alt, tilt, surface_azimuth,
                       solar_position_1m=solar_position_1m,
                       dni_extra_1m=dni_extra_1m,
                       ta=ta, p=p, freq="H")

    if poa is None:
        # Start of time integration (end-of-time convention)
        dni_extra = dni_extra_1m.resample("H").mean().reindex(times)
        zenith = zenith_1m.resample("H").mean().reindex(times)
        azimuth = solar_position_1m["azimuth"].resample("h").mean().reindex(times)

        # Compute dhi/dni
        kt = get_kt(ghi, lat, lon, alt, ta=None, p=None)
        kd = erbs_simple(kt)
        dhi = kd * ghi
        dni_ts = dni(ghi, dhi, zenith)

        poa = get_total_irradiance(
            surface_tilt=tilt,
            surface_azimuth=surface_azimuth,
            solar_zenith=zenith,
            solar_azimuth=azimuth,
            dni=dni_ts,
            ghi=ghi,
            dhi=dhi,
            dni_extra=dni_extra,
            model="haydavies"
        )["poa_global"]

    kpoa = (poa / poa_extra)

    return kpoa, poa_extra, aoi_angle
