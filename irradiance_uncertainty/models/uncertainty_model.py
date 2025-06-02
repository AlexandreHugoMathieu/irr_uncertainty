""" This module includes function to model irradiance uncertainty"""
# Created by A. MATHIEU at 27/10/2023
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import scipy.stats
import seaborn as sns

from tqdm import tqdm
from pvlib.irradiance import dni, get_extra_radiation, get_total_irradiance
from pvlib.tools import cosd
from PyAstronomy import pyasl
from scipy.stats import gaussian_kde
from typing import Union

from irradiance_uncertainty.config import Config, DATA_PATH
from irradiance_uncertainty.data.irr_data import load_bsrn_data
from irradiance_uncertainty.models.irr_limits import get_irr_limits, get_poa_limits, poa_limit_adj
from irradiance_uncertainty.models.optic_model import erbs_AM
from irradiance_uncertainty.models.uncertainty_config import euro_stations, START_BSRN, END_BSRN
from irradiance_uncertainty.utils import bestdistfit, dist_transfo, poly_func

image_folder = DATA_PATH / "images" / "irr_uncertainty"


def get_kd_dist_v2(
        overwrite=False,
        plot_bool=False,
        train_index=euro_stations[:int(0.75 * len(euro_stations))],
        kt_range: Union[list, None] = None,
        user=Config().bsrn()[0],
        password=Config().bsrn()[1],
        sat_source="cams_pvlib",
        legend: bool = True):
    """
    Computes and stores the distribution of kd-error values for different kt intervals.

    This function estimates the kd-error distributions for each kt-interval from 0 to 1,
    using kernel density estimation (KDE) on residuals between measured and modeled kd values.

    If a precomputed distribution exists, it loads the data from a pickle file unless `overwrite=True`.
    Optionally, it can also plot the distributions for each interval.

    :param overwrite: Boolean flag to force recalculation of kd-error distributions if set to True. Default is False.
    :param plot_bool: Boolean flag to enable plotting of KDE distributions. Default is False.
    :param train_index: List of station indices used for training. Default is 75% of `euro_stations`.
    :param kt_range: Array of kt values defining the intervals for error distribution estimation. Default is None, which sets it to `np.arange(0, 1, 0.05).round(2)`.
    :param user: Username for accessing BSRN data. Default is retrieved from `Config().bsrn()`.
    :param password: Password for accessing BSRN data. Default is retrieved from `Config().bsrn()`.
    :param sat_source: Satellite source: "cams_pvlib" as only option for now.
    :param legend: print the legend ?

    :return: A pandas DataFrame containing the estimated kd-error distributions and fitted parameters.
    """
    kd_dist_path = DATA_PATH / "irr_data" / f"kd_dist_v2_{sat_source}_{str(kt_range)}.pkl"

    if (not os.path.exists(kd_dist_path)) or overwrite:

        step_kt = 0.05
        if kt_range is None:
            kt_range = np.arange(0, 1, step_kt).round(2)

        kd_dist = pd.DataFrame(columns=kt_range)
        kd_dist.loc["#"] = 0
        x_vals = np.arange(-1, 1, 0.001)

        for kt in tqdm(kt_range,
                       desc=f"Estimate the kd-error distributions for each {step_kt} kt-interval"):
            if plot_bool:
                pal = sns.color_palette("Spectral", len(train_index))
                plt.figure(figsize=(5, 6))
                plt.title("$kt^{ref}$ in " + f"[{kt}, {round(kt + step_kt, 2)}]")

            df_kde_vals = pd.DataFrame(index=x_vals)

            for i, station in enumerate(train_index):
                sat_data, insitu_data, solar_position = load_bsrn_data(START_BSRN, END_BSRN, station, user, password,
                                                                       sat_source=sat_source)
                filter = (insitu_data["ghi"] > 0) & (sat_data["ghi"] > 0)

                zenith = solar_position["apparent_zenith"].fillna(solar_position["zenith"])
                dni_extra = get_extra_radiation(insitu_data.index)
                _, _, kt_erbs, kd_erbs = erbs_AM(insitu_data["ghi"], zenith, insitu_data.index, dni_extra)

                filter = filter & (kt_erbs > kt) & (kt_erbs < kt + 0.05)
                error_kd = (insitu_data["kd"].tz_convert("CET") - kd_erbs.tz_convert("CET")).loc[filter].astype(float)

                if len(error_kd) > 100:
                    kd_dist.loc["#", kt] += 1
                    if plot_bool:
                        ax = sns.kdeplot(error_kd, color=pal[i], label=station, linewidth=1.5)

                    # Get KDE values for the range of x-values
                    kde = gaussian_kde(error_kd)
                    kde_vals = kde(x_vals)
                    df_kde_vals.loc[x_vals, station] = kde_vals

            if not df_kde_vals.empty:
                avg = df_kde_vals.mean(axis=1)
                name_str, loc, scale = bestdistfit(avg)

                if plot_bool:
                    x = np.arange(ax.get_xlim()[0], ax.get_xlim()[1], 0.001)
                    avg = avg.loc[(avg.index > ax.get_xlim()[0]) & (avg.index < ax.get_xlim()[1])]
                    avg.plot(color="dodgerblue", linewidth=2.5, label="Average Distribution \n over the stations")

                kd_dist.loc["dist", kt] = name_str
                kd_dist.loc["loc", kt] = loc
                kd_dist.loc["scale", kt] = scale

                if plot_bool:
                    if name_str == "norm":
                        y = scipy.stats.norm.pdf(x, loc, scale)
                        plt.plot(x, y, color="blue", linewidth=4, label="Gaussian fit \n$\mu$=" + str(round(loc, 2)) +
                                                                        "$, \sigma$=" + str(round(scale, 2)))
                    elif name_str == "gumbel_l":
                        y = scipy.stats.gumbel_l.pdf(x, loc, scale)
                        plt.plot(x, y, linewidth=4, label="Gumbel (left) fit \n$\mu$=" + str(round(loc, 2)) +
                                                          "$, \sigma$=" + str(round(scale, 2)), color="blue")
                    elif name_str == "gumbel_r":
                        y = scipy.stats.gumbel_r.pdf(x, loc, scale)
                        plt.plot(x, y, linewidth=4, label="Gumbel (right) fit \n$\mu$=" + str(round(loc, 2)) +
                                                          "$, \sigma$=" + str(round(scale, 2)), color="blue")

                    if legend:
                        plt.legend(fontsize=14)
                        ax = plt.gca()
                        for item in ([ax.xaxis.label, ax.yaxis.label] + ax.get_xticklabels() + ax.get_yticklabels()):
                            item.set_fontsize(13)

                    else:
                        plt.ylabel(None)  # remove the y-axis label

                    if plot_bool:
                        plt.tight_layout()
                    plt.savefig(
                        DATA_PATH / "irr_data" / "images" / f"residual_kd_v2_{int(kt * 100)}_legend{legend}.png")

        kd_dist.to_pickle(kd_dist_path)
    else:
        kd_dist = pd.read_pickle(kd_dist_path)

    return kd_dist


