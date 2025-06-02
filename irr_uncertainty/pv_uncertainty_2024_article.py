"""This module enables to recreate the figures of the article"""
# Created by A. MATHIEU at 22/10/2024
import numpy as np
import os
import pandas as pd
import seaborn as sns
import scipy
import matplotlib.pyplot as plt
import geopandas as gpd

from global_land_mask import globe
from geopandas import GeoDataFrame
from shapely import Polygon
from shapely.geometry import Point
from tqdm import tqdm

from irr_uncertainty.config import DATA_PATH, Config
from irr_uncertainty.data.solar_data import stations_pv_live, pvlive_lat_long_alt, bsrn_lat_long_alt, bsrn_name, stations_bsrn
from irr_uncertainty.data.irr_data import ghi_dhi_bhi_pvgis_2015, load_bsrn_data, load_pvlive_data
from irr_uncertainty.models.optic_model import erbs_simple
from irr_uncertainty.models.uncertainty_config import euro_stations
from irr_uncertainty.models.uncertainty_model import get_kd_dist_v2, irrh_scenarios, transpo_scenarios
from irr_uncertainty.utils import blue, q_plot, collect_quantiles, collect_quantiles_pv_live, bar_poster

irr_folder = DATA_PATH / "irr_data"
image_folder = DATA_PATH / "irr_data" / "images"


# Arbitrary selected based on missing data
YEARS = {"bud": [2020, 2021, 2022],
         "cab": list(range(2005, 2023)),
         "cam": [2005, 2007, 2009, 2013, 2014],
         "car": list(range(2005, 2011)) + (list(range(2012, 2019))),
         "cnr": list(range(2011, 2015)) + (list(range(2016, 2023))),
         "lin": list(range(2006, 2023)),
         "pal": list(range(2008, 2012)) + (list(range(2013, 2023))),
         "pay": [2009] + (list(range(2013, 2023))),
         "tor": list(range(2006, 2022)),
         }

START_BSRN = pd.to_datetime("20050101").tz_localize("CET")
END_BSRN = pd.to_datetime("20230101").tz_localize("CET")

