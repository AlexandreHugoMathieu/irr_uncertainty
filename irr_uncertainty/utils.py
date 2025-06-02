""" This modules contains all util functions to calculate indicators and format plots"""
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import warnings
import scipy
import seaborn as sns

from tqdm import tqdm
from scipy.optimize import curve_fit

from irr_uncertainty.data.irr_data import load_bsrn_data

blue = (40 / 255, 106 / 255, 162 / 255)


def q_plot(data: pd.DataFrame, quantiles=[0.1, 0.5, 0.95], figsize=(8, 5), color="b", ax=None, line=False, label="",
           tweak=False):
    """
    Plots quantile intervals as shaded regions over time for a given DataFrame.

    This function visualizes uncertainty by plotting quantile intervals (e.g., 10%, 50%, 95%) as shaded areas.
    It computes the symmetric quantiles around the median and optionally adds boundary lines. The transparency
    of each shaded region depends on the number of quantiles, and the legend can be optionally adjusted.

    :param data: A pandas DataFrame with time-like index and columns representing different samples or scenarios.
    :param quantiles: List of quantile widths to plot (e.g., [0.1, 0.5, 0.95] for 10%, 50%, and 95% intervals). Default is [0.1, 0.5, 0.95].
    :param figsize: Tuple defining the size of the plot. Default is (8, 5).
    :param color: Color for the shaded quantile regions and optional lines. Default is "b" (blue).
    :param ax: Matplotlib Axes object. If None, a new figure and axes are created. Default is None.
    :param line: Boolean flag to plot boundary lines for each quantile interval. Default is False.
    :param label: Label prefix for each quantile interval in the legend. Default is an empty string.
    :param tweak: Boolean flag to adjust alpha levels in the legend for better visibility. Default is False.

    :return: Matplotlib Axes object with the quantile plot.
    """

    plt.style.use("ggplot")

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    alpha = 1 / len(quantiles)
    for i, q in enumerate(quantiles):
        q1 = 0.5 - q / 2
        q2 = 0.5 + q / 2

        qs = data.quantile([q1, q2], axis=1).T
        q_string = f"{label} {int(q * 100)}%-interval"
        ax.fill_between(qs.index, qs[q1], qs[q2], alpha=alpha, color=color, label=q_string)

        if line:
            ax.plot(qs.index, qs[q1], alpha=alpha, color=color)
            ax.plot(qs.index, qs[q2], alpha=alpha, color=color)

    leg = ax.legend()
    for i, lh in enumerate(leg.legendHandles):
        if tweak:
            lh.set_alpha(1 - (i) / (len(quantiles) + 1))
        else:
            lh.set_alpha(1 - (i + 1) / (len(quantiles) + 1))
    plt.tight_layout()

    return ax


def calculate_kt_kpis(euro_stations: list, start: pd.Timestamp, end: pd.Timestamp, user: str, password: str,
                      YEARS, sat_source):
    """
    Calculate the Kt error as function of the provided (satellite) kt/clearness index by 5% interval

    :param euro_stations: BSRN stations in Europe
    :param start: Start of the analysis
    :param end: End of the analysis
    :param user, password: credentials to get BSRN data (in secret.ini file)
    :param sat_source: What satellite provider ? "helioclim" (3v5) or "cams_pvlib"

    :return: two dataframes (columns: BSRN station, index: kt-interval)
    """
    step_kt = 0.05  # 5% interval
    kt_range = np.arange(0, 1, step_kt).round(2)  # All intervals

    # Recipients
    std_kt_kt_less15 = pd.DataFrame(columns=euro_stations, index=kt_range, dtype=float)
    std_kt_kt_over15 = pd.DataFrame(columns=euro_stations, index=kt_range, dtype=float)

    # Loop through all stations
    for station in tqdm(euro_stations):
        # Load data
        sat_data, insitu_data, solar_position = load_bsrn_data(start, end, station, user, password,
                                                               sat_source=sat_source)
        elevation = solar_position["apparent_elevation"].fillna(solar_position["elevation"])

        # Error calculations
        error_kt = (insitu_data["kt"].tz_convert("CET") - sat_data["kt"].tz_convert("CET")).astype(float)

        # Apply the filter to only keep relevant data
        filter_y = (np.isin(insitu_data.index.year, YEARS[station]))
        filter_less15 = filter_y & (insitu_data["ghi"] > 0) & (sat_data["ghi"] > 0) & (elevation < 15)
        filter_over15 = filter_y & (insitu_data["ghi"] > 0) & (sat_data["ghi"] > 0) & (elevation >= 15)

        # Loop through all the kt-intervals
        for kt in kt_range:
            # Apply the kt-interval filter on top of the others
            filter_kt = (sat_data["kt"] >= kt) & (sat_data["kt"] < kt + step_kt)
            filter_all_less15 = filter_less15 & filter_kt
            filter_all_over15 = filter_over15 & filter_kt

            # Store data only if there are more than 100 points available
            if len(error_kt.loc[filter_all_less15].dropna()) > 50:
                std_kt_kt_less15.loc[kt, station] = error_kt.loc[filter_all_less15].dropna().std()
                std_kt_kt_less15.loc[kt, station] = (error_kt.loc[filter_all_less15].dropna() ** 2).mean() ** (1 / 2)

            # Store data only if there are more than 100 points available
            if len(error_kt.loc[filter_all_over15].dropna()) > 50:
                std_kt_kt_over15.loc[kt, station] = error_kt.loc[filter_all_over15].dropna().std()
                std_kt_kt_over15.loc[kt, station] = (error_kt.loc[filter_all_over15].dropna() ** 2).mean() ** (1 / 2)

    return std_kt_kt_less15, std_kt_kt_over15