def irrh_scenarios(lat, long, alt,
                   solar_position: pd.DataFrame,
                   ghi: pd.Series,
                   n_scenarios: int = 1000,
                   kt_mu: float = 0.0104,
                   params_kt_less15: list = [0.2484, -0.1098, -1.297, 2.6225, -1.5656],
                   params_kt_over15: list = [0.1819, -1.3449, 5.8941, -9.335, 4.7071],
                   factor_kt=1.35,
                   factor_kd=1.3,
                   kt_autocorr: float = 0.27,
                   kd_autocorr: float = 0.47,
                   sat_source="cams_pvlib",
                   ) -> pd.DataFrame:
    """
    Generate Monte Carlo simulations to account for irradiance uncertainty on the horizontal plane.

    :param lat: Latitude of the installation [°]
    :param long: Longitude of the installation [°]
    :param alt:  Altitude of the installation [m]
    :param solar_position: Solar position dataframe with an hourly granularity with azimuth/elevation/zenith columns
    :param ghi: Global Horizontal Irradiance timeserie (provided from satellite data)
    :param n_scenarios: Number of Monte Carlo simulations to generate
    :param kt_mu: Second parameter of the Gaussian distribution (standard deviation) for the constant clearness index bais (first parameter = 0/centered)
    :param params_kt_less15: 5-parameter of the 5-degree polynomial function calculating the standard deviation as
        function of the satellite $kt^{ref}$ (computed from GHI) for the sun elevation under 15°
    :param params_kt_over15: 5-parameter of the 5-degree polynomial function calculating the standard deviation as
        function of the satellite $kt^{ref}$ (computed from GHI) for the sun elevation over 15°
    :param factor_kt: kt-distribution widening parameter
    :param factor_kd: kd-distribution widening parameter
    :param kt_autocorr: Residual autocorrelation for the clearness index
    :param kd_autocorr: Residual autocorrelation for the diffuse ratio
    :param sat_source: What satellite provider for the kd-error modeling ? "cams_pvlib" as only option for now


    :return: 3 pd.DataFrames with "n_scenarios" columns and same index as "ghi" containing the GHI/DHI/BHI Monte Carlo simulations
    """
    # Prepare recipients
    ghi_scns, bhi_scns, dhi_scns = {}, {}, {}

    # Set lower/higher limits with clearsky GHI for DNI and BHI, deduct DHI
    ghi_limit, bhi_limit, dhi_limit = get_irr_limits(solar_position.index, lat, long, alt)

    # Compute the reference satellite clearness index
    zenith = solar_position["apparent_zenith"].fillna(solar_position["zenith"])
    elevation = solar_position["apparent_elevation"].fillna(solar_position["elevation"])
    dni_extra = get_extra_radiation(ghi.index)
    ghi_extra = dni_extra * np.maximum(cosd(zenith), 0.065)
    _, _, kt_ts, _ = erbs_AM(ghi, zenith, ghi.index, dni_extra)

    # Get the residual distributions for the diffuse fraction
    kd_dist = get_kd_dist_v2(sat_source=sat_source)
    kd_dist.loc[:, (kd_dist.loc["#"] < 5)] = np.nan
    kd_dist = kd_dist.bfill(axis=1).ffill(axis=1)

    # Separate indexes
    index_pos = ghi[ghi > 0].index
    index_pos_less15 = ghi[(ghi > 0) & (elevation < 15)].index
    index_pos_over15 = ghi[(ghi > 0) & (elevation >= 15)].index

    kd_res_df = pd.DataFrame(data=np.nan, index=ghi.index, columns=range(n_scenarios))
    for n in tqdm(range(n_scenarios), disable=(n_scenarios < 20), desc="Horizontal Irradiation scenarios"):
        ##### GHI #####

        biais_ts = np.random.normal(loc=0, scale=kt_mu)  # Constant bias

        # Residual noise
        kt_res_norm = pd.Series(pyasl.expCorrRN(len(index_pos), -1 / np.log(kt_autocorr), mean=0, std=1),
                                index=index_pos)
        modulated_std_less15 = poly_func(kt_ts.loc[index_pos_less15], *params_kt_less15)
        modulated_std_over15 = poly_func(kt_ts.loc[index_pos_over15], *params_kt_over15)
        modulated_std = pd.concat([modulated_std_less15, modulated_std_over15]).sort_index().clip(lower=0.0) * factor_kt

        kt_scn = (kt_ts + biais_ts).copy() + (kt_res_norm) * modulated_std

        # Temporary collect it
        ghi_scns[n] = (kt_scn * ghi_extra).fillna(0).copy().clip(lower=ghi_limit["lower"], upper=ghi_limit["upper"])

        ##### Decomposition #####
        # Base diffuse ratio
        _, _, _, kd_ts = erbs_AM(ghi_scns[n], solar_position["zenith"], ghi.index, dni_extra)

        # Apply error on kd with erb models to get DHI, BHI
        kd_res_norm = pd.Series(pyasl.expCorrRN(len(ghi[ghi > 0].index), -1 / np.log(kd_autocorr), mean=0, std=1),
                                index=index_pos)  # Normalized error
        for kt in kd_dist.columns:  # scenario
            filter_irr = ((kt_ts >= kt) & (kt_ts < (kt + 0.05))) if kt != 0.95 else (kt_ts >= kt)
            filter_irr = filter_irr & (ghi > 0)
            kd_res_df.loc[filter_irr, n] = dist_transfo(kd_res_norm.loc[filter_irr], kd_dist, kt) * factor_kd

        # Apply kd error
        kd_scn = (kd_ts + kd_res_df[n]).clip(lower=0, upper=1)

        # Collect simulations and clip to physical limits
        dhi_scns[n] = \
            (kd_scn * ghi_scns[n]).clip(lower=dhi_limit["lower"], upper=dhi_limit["upper"]).fillna(0)
        bhi_scns[n] = \
            (ghi_scns[n] - dhi_scns[n]).clip(lower=bhi_limit["lower"], upper=bhi_limit["upper"]).fillna(0)
        ghi_scns[n] = \
            (bhi_scns[n] + dhi_scns[n]).clip(lower=ghi_limit["lower"], upper=ghi_limit["upper"]).fillna(0)

    return pd.DataFrame(ghi_scns), pd.DataFrame(dhi_scns), pd.DataFrame(bhi_scns)


