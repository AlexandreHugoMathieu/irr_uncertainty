"""This script includes the function to apply the decomposition model"""
# Created by A. MATHIEU at 15/03/2023
import numpy as np
import pandas as pd

from pvlib import tools
from pvlib.irradiance import clearness_index


def apply_diffuse(kd, ghi, zenith, max_zenith, datetime_or_doy, kd_error=None):
    """
    Compute the diffuse horizontal irradiance (DHI) and direct normal irradiance (DNI) from
    the diffuse fraction (kd) and global horizontal irradiance (GHI).

    Copied from pvlib

    :param kd: Diffuse fraction.
    :param ghi: Global horizontal irradiance (W/m²).
    :param zenith: Solar zenith angle (degrees).
    :param max_zenith: Maximum allowable zenith angle before DNI is set to 0.
    :param datetime_or_doy (pd.DatetimeIndex): Day of year or datetime index.
    :param kd_error (pd.Series, optional): additional error for kd. Default is None.

    :return:tuple: (DNI, DHI) in W/m².
    """
    if kd_error is None:
        dhi = kd * ghi

        dni = (ghi - dhi) / tools.cosd(zenith)
        bad_values = (zenith > max_zenith) | (ghi < 0) | (dni < 0)
        dni = np.where(bad_values, 0, dni)
        # ensure that closure relationship remains valid
        dhi = np.where(bad_values, ghi, dhi)

        return dni, dhi

    elif type(kd_error) == pd.Series:
        df = (kd_error + kd).clip(lower=0, upper=1)
        dhi = df * ghi

        dni = (ghi - dhi) / tools.cosd(zenith)
        bad_values = (zenith > max_zenith) | (ghi < 0) | (dni < 0)
        dni = pd.Series(np.where(bad_values, 0, dni), index=datetime_or_doy)
        # ensure that closure relationship remains valid
        dhi = pd.Series(np.where(bad_values, ghi, dhi), index=datetime_or_doy)

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

    return kd


def erbs_AM(ghi,
            zenith,
            datetime_or_doy,
            dni_extra,
            kt: pd.Series = None,
            kd_error: pd.Series = None,
            min_cos_zenith=0.065,
            max_zenith=87):
    """
    Estimate DNI and DHI from GHI using the Erbs model.

    This function is adapted from the PVLIB implementation
    (https://pvlib-python.readthedocs.io/en/latest/_modules/pvlib/irradiance.html#erbs)
    to allow specifying `dni_extra` as an input.

    The Erbs model [1]_ estimates the diffuse fraction (DF) from global
    horizontal irradiance (GHI) through an empirical relationship between DF
    and the global clearness index (Kt). The diffuse fraction is used to compute
    diffuse horizontal irradiance (DHI) as:

    .. math::

        DHI = DF \times GHI

    Direct normal irradiance (DNI) is then estimated as:

    .. math::

        DNI = \frac{GHI - DHI}{\cos(Z)}

    where \( Z \) is the zenith angle.

    :param ghi: Global horizontal irradiance in W/m².
    :param zenith: True (not refraction-corrected) zenith angles in decimal degrees.
    :param datetime_or_doy: Day of the year (DOY) or array of DOY values (e.g., `pd.DatetimeIndex.dayofyear` or `pd.DatetimeIndex`).
    :param min_cos_zenith: Minimum value of cos(zenith) to allow when calculating the global clearness index `Kt`. Default is 0.065 (equivalent to a zenith of 86.273°).
    :param max_zenith: Maximum zenith angle allowed in the DNI calculation. DNI is set to 0 for zenith values greater than `max_zenith`. Default is 87°.

    :return: Tuple containing estimated (DNI, DHI).

    Reference
    ---------
        D. G. Erbs, S. A. Klein, and J. A. Duffie, "Estimation of the diffuse radiation fraction for hourly, daily, and monthly-average global radiation," *Solar Energy*, vol. 28, no. 4, pp. 293-302, 1982.

    """

    if kt is None:
        kt = clearness_index(ghi.fillna(0), zenith, dni_extra, min_cos_zenith=min_cos_zenith,
                             max_clearness_index=2)
    kt.loc[ghi.isna()] = np.nan

    kd = erbs_simple(kt)

    kd = pd.Series(kd, index=datetime_or_doy)
    dni, dhi = apply_diffuse(kd, ghi, zenith, max_zenith, datetime_or_doy, kd_error)

    return dni, dhi, kt, kd