if __name__ == "__main__":

    plot_bool = False
    user, password = Config().bsrn()

    # Seperate the BSRN dataset into train and test set
    train_index = ['bud', 'cam', 'car', 'lin', 'pal', 'pay']
    test_index = ['cab', 'cnr', 'tor']

    ############## BSRN + PV-live MAP ##############
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    world = gpd.read_file("https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_admin_0_countries.geojson")
    df = GeoDataFrame(columns=["lat", "long", "ghi", "dhi", "geometry"])
    i = 0
    step = 0.25
    for lat in tqdm(np.arange(35, 65, step)):
        for long in np.arange(-15, 40, step):
            if globe.is_land(lat, long):
                try:
                    [ghi, bhi, dhi] = ghi_dhi_bhi_pvgis_2015(lat, long)
                except:
                    [ghi, bhi, dhi] = [np.nan, np.nan, np.nan]
                df.loc[i, "lat"] = lat
                df.loc[i, "long"] = long
                df.loc[i, "ghi"] = ghi / 1000
                df.loc[i, "dhi"] = dhi / 1000
                coords = ((long - step / 2, lat - step / 2), (long - step / 2, lat + step / 2),
                          (long + step / 2, lat + step / 2), (long + step / 2, lat - step / 2),
                          (long - step / 2, lat - step / 2))
                df.loc[i, "geometry"] = Polygon(coords)
                i += 1

    pvlive_all = stations_pv_live()
    bsrn_all = stations_bsrn()
    geometry = [Point(xy) for xy in zip(bsrn_all.loc[train_index, 'long'], bsrn_all.loc[train_index, 'lat'])]
    gdf = GeoDataFrame(bsrn_all.loc[train_index], geometry=geometry)
    geometry_3 = [Point(xy) for xy in zip(bsrn_all.loc[test_index, 'long'], bsrn_all.loc[test_index, 'lat'])]
    gdf_3 = GeoDataFrame(bsrn_all.loc[test_index], geometry=geometry_3)

    pv_live_geometry = [Point(xy) for xy in zip(pvlive_all['Longitude'], pvlive_all['Latitude'])]
    pv_live_gdf = GeoDataFrame(pvlive_all, geometry=pv_live_geometry)

    if plot_bool:
        df["ghi"] = df["ghi"].astype(float)
        ax = df.plot(figsize=(6.5, 4.5),
                     column="ghi",
                     cmap="cool",
                     legend=True,
                     legend_kwds={
                         "location": "bottom",
                         "shrink": .6
                     }
                     )
        world.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1, alpha=0.1)
        ax = gdf.plot(ax=ax, marker='o', color="red", markersize=45, edgecolor="white", linewidth=0.5)
        ax = gdf_3.plot(ax=ax, marker='o', color="blue", markersize=45, edgecolor="white", linewidth=0.5)
        ax = pv_live_gdf.plot(ax=ax, marker='o', color="purple", markersize=15, edgecolor="white", linewidth=0.2)
        plt.ylim([30, 65])
        plt.xlim([-20, 40])
        plt.tight_layout()
        plt.title("2015 PVGIS-ERA5 GHI irradiation [kWh]", fontsize=12)
        plt.xlim([-20, 40])
        plt.ylim([35, 65])
        plt.tight_layout()
        plt.savefig(image_folder / "bsrn_pvlive_cities_ghi_2015.png")

        df["kd"] = df["dhi"].astype(float) / df["ghi"].astype(float)
        ax = df.plot(figsize=(6.5, 4.5),
                     column="kd",
                     cmap="spring",
                     legend=True,
                     legend_kwds={
                         "location": "bottom",
                         "shrink": .6
                     }
                     )
        world.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1, alpha=0.1)
        ax = gdf.plot(ax=ax, marker='o', color="red", markersize=45, edgecolor="white", linewidth=0.5)
        ax = gdf_3.plot(ax=ax, marker='o', color="blue", markersize=45, edgecolor="white", linewidth=0.5)
        ax = pv_live_gdf.plot(ax=ax, marker='o', color="purple", markersize=15, edgecolor="white", linewidth=0.2)
        plt.ylim([30, 65])
        plt.xlim([-20, 40])
        plt.tight_layout()
        plt.title("2015 PVGIS-ERA5 diffuse fraction [-]", fontsize=13)
        plt.xlim([-20, 40])
        plt.ylim([35, 65])
        plt.tight_layout()
        plt.savefig(image_folder / "bsrn_pvlive_cities_kd_2015.png")

    ############## Calculate global error metrics ##############
    meta_data = pd.DataFrame()
    error_m = pd.DataFrame(columns=["ghi", "dhi", "bhi", "dni", "kd", "kt"], index=euro_stations, dtype=float)
    mean_helio = error_m.copy()
    error_mp = error_m.copy()
    error_std = error_m.copy()
    error_rmse = error_m.copy()
    error_stdp = error_m.copy()
    error_p_autocorr = error_m.copy()

    step_kt = 0.05
    step_kd = 0.05
    kt_range = np.arange(0, 1, step_kt).round(2)
    kd_range = np.arange(0, 1, step_kd).round(2)
    kt_moy = pd.Series(dtype=float)

    # If not-predownloaded, it takes approximately 1h-1h30 to download BSRN data
    for station in tqdm(euro_stations):
        lat, lon, alt = bsrn_lat_long_alt(station)
        sat_data, insitu_data, solar_position = load_bsrn_data(START_BSRN, END_BSRN, station, user, password)
        filter = (insitu_data["ghi"] > 0) & (sat_data["ghi"] > 0) & (np.isin(insitu_data.index.year, YEARS[station]))

        # Collect meta data
        meta_data.loc[station, "city"] = bsrn_name(station)
        meta_data.loc[station, ["lat", "long", "alt"]] = lat, lon, alt
        meta_data.loc[station, ["years", "#"]] = str(YEARS[station]), len(filter[filter])

        for col in ["ghi", "dhi", "bhi", "dni", "kd", "kt"]:
            error = (insitu_data[col].tz_convert("CET") - sat_data[col].tz_convert("CET")).loc[filter].astype(float)

            mean_helio.loc[station, col] = sat_data.loc[filter, col].mean()
            error_m.loc[station, col] = error.mean()
            error_mp.loc[station, col] = error.mean() / sat_data.loc[filter, col].mean()
            error_std.loc[station, col] = error.std(ddof=0)
            error_rmse.loc[station, col] = ((error ** 2).mean()) ** (1 / 2)
            error_stdp.loc[station, col] = error.std(ddof=0) / sat_data.loc[filter, col].mean()
            error_p_autocorr.loc[station, col] = error.autocorr()

    if plot_bool:
        print("Error metrics")
        print((error_m.loc[train_index, :] ** 2).mean() ** (1 / 2))
        print(error_m[["kd", "kt"]].round(3))
        print(error_p_autocorr[["kd", "kt"]].round(3))
        print(error_p_autocorr.loc[train_index].mean().round(2))

        error_m.to_pickle(DATA_PATH / "irr_data" / "error_m.pkl")
        error_stdp.to_pickle(DATA_PATH / "irr_data" / "error_stdp.pkl")

    ############## Calculate kt-error as function of kt ##############
    std_kt_kt_less15, std_kt_kt_over15 = calculate_kt_kpis(euro_stations, START_BSRN, END_BSRN, user, password,
                                                           sat_source="cams_pvlib")

    # get paramaters under and over 15 degrees
    params_kt_less15 = plot_kt_kt(std_kt_kt_less15.loc[:, train_index], plot_bool=False)
    params_kt_over15 = plot_kt_kt(std_kt_kt_over15.loc[:, train_index], plot_bool=False)

    if plot_bool:
        # Seperate into training and test datasets
        std_kt_kt_train = std_kt_kt_less15.loc[:, train_index]
        std_kt_kt_test = std_kt_kt_less15.loc[:, test_index]

        params = plot_kt_kt(std_kt_kt_train, 13)
        print(np.array(params).round(4))
        plt.savefig(image_folder / "kt_kt_less15.png")

        std_kt_kt_train = std_kt_kt_over15.loc[:, train_index]
        params = plot_kt_kt(std_kt_kt_train, 13)
        print(np.array(params).round(4))
        plt.savefig(image_folder / "kt_kt_over15.png")

    ##############  Calibration-Validation kt ##############
    n_scenarios = 1000
    df_95 = pd.DataFrame(dtype=float, columns=["ghi", "dhi", "bhi"])
    df_75 = pd.DataFrame(dtype=float, columns=["ghi", "dhi", "bhi"])
    df_50 = pd.DataFrame(dtype=float, columns=["ghi", "dhi", "bhi"])
    df_25 = pd.DataFrame(dtype=float, columns=["ghi", "dhi", "bhi"])
    q_kt = pd.DataFrame(dtype=float)
    q_dhi = pd.DataFrame(dtype=float)
    q_bhi = pd.DataFrame(dtype=float)
    for station in train_index + test_index:
        print(station)
        sat_data, insitu_data, solar_position = load_bsrn_data(START_BSRN, END_BSRN, station, user, password)
        lat, long, alt = bsrn_lat_long_alt(station)
        filter = (insitu_data["ghi"] > 0) & (sat_data["ghi"] > 0) & (np.isin(insitu_data.index.year, YEARS[station]))

        sat_data = sat_data.loc[filter[filter].index[0]:filter[filter].index[-1]]
        insitu_data = insitu_data.loc[filter[filter].index[0]: filter[filter].index[-1]]
        solar_position = solar_position.loc[filter[filter].index[0]:filter[filter].index[-1]]

        ghi_scns, dhi_scns, bhi_scns = irrh_scenarios(lat, long, alt,
                                                         solar_position, sat_data["ghi"],
                                                         factor_kt=1.3,
                                                         factor_kd=1.3,
                                                         n_scenarios=n_scenarios)

        quantiles_g = ghi_scns.loc[filter].quantile([0.025, 0.125, 0.25, 0.375, 0.625, 0.75, 0.875, 0.975], axis=1).T
        quantiles_b = bhi_scns.loc[filter].quantile([0.025, 0.125, 0.25, 0.375, 0.625, 0.75, 0.875, 0.975], axis=1).T
        quantiles_d = dhi_scns.loc[filter].quantile([0.025, 0.125, 0.25, 0.375, 0.625, 0.75, 0.875, 0.975], axis=1).T

        df_25, df_50, df_75, df_95, q_kt, q_dhi, q_bhi = \
            collect_quantiles(df_25, df_50, df_75, df_95, quantiles_g, quantiles_d, quantiles_b,
                              insitu_data, filter, station, q_kt, q_dhi, q_bhi, ghi_scns, dhi_scns, bhi_scns)

    if plot_bool:
        _ = bar_poster(df_50, df_95, test_index)
        plt.legend(fontsize=9.5, bbox_to_anchor=(1.0, 1.05))
        plt.savefig(image_folder / "irrh_validation.png")

        (df_95 * 100).round(1).to_csv(image_folder / "gh_95_validation.csv")
        (df_50 * 100).round(1).to_csv(image_folder / "gh_50_validation.csv")

        # qqplot
        fig, axes = plt.subplots(1, 3, figsize=(9, 5))

        colors_train = ["darkred", "lightcoral", "salmon", "chocolate", "peru", "orange"]
        colors_test = ["deepskyblue", "dodgerblue", "navy"]
        axes[0].set_title("GHI q-q plot")
        axes[0].plot(np.arange(0, 1, 0.01), np.arange(0, 1, 0.01), color="black", label="y=x")
        q_kt.loc[:, train_index].plot(color=colors_train, ax=axes[0], alpha=0.4)
        q_kt.loc[:, test_index].plot(color=colors_test, ax=axes[0], marker=".")
        axes[0].legend()
        axes[1].set_title("DHI q-q plot")
        axes[1].plot(np.arange(0, 1, 0.01), np.arange(0, 1, 0.01), color="black")
        q_dhi.loc[:, train_index].plot(color=colors_train, ax=axes[1], alpha=0.4)
        q_dhi.loc[:, test_index].plot(color=colors_test, ax=axes[1], marker=".")
        axes[1].legend([])
        axes[2].set_title("BHI q-q plot")
        axes[2].plot(np.arange(0, 1, 0.01), np.arange(0, 1, 0.01), color="black", label="y=x")
        q_bhi.loc[:, train_index].plot(color=colors_train, ax=axes[2], alpha=0.4)
        q_bhi.loc[:, test_index].plot(color=colors_test, ax=axes[2], marker=".")
        axes[2].legend([])

        plt.tight_layout()
        plt.savefig(image_folder / "qq_h_validation.png")

    ############## kt vs kd: error illustration ##############
    user, password = Config().bsrn()
    station = "bud"  # BSRN station

    # Get kt/kd data when ghi>0
    sat_data, insitu_data, solar_position = load_bsrn_data(START_BSRN, END_BSRN, station, user, password,
                                                           sat_source="cams_pvlib")
    filter = (insitu_data["ghi"] > 0) & (sat_data["ghi"] > 0) & (np.isin(insitu_data.index.year, YEARS[station]))

    insitu_data = insitu_data.loc[filter]
    sat_data = sat_data.loc[filter]
    solar_position = solar_position.loc[filter]

    # Prep data
    insitu_data["$kt^{ref}$"] = sat_data["kt"]
    insitu_data["kd"] = insitu_data["kd"].clip(upper=1)  # Over 1 is not realistic

    insitu_data = insitu_data.copy()

    ## Compute the quantiles per 5% interval
    # Round values to make intervals
    insitu_data["kt_sat"] = (insitu_data["$kt^{ref}$"].astype(float) * 20).round(0) / 20
    q05 = insitu_data.pivot_table(index="kt_sat", values="kd", aggfunc=lambda x: np.quantile(x, 0.05))["kd"]
    q95 = insitu_data.pivot_table(index="kt_sat", values="kd", aggfunc=lambda x: np.quantile(x, 0.95))["kd"]
    q75 = insitu_data.pivot_table(index="kt_sat", values="kd", aggfunc=lambda x: np.quantile(x, 0.75))["kd"]
    q25 = insitu_data.pivot_table(index="kt_sat", values="kd", aggfunc=lambda x: np.quantile(x, 0.25))["kd"]

    if plot_bool:
        _ = plt.figure(figsize=(8, 5))
        # Scatter plot
        ax = sns.scatterplot(data=insitu_data, x="$kt^{ref}$", y="kd", color="navy", alpha=0.035,
                             label=f'In-situ measurements, BSRN "{station}"')

        # Erbs model curve
        kt_erbs = np.linspace(0, 1, 100)
        kd_erbs = erbs_simple(kt_erbs)
        plt.plot(kt_erbs, kd_erbs, color="deepskyblue", linewidth=2.5, label='Erbs model')

        # Quantile intervals in grey
        plt.fill_between(q05.index, q05, q95, color="grey", alpha=0.25, label="90% interval")
        plt.fill_between(q25.index, q25, q75, color="grey", alpha=0.50, label="50% interval")

        plt.ylabel("$kd$")
        plt.xlabel("$kt^{ref}$")
        plt.xlim([0.05, 0.9])
        plt.legend()

        leg = ax.get_legend()
        leg.legendHandles[1].set_alpha(0.5)
        plt.tight_layout()
        plt.savefig(image_folder / f"{station}_all_quantiles.png")

    ############## Illustration kd error as function of kt bin ##############
    kd_dist = get_kd_dist_v2(train_index=train_index, plot_bool=False, legend=False)

    if plot_bool:
        fig = plt.subplots(figsize=(8, 5))
    x = np.arange(-0.3, 0.3, 0.001)
    pal = sns.color_palette("cool", len(kd_dist.columns))
    df = pd.DataFrame()
    for i, col in enumerate(kd_dist):
        print(col)
        if type(kd_dist.loc["dist", col]) == str:
            if kd_dist.loc["dist", col] == "norm":
                y = scipy.stats.norm.pdf(x, kd_dist.loc["loc", col], kd_dist.loc["scale", col])
                if plot_bool:
                    plt.plot(x, y, linewidth=2, color=pal[i], label=str(round(col, 2)))
                samples = scipy.stats.norm.rvs(kd_dist.loc["loc", col], kd_dist.loc["scale", col], 1000 * 1000 * 10)
            if kd_dist.loc["dist", col] == "gumbel_l":
                y = scipy.stats.gumbel_l.pdf(x, kd_dist.loc["loc", col], kd_dist.loc["scale", col])
                if plot_bool:
                    plt.plot(x, y, linewidth=2, color=pal[i], label=str(round(col, 2)))
                samples = scipy.stats.gumbel_l.rvs(kd_dist.loc["loc", col], kd_dist.loc["scale", col],
                                                   1000 * 1000 * 10)
            if kd_dist.loc["dist", col] == "gumbel_r":
                y = scipy.stats.gumbel_r.pdf(x, kd_dist.loc["loc", col], kd_dist.loc["scale", col])
                if plot_bool:
                    plt.plot(x, y, linewidth=2, color=pal[i], label=str(round(col, 2)))
                samples = scipy.stats.gumbel_r.rvs(kd_dist.loc["loc", col], kd_dist.loc["scale", col],
                                                   1000 * 1000 * 10)
            df.loc["distribution", col] = kd_dist.loc["dist", col]
            df.loc["avg", col] = round(samples.mean(), 4)
            df.loc["std", col] = round(samples.std(), 4)
            df.loc["skew", col] = round(pd.Series(samples).skew(), 4)
            df.loc["loc", col], df.loc["scale", col] = round(kd_dist.loc["loc", col], 4), round(
                kd_dist.loc["scale", col], 4)

    if plot_bool:
        df.to_csv(image_folder / "distribution_info.csv")

    ############## GHI/BHI/DHI illustration ##############
    user, password = Config().bsrn()
    station = "pal"
    start_2 = pd.to_datetime("20220812").tz_localize("CET")
    end_2 = pd.to_datetime("20220816").tz_localize("CET")
    sat_data, insitu_data, solar_position = load_bsrn_data(start, end, station, user, password)
    sat_data = sat_data.loc[start_2: end_2].copy()
    insitu_data = insitu_data.loc[start_2: end_2].copy()
    solar_position = solar_position.loc[start_2: end_2].copy()

    n_scenarios = 1000
    lat, long, alt = bsrn_lat_long_alt(station)
    ghi_scns, dhi_scns, bhi_scns = irrh_scenarios(lat, long, alt,
                                                     solar_position, sat_data["ghi"],
                                                     factor_kt=1.35,
                                                     factor_kd=1.3,
                                                     n_scenarios=n_scenarios)
    if plot_bool:
        # GHI, BHI, DHI, POAgrd
        quantiles = [0.5, 0.95]
        fig, axes = plt.subplots(3, 1, figsize=(8, 6), sharex=True)

        # GHI
        axes[0].plot(insitu_data.loc[:, "ghi"].index, insitu_data.loc[:, "ghi"], color="black", marker=".",
                     label=f"In-situ BSRN '{station}' GHI", linewidth=1)
        axes[0] = q_plot(ghi_scns.loc[:], quantiles=quantiles, color=blue, ax=axes[0], label="GHI", tweak=True)
        axes[0].set_ylabel("GHI [W/m²]", color="black")
        axes[0].set_ylim([-50, 1400])
        axes[0].get_xaxis().set_ticks([])
        axes[0].get_yaxis().set_ticks([0, 500, 1000])

        # Beam
        axes[1].plot(insitu_data.loc[:, "bhi"].index, insitu_data.loc[:, "bhi"], color="black", marker=".",
                     label="In-situ BSRN BHI", linewidth=1)
        axes[1] = q_plot(bhi_scns.loc[:], quantiles=quantiles, color="purple", ax=axes[1], label="BHI", tweak=True)
        # leg = axes[1].legend()
        # leg.get_frame().set_alpha(0.3)
        axes[1].set_ylabel("BHI [W/m²]", color="black")
        axes[1].set_ylim([-50, 1400])
        axes[1].get_xaxis().set_ticks([])
        axes[1].get_yaxis().set_ticks([0, 500, 1000])

        # Diffuse
        axes[2].plot(insitu_data.loc[:, "dhi"].index, insitu_data.loc[:, "dhi"], color="black", marker=".",
                     label="In-situ BSRN DHI", linewidth=1)
        axes[2] = q_plot(dhi_scns.loc[:], quantiles=quantiles, color="teal", ax=axes[2], label="DHI", tweak=True)

        # leg = axes[2].legend()
        # leg.get_frame().set_alpha(0.3)
        axes[2].set_ylabel("DHI [W/m²]", color="black")
        axes[2].set_ylim([-50, 1400])
        axes[2].get_xaxis().set_ticks([])
        axes[2].get_yaxis().set_ticks([0, 500, 1000])

        plt.tight_layout()
        plt.savefig(image_folder / f"{station}_all_quantiles.png")

    ############## PV-live verification ##############
    pvlive_stations = stations_pv_live()

    factor_kt = 1.35
    factor_kd = 1.3
    kt_mu = 0.0104
    n_scenarios = 1000
    tilt = 25

    n_data = pd.Series(dtype=float)

    if os.path.exists(irr_folder / "df_50_poa.pkl"):
        df_50 = pd.read_pickle(irr_folder / "df_50_poa.pkl")
        df_95 = pd.read_pickle(irr_folder / "df_95_poa.pkl")
    else:
        df_50 = pd.DataFrame(index=pvlive_stations.index, columns=['ghi', 's', 'e', 'w'])
        df_95 = pd.DataFrame(index=pvlive_stations.index, columns=['ghi', 's', 'e', 'w'])

    pvlive_stations_left = df_50[~df_50.index.isin(df_50.dropna().index)].index
    print(pvlive_stations_left)

    for station in list(pvlive_stations_left):
        print(station)
        lat, long, alt = pvlive_lat_long_alt(station)
        sat_data, insitu_h, insitu_s, insitu_e, insitu_w, solar_position = load_pvlive_data(station=station,
                                                                                            sat_source="cams_pvlib")

        # Generate Monte Carlo simulations
        ghi_scns, dhi_scns, bhi_scns = irrh_scenarios(lat, long, alt,
                                                         solar_position, sat_data["ghi"],
                                                         factor_kt=factor_kt,
                                                         factor_kd=factor_kd,
                                                         kt_mu=kt_mu,
                                                         params_kt_less15=params_kt_less15,
                                                         params_kt_over15=params_kt_over15,
                                                         sat_source="cams_pvlib",
                                                         n_scenarios=n_scenarios)

        poa_scns_s, _, _, _ = \
            transpo_scenarios(tilt, 180, lat, long, alt, solar_position, ghi_scns, dhi_scns, n_scenarios=n_scenarios)
        poa_scns_e, _, _, _ = \
            transpo_scenarios(tilt, 90, lat, long, alt, solar_position, ghi_scns, dhi_scns, n_scenarios=n_scenarios)

        poa_scns_w, _, _, _ = \
            transpo_scenarios(tilt, 270, lat, long, alt, solar_position, ghi_scns, dhi_scns, n_scenarios=n_scenarios)

        filter = (sat_data["ghi"] > 0) & (insitu_h["Gg_pyr"].reindex(sat_data.index).fillna(0) > 0)
        filter_s = (sat_data["ghi"] > 0) & (insitu_s["Gg_pyr"].reindex(sat_data.index).fillna(0) > 0)
        filter_e = (sat_data["ghi"] > 0) & (insitu_e["Gg_pyr"].reindex(sat_data.index).fillna(0) > 0)
        filter_w = (sat_data["ghi"] > 0) & (insitu_w["Gg_pyr"].reindex(sat_data.index).fillna(0) > 0)

        quantiles_g = ghi_scns.quantile([0.025, 0.25, 0.5, 0.75, 0.975], axis=1).T.loc[filter]
        quantiles_s = poa_scns_s.quantile([0.025, 0.25, 0.75, 0.975], axis=1).T.loc[filter_s]
        quantiles_e = poa_scns_e.quantile([0.025, 0.25, 0.75, 0.975], axis=1).T.loc[filter_e]
        quantiles_w = poa_scns_w.quantile([0.025, 0.25, 0.5, 0.75, 0.975], axis=1).T.loc[filter_w]

        df_50, df_95 = collect_quantiles_pv_live(station, df_50, df_95,
                                                 quantiles_g, quantiles_s, quantiles_e, quantiles_w,
                                                 insitu_h["Gg_pyr"].loc[filter],
                                                 insitu_s["Gg_si_south"].loc[filter_s],
                                                 insitu_e["Gg_si_east"].loc[filter_e],
                                                 insitu_w["Gg_si_west"].loc[filter_w])

        df_50.to_pickle(irr_folder / "df_50_poa.pkl")
        df_95.to_pickle(irr_folder / "df_95_poa.pkl")

    df_50 = pd.read_pickle(irr_folder / "df_50_poa.pkl")
    df_95 = pd.read_pickle(irr_folder / "df_95_poa.pkl")
    if plot_bool:
        _ = bar_poster(df_50, df_95, df_95.index, poa=True)
        plt.tight_layout()
        plt.savefig(image_folder / "poa_validation.png")

    ############## Illustration POA ##############
    tilt = 25
    station = 1
    start = pd.to_datetime("20220622").tz_localize("CET")
    end = pd.to_datetime("20220626").tz_localize("CET")

    lat, long, alt = pvlive_lat_long_alt(station)
    sat_data, insitu_h, insitu_s, insitu_e, insitu_w, solar_position = load_pvlive_data(station=station, start=start,
                                                                                        end=end)

    # Generate Monte Carlo simulations
    ghi_scns, dhi_scns, bhi_scns = irrh_scenarios(lat, long, alt,
                                                     solar_position, sat_data["ghi"],
                                                     factor_kt=factor_kt,
                                                     factor_kd=factor_kd,
                                                     kt_mu=kt_mu,
                                                     params_kt_less15=params_kt_less15,
                                                     params_kt_over15=params_kt_over15,
                                                     sat_source="cams_pvlib",
                                                     n_scenarios=n_scenarios)

    poa_scns_s, _, _, _ = \
        transpo_scenarios(tilt, 180, lat, long, alt, solar_position, ghi_scns, dhi_scns, n_scenarios=n_scenarios)
    poa_scns_e, _, _, _ = \
        transpo_scenarios(tilt, 90, lat, long, alt, solar_position, ghi_scns, dhi_scns, n_scenarios=n_scenarios)

    poa_scns_w, _, _, _ = \
        transpo_scenarios(tilt, 270, lat, long, alt, solar_position, ghi_scns, dhi_scns, n_scenarios=n_scenarios)

    if plot_bool:
        # GHI, POAgrd
        quantiles = [0.5, 0.95]
        fig, axes = plt.subplots(4, 1, figsize=(8, 8), sharex=True, sharey=True)

        # GHI
        h_plot = insitu_h.loc[:, "Gg_pyr"].reindex(ghi_scns.index)
        h_plot.loc[sat_data["Gh_w.m2"] <= 0] = np.nan
        axes[0].plot(h_plot.index, h_plot, color="black", marker=".", label=f"In-situ PV-live station '{station}' GHI",
                     linewidth=1)
        axes[0] = q_plot(ghi_scns.loc[:], quantiles=quantiles, color=blue, ax=axes[0], label="GHI", tweak=True)

        axes[0].set_ylabel("GHI [W/m²]", color="black")
        axes[0].set_ylim([-50, 1400])
        axes[0].get_yaxis().set_ticks([0, 500, 1000])

        # POA-s
        s_plot = insitu_h.loc[:, "Gg_si_south"].reindex(ghi_scns.index)
        s_plot.loc[sat_data["Gh_w.m2"] <= 0] = np.nan
        axes[1].plot(s_plot.index, s_plot, color="black", marker=".",
                     label=f"In-situ PV-live station '{station}' POA south", linewidth=1)
        axes[1] = q_plot(poa_scns_s.loc[:], quantiles=quantiles, color="seagreen", ax=axes[1], label="POA-south",
                         tweak=True)
        axes[1].set_ylabel("POA (25° south) [W/m²]", color="black")

        # POA-e
        e_plot = insitu_e.loc[:, "Gg_si_east"].reindex(ghi_scns.index)
        e_plot.loc[sat_data["Gh_w.m2"] <= 0] = np.nan
        axes[2].plot(e_plot.index, e_plot, color="black", marker=".",
                     label=f"In-situ PV-live station '{station}' POA east", linewidth=1)
        axes[2] = q_plot(poa_scns_e.loc[:], quantiles=quantiles, color="darkseagreen", ax=axes[2], label="POA-east",
                         tweak=True)
        axes[2].set_ylabel("POA (25° east) [W/m²]", color="black")

        # POA-w
        w_plot = insitu_w.loc[:, "Gg_si_west"].reindex(ghi_scns.index)
        w_plot.loc[sat_data["Gh_w.m2"] <= 0] = np.nan
        axes[3].plot(w_plot.index, w_plot, color="black", marker=".",
                     label=f"In-situ PV-live station '{station}' POA west", linewidth=1)
        axes[3] = q_plot(poa_scns_w.loc[:], quantiles=quantiles, color="forestgreen", ax=axes[3], label="POA-west",
                         tweak=True)
        axes[3].set_ylabel("POA (25° west) [W/m²]", color="black")

        plt.tight_layout()
        plt.savefig(image_folder / f"station_{station}_all_quantiles.png")