def generate_transpo_error(poag):
    """
    Generates stochastic transposition errors for POA irradiance based on literature-reviewed biases.

    This function simulates the uncertainty inherent in transposition models by generating
    a time series of stochastic errors for plane-of-array (POA) irradiance. The error is modeled
    using a mean bias and standard deviation derived from literature, accounting for both systematic
    and random deviations observed in transposition studies. The generated errors follow an
    exponentially correlated (0.4 of autocorrelation) random noise process to reflect real-world fluctuations.

    Mean Biais: [-3%:3%]

    Error standard deviation [5%:9%]

    References
    ----------

    [1] Anne Migan Dubois et al., "Estimation of the Uncertainty due to Each Step of Simulating the Photovoltaic Conversion under Real Operating Conditions," International Journal of Photoenergy, 2021.

    [2] Christian A. Gueymard, "Direct and indirect uncertainties in the prediction of tilted irradiance for solar engineering applications," Solar Energy, 2009.

    [3] Riyad Mubarak et al., "Comparison of Modeled and Measured Tilted Solar Irradiance for Photovoltaic Applications" Energies, 2017.

    [4] Matthew Lave et al., "Evaluation of Global Horizontal Irradiance to Plane-of-Array Irradiance Models at Locations Across the United States," IEEE Journal of Photovoltaics, 2015.

    :param poag: Pandas Series of global POA irradiance values.

    :return: A Pandas Series of stochastic transposition errors, indexed by time.
    """

    # Apply literature-based biases and stochastic error modeling
    me_poa = np.random.normal(0, 1.5) / 100  # Mean bias from literature review
    std_poa = np.random.uniform(5, 9) / 100  # Standard deviation from literature review

    # Generate a gaussian error
    index_pos = poag.loc[poag > 0].index
    res_ts = pd.Series(pyasl.expCorrRN(len(index_pos), -1 / np.log(0.4), me_poa, std_poa), index=index_pos)

    return res_ts