def poly_func(x, a, b, c, d, e):
    """ 5th-degree polynomial function with [a,b,c,d,e] coefficients"""
    y = a + b * x + c * x ** 2 + d * x ** 3 + e * x ** 4
    return y


def bestdistfit(avg: pd.Series, plot_bool: bool = False):
    """
    Determines the best-fitting statistical distribution for a given dataset.

    This function fits three probability distributions (normal, left-skewed Gumbel, and right-skewed Gumbel)
    to the provided dataset and selects the one with the lowest root mean square error (RMSE).

    Optionally, it can also plot the fitted distributions.

    :param avg: Pandas Series representing the dataset to fit distributions to.
    :param plot_bool: Boolean flag to enable plotting of the fitted distributions. Default is False.

    :return: A tuple containing:
        - name_str (str): Name of the best-fitting distribution ('norm', 'gumbel_l', or 'gumbel_r').
        - loc (float): Estimated location parameter of the best-fitting distribution.
        - scale (float): Estimated scale parameter of the best-fitting distribution.
    """

    def func_norm(x_vals, loc, scale):
        pdf_values = scipy.stats.norm.pdf(x_vals, loc, scale)
        return pdf_values

    def func_gumbel_l(x_vals, loc, scale):
        pdf_values = scipy.stats.gumbel_l.pdf(x_vals, loc, scale)
        return pdf_values

    def func_gumbel_r(x_vals, loc, scale):
        pdf_values = scipy.stats.gumbel_r.pdf(x_vals, loc, scale)
        return pdf_values

    # Fit and get estimated values
    popt_norm, _ = curve_fit(func_norm, avg.index, avg.values)
    popt_gumbel_l, pcov = curve_fit(func_gumbel_l, avg.index, avg.values)
    popt_gumbel_r, pcov = curve_fit(func_gumbel_r, avg.index, avg.values)
    norm_values = func_norm(avg.index, popt_norm[0], popt_norm[1])
    gumbel_l_values = func_gumbel_l(avg.index, popt_gumbel_l[0], popt_gumbel_l[1])
    gumbel_r_values = func_gumbel_r(avg.index, popt_gumbel_r[0], popt_gumbel_r[1])

    # RMSE
    rmse_norm = ((norm_values - avg.values) ** 2).mean() ** (1 / 2)
    gumbel_l_norm = ((gumbel_l_values - avg.values) ** 2).mean() ** (1 / 2)
    gumbel_r_norm = ((gumbel_r_values - avg.values) ** 2).mean() ** (1 / 2)

    name_str, loc, scale = None, None, None
    if (rmse_norm < gumbel_l_norm) & (rmse_norm < gumbel_r_norm):
        name_str = "norm"
        loc, scale = popt_norm[0], popt_norm[1]
    elif (gumbel_l_norm < rmse_norm) & (gumbel_l_norm < gumbel_r_norm):
        name_str = "gumbel_l"
        loc, scale = popt_gumbel_l[0], popt_gumbel_l[1]
    elif (gumbel_r_norm < gumbel_l_norm) & (gumbel_r_norm < rmse_norm):
        name_str = "gumbel_r"
        loc, scale = popt_gumbel_r[0], popt_gumbel_r[1]

    if plot_bool:
        plt.figure()
        plt.plot(avg.index, norm_values)
        plt.plot(avg.index, gumbel_l_values)
        plt.plot(avg.index, gumbel_r_values)
        avg.plot(color="red")

    return name_str, loc, scale


