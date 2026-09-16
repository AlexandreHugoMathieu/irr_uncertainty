"""This module analyze CAMS error on BSRN stations"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm

from irr_uncertainty.config import DATA_PATH, Config
from irr_uncertainty.data.station_metadata import bsrn_lat_long_alt, bsrn_name
from irr_uncertainty.data.irr_data import load_bsrn_data
from irr_uncertainty.models.uncertainty_config import euro_stations, YEARS, START_BSRN, END_BSRN
from irr_uncertainty.models.uncertainty_model import irrh_scenarios_v2

from irr_uncertainty.utils import calculate_kt_kpis

if __name__ == "__main__":
    plot_bool = True
    user, password = Config().bsrn()

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

    # If not-predownloaded, it takes approximately 1h30-2h00 to download BSRN data
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
        print((error_m.loc[:] ** 2).mean() ** (1 / 2))
        print(error_m[["kd", "kt"]].round(3))
        print(error_p_autocorr[["kd", "kt"]].round(3))
        print(error_p_autocorr.loc[:].mean().round(2))

        error_m.to_pickle(DATA_PATH / "irr_data" / "error_m.pkl")
        error_stdp.to_pickle(DATA_PATH / "irr_data" / "error_stdp.pkl")

    ############## Probabilistic metrics ##############
    df_95 = pd.DataFrame(dtype=float, columns=["ghi", "dhi", "bhi"])
    df_75 = pd.DataFrame(dtype=float, columns=["ghi", "dhi", "bhi"])
    df_50 = pd.DataFrame(dtype=float, columns=["ghi", "dhi", "bhi"])
    df_25 = pd.DataFrame(dtype=float, columns=["ghi", "dhi", "bhi"])
    q_kt = pd.DataFrame(dtype=float)

    train_index = euro_stations[:int(0.75 * len(euro_stations))]
    test_index =  euro_stations[int(0.75 * len(euro_stations)):]

    for station in euro_stations:
        print(station)
        sat_data, insitu_data, solar_position = load_bsrn_data(START_BSRN, END_BSRN, station, user, password)
        lat, long, alt = bsrn_lat_long_alt(station)
        filter = (insitu_data["ghi"] > 0) & (sat_data["ghi"] > 0) & (np.isin(insitu_data.index.year, YEARS[station]))

        # Shorten the datasets
        sat_data = sat_data.loc[filter[filter].index[0]:filter[filter].index[-1]]
        insitu_data = insitu_data.loc[filter[filter].index[0]: filter[filter].index[-1]]
        solar_position = solar_position.loc[filter[filter].index[0]:filter[filter].index[-1]]

        quantiles = [0.025, 0.975]
        ghi = sat_data["ghi"]
        lon = long
        elev_step = 5
        light = True
        sat_source = "cams_pvlib"
        k_indice="kt"

        # Quantile generation
        ghi_qs, dhi_qs, bhi_qs = irrh_scenarios_v2(lat, long, alt, sat_data["ghi"],
                                                   quantiles=[0.025, 0.975],
                                                   light=True)
        ghi_qs, dhi_qs, bhi_qs = irrh_scenarios_v2(lat, long, alt, sat_data["ghi"],
                                                   quantiles=[0.025, 0.975],
                                                   light=False)


    ############## Calculate kt-error as function of kt ##############

    for station in tqdm(euro_stations):
        lat, lon, alt = bsrn_lat_long_alt(station)
        sat_data, insitu_data, solar_position = load_bsrn_data(START_BSRN, END_BSRN, station, user, password)

        filter = (insitu_data["ghi"] > 0) & (sat_data["ghi"] > 0) & (np.isin(insitu_data.index.year, YEARS[station]))


    ############## GHI/BHI/DHI illustration ##############
    user, password = Config().bsrn()
    station = "pal"
    start_2 = pd.to_datetime("20220812").tz_localize("CET")
    end_2 = pd.to_datetime("20220816").tz_localize("CET")
    sat_data, insitu_data, solar_position = load_bsrn_data(START_BSRN, END_BSRN, station, user, password)
    sat_data = sat_data.loc[start_2: end_2].copy()
    insitu_data = insitu_data.loc[start_2: end_2].copy()
    solar_position = solar_position.loc[start_2: end_2].copy()

    lat, long, alt = bsrn_lat_long_alt(station)
    ghi_scns, dhi_scns, bhi_scns = irrh_scenarios_v2(lat, long, alt,   solar_position, sat_data["ghi"])
    if plot_bool:
        # GHI, BHI, DHI, POAgrd
        q_ranges = [0.5, 0.9]
        fig, axes = plt.subplots(3, 1, figsize=(8, 6), sharex=True)

        # GHI
        axes[0].plot(insitu_data.loc[:, "ghi"].index.tz_convert("CET"), insitu_data.loc[:, "ghi"], color="black", marker=".",
                     label=f"In-situ BSRN '{station}' GHI", linewidth=1)
        axes[0].plot(ghi_scns.loc[start_2:end_2, 0.5].index.tz_convert("CET"), ghi_scns.loc[start_2:end_2, 0.5].tz_convert("CET"), color="red", marker=".",
                     label=f"In-situ BSRN '{station}' GHI", linewidth=1)
        axes[0] = q_plot_v2(ghi_scns.loc[start_2:end_2].tz_convert("CET"), q_ranges=q_ranges, color=blue, ax=axes[0], label="GHI")
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