def add_transpo_error(poag, poab, poagrd, poa_upper=None, poa_lower=None, tilt=None, azimuth=None, solar_position=None,
                      res_ts=None):
    """
    Applies transposition error to POA irradiance and adjusts within physical limits.

    This function perturbs the POA irradiance with a random transposition error and ensures
    that the resulting values remain within physical constraints.

    :param poag: Pandas Series of global POA irradiance values.
    :param poab: Pandas Series of direct POA irradiance values.
    :param poagrd: Pandas Series of ground-reflected POA irradiance values.
    :param poa_upper: Optional dataframe containing upper POA irradiance limits. If None, computed using `poa_limit`.
    :param poa_lower: Optional dataframe containing lower POA irradiance limits. If None, computed using `poa_limit`.
    :param tilt: Surface tilt angle (degrees). Required if `poa_upper` and `poa_lower` are not provided.
    :param azimuth: Surface azimuth angle (degrees). Required if `poa_upper` and `poa_lower` are not provided.
    :param solar_position: Pandas DataFrame containing solar position data (zenith and azimuth angles).
    :param res_ts: Optional time series of transposition errors. If None, generated using `generate_transpo_error`.

    :return: A tuple containing:
        - poa_scn_new (Pandas Series): Adjusted global POA irradiance.
        - poad_scn_new (Pandas Series): Adjusted diffuse POA irradiance.
        - poab_scn_new (Pandas Series): Adjusted direct POA irradiance.
        - poagrd_scn_new (Pandas Series): Unchanged ground-reflected POA irradiance.
    """

    if res_ts is None:
        res_ts = generate_transpo_error(poag)
    poa_scn = poag + res_ts * poag

    poa_scn_new = poa_scn
    poa_scn_new, poad_scn_new, poab_scn_new, poagrd_scn_new = \
        poa_limit_adj(poa_scn_new, poab, poagrd, poa_upper, poa_lower, tilt, azimuth, solar_position)

    return poa_scn_new, poad_scn_new, poab_scn_new, poagrd_scn_new