def dist_transfo(values, dist_df, kt):
    """
    Disribution transformation from a normalized Gaussian to the distribution which is associated to "kt"-interval

    :param values: Generated values from the 1st distribution which is a normalized gaussian
    :param dist_df: DataFrame with the parameters for the 2nd distribution.
        Three rows: ["dist", "loc", "scale"]
            In "dist", there are the distribution names ("gumber_l": Gumbel left, "gumbel_r": Gumbel right, "norm": Normal)
            "loc" and "scale" include the two distribution parameters
        Columns: kt-interval
    :param kt:

    :return: Distribution-transformed values
    """
    loc, scale = dist_df.loc["loc", kt], dist_df.loc["scale", kt]

    if dist_df.loc["dist", kt] == "norm":
        cdf_values = scipy.stats.norm.cdf(values, loc=0, scale=1)
        dist_values = scipy.stats.norm.ppf(cdf_values, loc, scale)
    else:
        cdf_values = scipy.stats.norm.cdf(values, loc=0, scale=1)
        if dist_df.loc["dist", kt] == "gumbel_l":
            dist_values = scipy.stats.gumbel_l.ppf(cdf_values, loc, scale)
        elif dist_df.loc["dist", kt] == "gumbel_r":
            dist_values = scipy.stats.gumbel_r.ppf(cdf_values, loc, scale)

    return dist_values


def plot_kt_kt(std_kt_kt_train, fontsize=11, legend=True, plot_bool=True):
    """
    Plots the kt-RMSE error for each station and fits a polynome to the average error over the stations.

    This function creates a scatter plot of kt-RMSE values across stations and overlays a polynomial fit to the
    average error trend. It optionally displays the legend and the plot.

    :param std_kt_kt_train: DataFrame containing kt-RMSE values for different stations.
    :param fontsize: Font size for plot labels and legend. Default is 11.
    :param legend: Boolean flag to display the legend. Default is True.
    :param plot_bool: Boolean flag to enable plotting. Default is True.

    :return: Numpy array containing the coefficients of the fitted 3rd-degree polynomial.
    """

    # Compute the average distribution over all stations
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        x_mean = std_kt_kt_train.max(axis=1).dropna().index
        y_mean = std_kt_kt_train.mean(axis=1).dropna().values

        params_poly_3, _ = curve_fit(poly_func, x_mean, y_mean)
        x_train = std_kt_kt_train.loc[std_kt_kt_train.sum(axis=1) != 0].index
        y_train = poly_func(x_train, *params_poly_3)
        y_train_ts = pd.Series(y_train, index=x_train) * 1
        errors = std_kt_kt_train.sub(y_train_ts, axis=0).values.flatten()
        # sigma_poly = np.std([er for er in errors if ~np.isnan(er)])

        if plot_bool:
            plt.figure(figsize=(6, 5))
            # markers = ["o", "v", "^", "1", "s", "*", "+"]
            colors = [mpl.cm.get_cmap('cool')(i / len(std_kt_kt_train.columns)) for i in
                      range(len(std_kt_kt_train.columns))]
            for i, col in enumerate(std_kt_kt_train.columns):
                std_kt_kt_train[col].plot(label=col, marker=".", color=colors[i])
            plt.plot(x_mean, y_mean, linewidth=0, marker="o", color="black")
            plt.plot(y_train_ts.index, y_train_ts, linewidth=2.5, color="black",
                     label="Polynomial fit")
            plt.plot(y_train_ts.index, y_train_ts * 1.35, linewidth=2.5, color="grey",
                     label="Polynomial fit +35%")
            # for i, col in enumerate(std_kt_kt_test.columns):
            #     std_kt_kt_test[col].plot(color="blue", marker=markers[i], label=col)
            if legend:
                plt.legend(fontsize=fontsize)
            plt.xlabel("$kt^{ref}$", fontsize=fontsize)
            plt.ylabel("kt-RMSE error", fontsize=fontsize)
            # plt.title(elevation_step)
            plt.tight_layout()
            plt.ylim([0, 0.3])

    return params_poly_3


