"""This module gives an overview of the BSRN and PV-live stations"""
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd

from global_land_mask import globe
from geopandas import GeoDataFrame
from shapely import Polygon
from shapely.geometry import Point
from tqdm import tqdm

from irr_uncertainty.config import DATA_PATH, Config
from irr_uncertainty.data.station_metadata import stations_pv_live, bsrn_lat_long_alt, bsrn_name, stations_bsrn
from irr_uncertainty.data.irr_data import ghi_dhi_bhi_pvgis_2015, load_bsrn_data
from irr_uncertainty.models.uncertainty_config import euro_stations, YEARS, START_BSRN, END_BSRN
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