def transpo_scenarios(tilt: Union[int, float],
                      azimuth: Union[int, float],
                      lat: Union[int, float],
                      long: Union[int, float],
                      alt: Union[int, float],
                      solar_position: pd.DataFrame,
                      ghi_scns: pd.DataFrame,
                      dhi_scns: pd.DataFrame,
                      n_scenarios: int = 1000) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Generates Monte Carlo transposition simulations for plane-of-array (POA) irradiance from Horizontal simulations
    (ghi_scns, dhi_scns).

    This function simulates uncertainty in transposition modeling by generating multiple POA irradiance
    simulations.
    Stochastic variability is introduced through randomized biases and standard deviations,
    derived from literature-reviewed uncertainties.

    The function allows for biasing toward a target POA irradiance (`poa_target`) if provided,
    ensuring scenario realism by maintaining physical irradiance constraints. (For pyranometers)

    **Methodology:**

        - Determines physical POA irradiance limits based on site-specific parameters.
        - Applies a transposition model to compute POA components (direct, diffuse, and ground-reflected).
        - Introduces uncertainty through random perturbations, maintaining consistency with literature.

    :param tilt: Surface tilt angle in degrees.
    :param azimuth: Surface azimuth angle in degrees.
    :param lat: Latitude of the location in decimal degrees.
    :param long: Longitude of the location in decimal degrees.
    :param alt: Altitude of the location in meters.
    :param solar_position: Pandas DataFrame containing solar position data, including zenith and azimuth angles.
    :param ghi_scns: pd.DataFrame where keys are scenario indices and values are Pandas Series of
                     global horizontal irradiance (GHI).
    :param dhi_scns: pd.DataFrame where keys are scenario indices and values are Pandas Series of
                     diffuse horizontal irradiance (DHI).
    :param n_scenarios: Number of Monte Carlo scenarios to generate (default: 1000).

    :return: A tuple of four Pandas DataFrames containing scenario data:
        - `poa_scns`: Global POA irradiance scenarios.
        - `poad_scns`: Diffuse POA irradiance scenarios.
        - `poab_scns`: Direct POA irradiance scenarios.
        - `poagrd_scns`: Ground-reflected POA irradiance scenarios.
    """

    # Recipients
    poa_scns, poab_scns, poad_scns, poagrd_scns = {}, {}, {}, {}

    # Physical limits
    poa_upper, poa_lower = get_poa_limits(tilt, azimuth, solar_position, lat, long, alt)

    # Transposition
    dni_extra = get_extra_radiation(ghi_scns.index)
    for n in tqdm(range(n_scenarios), disable=(n_scenarios < 20), desc="POA Irradiance simulations"):
        dni_ts = dni(ghi_scns[n], dhi_scns[n], solar_position["apparent_zenith"].fillna(solar_position["zenith"]),
                     clearsky_dni=dni_extra)
        poa = get_total_irradiance(
            surface_tilt=tilt,
            surface_azimuth=azimuth,
            dni=dni_ts.fillna(0),
            ghi=ghi_scns[n].fillna(0),
            dhi=dhi_scns[n].fillna(0),
            dni_extra=dni_extra.fillna(0),
            albedo=0.2,
            solar_zenith=solar_position['apparent_zenith'].fillna(solar_position["zenith"]),
            solar_azimuth=solar_position['azimuth'], model="haydavies")

        poa_scns[n], poad_scns[n], poab_scns[n], poagrd_scns[n] = \
            add_transpo_error(poa["poa_global"], poa["poa_direct"], poa["poa_ground_diffuse"],
                              poa_upper, poa_lower, tilt, azimuth, solar_position)

    poa_scns, poad_scns, poab_scns, poagrd_scns = \
        pd.DataFrame(poa_scns), pd.DataFrame(poad_scns), pd.DataFrame(poab_scns), pd.DataFrame(poagrd_scns)

    if n_scenarios == 1:
        poa_scns = poa_scns[0]
        poad_scns = poad_scns[0]
        poab_scns = poab_scns[0]
        poagrd_scns = poagrd_scns[0]

    return poa_scns, poad_scns, poab_scns, poagrd_scns