def collect_quantiles(df_25, df_50, df_75, df_95, quantiles_g, quantiles_d, quantiles_b, insitu_data, filter, station,
                      q_kt, q_dhi, q_bhi, ghi_scns, dhi_scns, bhi_scns,
                      print_bool: bool = True):
    """
    Calculates coverage of prediction intervals and quantile accuracy for GHI, DHI, and BHI components.

    This function assesses how often observed irradiance values fall within different forecast intervals
    (25%, 50%, 75%, and 95%) and computes quantile distribution accuracy. It supports scenario-based
    predictions and can optionally print the summary.

    :param df_25: DataFrame to store 25% interval coverage results.
    :param df_50: DataFrame to store 50% interval coverage results.
    :param df_75: DataFrame to store 75% interval coverage results.
    :param df_95: DataFrame to store 95% interval coverage results.
    :param quantiles_g: Quantiles for GHI.
    :param quantiles_d: Quantiles for DHI.
    :param quantiles_b: Quantiles for BHI.
    :param insitu_data: Ground truth irradiance measurements.
    :param filter: Boolean or index mask to filter the dataset.
    :param station: Name of the station.
    :param q_kt: DataFrame to store quantile validation for GHI.
    :param q_dhi: DataFrame to store quantile validation for DHI.
    :param q_bhi: DataFrame to store quantile validation for BHI.
    :param ghi_scns: Scenario forecast values for GHI.
    :param dhi_scns: Scenario forecast values for DHI.
    :param bhi_scns: Scenario forecast values for BHI.
    :param print_bool: Boolean flag to print results. Default is True.

    :return: Updated DataFrames with interval and quantile validation statistics.
    """
    df_25.loc[station, "ghi"] = ((quantiles_g.loc[filter, 0.375] <= insitu_data["ghi"].loc[filter].clip(lower=0)) &
                                 (quantiles_g.loc[filter, 0.625] >= insitu_data["ghi"].loc[filter])).mean()
    df_25.loc[station, "dhi"] = ((quantiles_d.loc[filter, 0.375] <= insitu_data["dhi"].loc[filter].clip(lower=0)) &
                                 (quantiles_d.loc[filter, 0.625] >= insitu_data["dhi"].loc[filter])).mean()
    df_25.loc[station, "bhi"] = ((quantiles_b.loc[filter, 0.375] <= insitu_data["bhi"].loc[filter].clip(lower=0)) &
                                 (quantiles_b.loc[filter, 0.625] >= insitu_data["bhi"].loc[filter])).mean()

    df_50.loc[station, "ghi"] = ((quantiles_g.loc[filter, 0.25] <= insitu_data["ghi"].loc[filter].clip(lower=0)) &
                                 (quantiles_g.loc[filter, 0.75] >= insitu_data["ghi"].loc[filter])).mean()
    df_50.loc[station, "dhi"] = ((quantiles_d.loc[filter, 0.25] <= insitu_data["dhi"].loc[filter].clip(lower=0)) &
                                 (quantiles_d.loc[filter, 0.75] >= insitu_data["dhi"].loc[filter])).mean()
    df_50.loc[station, "bhi"] = ((quantiles_b.loc[filter, 0.25] <= insitu_data["bhi"].loc[filter].clip(lower=0)) &
                                 (quantiles_b.loc[filter, 0.75] >= insitu_data["bhi"].loc[filter])).mean()
    if print_bool:
        print(df_50.loc[station])

    df_75.loc[station, "ghi"] = ((quantiles_g.loc[filter, 0.125] <= insitu_data["ghi"].loc[filter].clip(lower=0)) &
                                 (quantiles_g.loc[filter, 0.875] >= insitu_data["ghi"].loc[filter])).mean()
    df_75.loc[station, "dhi"] = ((quantiles_d.loc[filter, 0.125] <= insitu_data["dhi"].loc[filter].clip(lower=0)) &
                                 (quantiles_d.loc[filter, 0.875] >= insitu_data["dhi"].loc[filter])).mean()
    df_75.loc[station, "bhi"] = ((quantiles_b.loc[filter, 0.125] <= insitu_data["bhi"].loc[filter].clip(lower=0)) &
                                 (quantiles_b.loc[filter, 0.875] >= insitu_data["bhi"].loc[filter])).mean()
    # print(df_75.loc[station])

    df_95.loc[station, "ghi"] = ((quantiles_g.loc[filter, 0.025] <= insitu_data["ghi"].loc[filter].clip(lower=0)) &
                                 (quantiles_g.loc[filter, 0.975] >= insitu_data["ghi"].loc[filter])).mean()
    df_95.loc[station, "dhi"] = ((quantiles_d.loc[filter, 0.025] <= insitu_data["dhi"].loc[filter].clip(lower=0)) &
                                 (quantiles_d.loc[filter, 0.975] >= insitu_data["dhi"].loc[filter])).mean()
    df_95.loc[station, "bhi"] = ((quantiles_b.loc[filter, 0.025] <= insitu_data["bhi"].loc[filter].clip(lower=0)) &
                                 (quantiles_b.loc[filter, 0.975] >= insitu_data["bhi"].loc[filter])).mean()
    if print_bool:
        print(df_95.loc[station])
    # print(df_95.loc[station])  #

    for q in np.arange(0, 1, 0.05):
        q_kt.loc[q, station] = (
                ghi_scns.loc[filter].quantile(q, axis=1) > insitu_data["ghi"].loc[filter].clip(lower=0)).mean()
        q_kt.loc[q, "y=x"] = q

    for q in np.arange(0, 1, 0.05):
        q_dhi.loc[q, station] = (
                dhi_scns.loc[filter].quantile(q, axis=1) > insitu_data["dhi"].loc[filter].clip(lower=0)).mean()
        q_dhi.loc[q, "y=x"] = q

    for q in np.arange(0, 1, 0.05):
        q_bhi.loc[q, station] = (
                bhi_scns.loc[filter].quantile(q, axis=1) > insitu_data["bhi"].loc[filter].clip(lower=0)).mean()
        q_bhi.loc[q, "y=x"] = q

    return df_25, df_50, df_75, df_95, q_kt, q_dhi, q_bhi


