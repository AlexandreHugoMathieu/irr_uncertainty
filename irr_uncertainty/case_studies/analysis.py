"""This module analyze CAMS error on BSRN stations"""
# Created by A. MATHIEU at 09/05/2026
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
from irr_uncertainty.data.station_metadata import stations_pv_live, pvlive_lat_long_alt, bsrn_lat_long_alt, bsrn_name, stations_bsrn
from irr_uncertainty.data.irr_data import ghi_dhi_bhi_pvgis_2015, load_bsrn_data, load_pvlive_data
from irr_uncertainty.models.optic_model import erbs_simple
from irr_uncertainty.models.uncertainty_config import euro_stations, YEARS
from irr_uncertainty.models.uncertainty_model import irrh_scenarios_v2
from irr_uncertainty.utils import  plot_kt_kt,  calculate_kt_kpis


if __name__ == "__main__":

    plot_bool = False
    user, password = Config().bsrn()

    # Separate the BSRN dataset into train and test set
    train_index = ['bud', 'cam', 'car', 'lin', 'pal', 'pay']
    test_index = ['cab', 'cnr', 'tor']

    ############## BSRN + PV-live MAP ##############
    world = gpd.read_file("https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_admin_0_countries.geojson")

    df = pd.DataFrame(columns=["lat", "long", "ghi", "dhi", "geometry"])
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