def collect_quantiles_pv_live(station,
                              df_50, df_95,
                              quantiles_g, quantiles_s, quantiles_e, quantiles_w,
                              df_1h_g, df_1h_s, df_1h_e, df_1h_w,
                              print_bool: bool = True):
    """
    Computes the percentage of ground truth values within the 50% and 95% prediction intervals for POA irradiance.

    This function evaluates how often the measured POA irradiance falls within the 50% and 95% predicted
    quantile intervals for each component. Results are stored in the respective DataFrames.

    :param station: Station name identifier.
    :param df_50: DataFrame to store 50% coverage results.
    :param df_95: DataFrame to store 95% coverage results.
    :param quantiles_g: DataFrame of global horizontal irradiance quantile predictions.
    :param quantiles_s: DataFrame of south-facing POA quantile predictions.
    :param quantiles_e: DataFrame of east-facing POA quantile predictions.
    :param quantiles_w: DataFrame of west-facing POA quantile predictions.
    :param df_1h_g: Ground truth global horizontal irradiance measurements.
    :param df_1h_s: Ground truth south-facing POA measurements.
    :param df_1h_e: Ground truth east-facing POA measurements.
    :param df_1h_w: Ground truth west-facing POA measurements.
    :param print_bool: Boolean flag to print results to console. Default is True.

    :return: Updated DataFrames `df_50` and `df_95` with interval coverage statistics.
    """

    df_50.loc[station, "ghi"] = ((quantiles_g.loc[:, 0.25] <= df_1h_g.clip(lower=0)) & \
                                 (quantiles_g.loc[:, 0.75] >= df_1h_g)).mean()
    df_50.loc[station, "s"] = (
            (quantiles_s.loc[:, 0.25] <= df_1h_s.clip(lower=0)) & \
            (quantiles_s.loc[:, 0.75] >= df_1h_s)).mean()

    df_50.loc[station, "e"] = (
            (quantiles_e.loc[:, 0.25] <= df_1h_e.clip(lower=0)) & \
            (quantiles_e.loc[:, 0.75] >= df_1h_e)).mean()

    df_50.loc[station, "w"] = (
            (quantiles_w.loc[:, 0.25] <= df_1h_w.clip(lower=0)) & \
            (quantiles_w.loc[:, 0.75] >= df_1h_w)).mean()

    df_95.loc[station, "ghi"] = ((quantiles_g.loc[:, 0.025] <= df_1h_g.clip(lower=0)) & \
                                 (quantiles_g.loc[:, 0.975] >= df_1h_g)).mean()

    df_95.loc[station, "s"] = (
            (quantiles_s.loc[:, 0.025] <= df_1h_s.clip(lower=0)) & \
            (quantiles_s.loc[:, 0.975] >= df_1h_s)).mean()

    df_95.loc[station, "e"] = (
            (quantiles_e.loc[:, 0.025] <= df_1h_e.clip(lower=0)) & \
            (quantiles_e.loc[:, 0.975] >= df_1h_e)).mean()

    df_95.loc[station, "w"] = (
            (quantiles_w.loc[:, 0.025] <= df_1h_w.clip(lower=0)) & \
            (quantiles_w.loc[:, 0.975] >= df_1h_w)).mean()

    if print_bool:
        print(df_50.loc[station])
        print(df_95.loc[station])

    return df_50, df_95


def bar_poster(df_50, df_95, test_index, poa=False, figsize=(6, 5)):
    """
    Creates a bar chart comparing 50% and 95% confidence interval coverage across stations.

    This function visualizes the reliability of predictive intervals for irradiance values.
    It compares the observed percentage of values falling within 50% and 95% confidence intervals,
    and supports both plane-of-array (POA) and horizontal irradiance components.

    :param df_50: DataFrame with 50% interval coverage statistics.
    :param df_95: DataFrame with 95% interval coverage statistics.
    :param test_index: List of station names or indices to include in the plot.
    :param poa: Boolean flag to indicate if the data is for POA (True) or GHI/DHI/BHI (False). Default is False.
    :param figsize: Tuple indicating the size of the figure. Default is (6, 5).

    :return: The matplotlib Axes object containing the plot.
    """
    blue_poster = (0 / 255, 0 / 255, 255 / 255)
    turquoise_poster = (10 / 255, 221 / 255, 220 / 255)
    purple_poster = (130 / 255, 72 / 255, 148 / 255)

    ghi_50_pcts = df_50.loc[test_index, "ghi"].values * 100
    ghi_95_pcts = (df_95.loc[test_index, "ghi"] - df_50.loc[test_index, "ghi"]).values * 100
    if not poa:
        dhi_50_pcts = df_50.loc[test_index, "dhi"].values * 100
        dhi_95_pcts = (df_95.loc[test_index, "dhi"] - df_50.loc[test_index, "dhi"]).values * 100
        bhi_50_pcts = df_50.loc[test_index, "bhi"].values * 100
        bhi_95_pcts = (df_95.loc[test_index, "bhi"] - df_50.loc[test_index, "bhi"]).values * 100
    else:
        poas_50_pcts = df_50.loc[test_index, "s"].values * 100
        poas_95_pcts = (df_95.loc[test_index, "s"] - df_50.loc[test_index, "s"]).values * 100
        poae_50_pcts = df_50.loc[test_index, "e"].values * 100
        poae_95_pcts = (df_95.loc[test_index, "e"] - df_50.loc[test_index, "e"]).values * 100
        poaw_50_pcts = df_50.loc[test_index, "w"].values * 100
        poaw_95_pcts = (df_95.loc[test_index, "w"] - df_50.loc[test_index, "w"]).values * 100

    genes = test_index

    fig, ax = plt.subplots(figsize=figsize)
    with sns.axes_style("white"):
        sns.set_style("ticks")

        # plot details
        bar_width = 0.15 if not poa else 0.20
        line_width = 1

        if poa:
            poa_s_bar_positions = np.arange(len(ghi_50_pcts))
            poa_e_bar_positions = poa_s_bar_positions + bar_width + 0.01
            poa_w_bar_positions = poa_e_bar_positions + bar_width + 0.01
        else:
            ghi_bar_positions = np.arange(len(ghi_50_pcts))
            dhi_bar_positions = ghi_bar_positions + bar_width + 0.025
            bhi_bar_positions = dhi_bar_positions + bar_width + 0.025

        if not poa:
            # make bar plots
            _ = plt.bar(ghi_bar_positions, ghi_50_pcts, bar_width,
                        color=blue_poster,
                        edgecolor="black",
                        linewidth=line_width,
                        hatch='//',
                        label='GHI 50%-interval')
            _ = plt.bar(ghi_bar_positions, ghi_95_pcts, bar_width,
                        bottom=ghi_50_pcts,
                        color=blue_poster,
                        edgecolor="black",
                        label='GHI 95%-interval')

            _ = plt.bar(dhi_bar_positions, dhi_50_pcts, bar_width,
                        color=turquoise_poster,
                        edgecolor="black",
                        linewidth=line_width,
                        hatch='//',
                        label='DHI 50%-interval')
            _ = plt.bar(dhi_bar_positions, dhi_95_pcts, bar_width,
                        bottom=dhi_50_pcts,
                        color=turquoise_poster,
                        edgecolor="black",
                        label='DHI 95%-interval')
            _ = plt.bar(bhi_bar_positions, bhi_50_pcts, bar_width,
                        color=purple_poster,
                        edgecolor="black",
                        linewidth=line_width,
                        hatch='//',
                        label='BHI 50%-interval')
            _ = plt.bar(bhi_bar_positions, bhi_95_pcts, bar_width,
                        bottom=bhi_50_pcts,
                        color=purple_poster,
                        edgecolor="black",
                        label='BHI 95%-interval')

        if poa:
            _ = plt.bar(poa_s_bar_positions, poas_50_pcts, bar_width,
                        color="seagreen",
                        edgecolor="black",
                        linewidth=line_width,
                        hatch='//',
                        label='POA-south 50%-interval')
            _ = plt.bar(poa_s_bar_positions, poas_95_pcts, bar_width,
                        bottom=poas_50_pcts,
                        color="seagreen",
                        edgecolor="black",
                        label='POA-south 95%-interval')
            _ = plt.bar(poa_e_bar_positions, poae_50_pcts, bar_width,
                        color="darkseagreen",
                        edgecolor="black",
                        linewidth=line_width,
                        hatch='//',
                        label='POA-east 50%-interval')
            _ = plt.bar(poa_e_bar_positions, poae_95_pcts, bar_width,
                        bottom=poae_50_pcts,
                        color="darkseagreen",
                        edgecolor="black",
                        label='POA-east 95%-interval')
            _ = plt.bar(poa_w_bar_positions, poaw_50_pcts, bar_width,
                        color="yellowgreen",
                        edgecolor="black",
                        linewidth=line_width,
                        hatch='//',
                        label='POA-west 50%-interval')
            _ = plt.bar(poa_w_bar_positions, poaw_95_pcts, bar_width,
                        bottom=poaw_50_pcts,
                        color="yellowgreen",
                        edgecolor="black",
                        label='POA-west 95%-interval')

        plt.yticks(fontsize=12)
        plt.ylabel('Confidence probabilities', fontsize=12)
        if poa:
            plt.xticks(poa_e_bar_positions, genes, fontsize=12)
            leg = plt.legend(loc='lower right', fontsize=9)
            _ = leg.get_frame().set_alpha(1)
            plt.xlim([-1, 41])
        else:
            plt.xticks(dhi_bar_positions, genes, fontsize=12)
            plt.legend(loc='best', fontsize=10, bbox_to_anchor=(1.0, 1.05))

        xmin, xmax = ax.get_xlim()
        plt.hlines(y=95, xmin=xmin, xmax=xmax, color="black")
        plt.hlines(y=50, xmin=xmin, xmax=xmax, color="black", linestyle="dashed")

        plt.ylim([40, 105])
        sns.despine()
        plt.tight_layout()

    return ax


if __name__ == "__main__":

    t = np.linspace(0, 100, 100)
    data = pd.DataFrame(index=t, columns=range(0, 1000))

    for n in data.columns:
        data[n] = 5 + np.sin(t / 10) + 1 * np.random.randn(len(t))

    ax = q_plot(data)
