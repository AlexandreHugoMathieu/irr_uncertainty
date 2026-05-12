""" This module includes function to model irradiance uncertainty"""
# Created by A. MATHIEU at 27/10/2023
import numpy as np
import pandas as pd
from tqdm import tqdm

from irr_uncertainty.data.irr_data import load_pvlive_data, load_bsrn_data
from irr_uncertainty.models.irr_limits import get_irr_limits, get_poa_limits
from irr_uncertainty.models.optic_model import get_kt, get_kpoa

from irr_uncertainty.data.station_metadata import pvlive_lat_long_alt, bsrn_lat_long_alt
from irr_uncertainty.models.idr_tools import kpoaq_idr_fc, kdq_idr_fc, ktq_idr_fc, \
    kbq_idr_fc, npz_idr_load

from irr_uncertainty.models.uncertainty_config import START_BSRN, END_BSRN
from irr_uncertainty.config import Config
from irr_uncertainty.data.irr_data import get_cams

# station = "pal"
# user, password = Config().bsrn()
# start = pd.to_datetime("20220101").tz_localize("CET")
# end = END_BSRN
# sat_data, insitu_data, solar_position = load_bsrn_data(start, END_BSRN, station, user, password)
# lat, long, alt = bsrn_lat_long_alt(station)
# # station = 20
# # sat_data, insitu_h, insitu_s, insitu_e, insitu_w, solar_position = load_pvlive_data(station=station, sat_source="cams_pvlib")
#
# ghi = sat_data["ghi"]
# # lat, long, alt = pvlive_lat_long_alt(station)
#
# tilt = 25
# azimuth = 180
# elev_step = 5
# lon = long
# sat_source = "cams_pvlib"
# quantiles: list = [0.05, 0.25, 0.5, 0.75, 0.95]
# light = True


def irrh_scenarios_v2(lat, long, alt,
                      ghi: pd.Series,
                      quantiles: list = [0.05, 0.25, 0.5, 0.75, 0.95],
                      light=False,
                      sat_source: str = "cams_pvlib",
                      ) -> pd.DataFrame:
    """
    Generate Monte Carlo simulations to account for irradiance uncertainty on the horizontal plane.

    :param lat: Latitude of the installation [°]
    :param long: Longitude of the installation [°]
    :param alt:  Altitude of the installation [m]
    :param solar_position: Solar position dataframe with an hourly granularity with azimuth/elevation/zenith columns
    :param ghi: Global Horizontal Irradiance timeserie (provided from satellite data)
    :param n_scenarios: Number of Monte Carlo simulations to generate
    :param sat_source: What satellite provider for the kd-error modeling ? "cams_pvlib" as only option for now


    :return: 3 pd.DataFrames with "n_scenarios" columns and same index as "ghi" containing the GHI/DHI/BHI Monte Carlo simulations
    """
    # Set lower/higher limits with clearsky GHI for DNI and BHI, deduct DHI
    ghi_limit, bhi_limit, dhi_limit = get_irr_limits(ghi.index, lat, long, alt)
    kt_ts, ghi_extra, dni_extra, elevation = get_kt(ghi, lat, long, alt, return_ghiextra_elev=True)

    # TODO: Add years until 2025 included
    kt_qs = ktq_idr_fc(ghi, lat, long, alt, quantiles, light=light, sat_source=sat_source)
    kd_qs = kdq_idr_fc(ghi, lat, long, alt, quantiles, light=light, sat_source=sat_source)
    kb_qs = kbq_idr_fc(ghi, lat, long, alt, quantiles, light=light, sat_source=sat_source)

    # Separate indexes
    ghi_qs = pd.DataFrame(data=np.nan, index=ghi.index, columns=quantiles)
    dhi_qs = pd.DataFrame(data=np.nan, index=ghi.index, columns=quantiles)
    bhi_qs = pd.DataFrame(data=np.nan, index=ghi.index, columns=quantiles)
    for q in quantiles:
        kt_q = kt_qs[q]
        kd_q = kd_qs[q]
        kb_q = kb_qs[q]

        ghi_qs.loc[kt_q.index, q] = (kt_q * ghi_extra.loc[kt_q.index]).fillna(0)
        dhi_qs.loc[kd_q.index, q] = (kd_q * ghi_extra.loc[kd_q.index] * kt_ts.loc[kd_q.index])
        bhi_qs.loc[kd_q.index, q] = (kb_q * ghi_extra.loc[kd_q.index] * kt_ts.loc[kd_q.index])

    ghi_qs = ghi_qs.clip(lower=ghi_limit["lower"], upper=ghi_limit["upper"], axis=0).fillna(0)
    dhi_qs = dhi_qs.clip(lower=dhi_limit["lower"], upper=dhi_limit["upper"], axis=0).fillna(0)
    bhi_qs = bhi_qs.clip(lower=bhi_limit["lower"], upper=bhi_limit["upper"], axis=0).fillna(0)

    kt_ts, ghi_extra, _, elevation = get_kt(ghi, lat, long, alt, return_ghiextra_elev=True)

    # kt_scns.plot()
    # kt_ts.plot(color="red", marker=".")
    #
    # bhi_qs.plot()
    # sat_data["bhi"].plot(color="red", marker=".")
    # insitu_data["bhi"].plot(color="blue", marker=".")
    #
    # dhi_qs.plot()
    # sat_data["dhi"].plot(color="red", marker=".")
    # insitu_data["dhi"].plot(color="blue", marker=".")
    #
    # insitu_h["Gg_pyr"].plot(color="black", marker=".")
    #
    # ghi_qs.plot()
    # ghi.plot(color="red", marker=".")
    # insitu_data["ghi"].plot(color="black", marker=".")
    # ghi_qs[0.05].plot(color="brown")
    #
    # filter = (insitu_data["ghi"] > 50) & (elevation > 20)
    #
    # (ghi_qs[0.05].reindex(insitu_data.index).loc[filter] < insitu_data["ghi"].loc[filter]).mean()
    # (ghi_qs[0.25].reindex(insitu_data.index).loc[filter] < insitu_data["ghi"].loc[filter]).mean()
    # (ghi_qs[0.50].reindex(insitu_data.index).loc[filter] < insitu_data["ghi"].loc[filter]).mean()
    # (ghi_qs[0.75].reindex(insitu_data.index).loc[filter] < insitu_data["ghi"].loc[filter]).mean()
    # (ghi_qs[0.95].reindex(insitu_data.index).loc[filter] < insitu_data["ghi"].loc[filter]).mean()
    #
    # filter = insitu_data["dhi"] > 50
    # (dhi_qs[0.05].reindex(insitu_data.index).loc[filter] < insitu_data["dhi"].loc[filter]).mean()
    # (dhi_qs[0.25].reindex(insitu_data.index).loc[filter] < insitu_data["dhi"].loc[filter]).mean()
    # (dhi_qs[0.50].reindex(insitu_data.index).loc[filter] < insitu_data["dhi"].loc[filter]).mean()
    # (dhi_qs[0.75].reindex(insitu_data.index).loc[filter] < insitu_data["dhi"].loc[filter]).mean()
    # (dhi_qs[0.95].reindex(insitu_data.index).loc[filter] < insitu_data["dhi"].loc[filter]).mean()
    #
    # insitu_data = insitu_data[~insitu_data.index.duplicated()]
    # kd_scns = kd_scns[~kd_scns.index.duplicated()]
    # filter = insitu_data["ghi"] > 100
    # insitu_data["kt_obs"] = insitu_data["dhi"] / sat_data["ghi"]
    # (kd_scns[0.05].reindex(insitu_data.index).loc[filter] < insitu_data["kt_obs"].loc[filter]).mean()
    # (kd_scns[0.25].reindex(insitu_data.index).loc[filter] < insitu_data["kt_obs"].loc[filter]).mean()
    # (kd_scns[0.50].reindex(insitu_data.index).loc[filter] < insitu_data["kt_obs"].loc[filter]).mean()
    # (kd_scns[0.75].reindex(insitu_data.index).loc[filter] < insitu_data["kt_obs"].loc[filter]).mean()
    # (kd_scns[0.95].reindex(insitu_data.index).loc[filter] < insitu_data["kt_obs"].loc[filter]).mean()
    #
    # kd_scns[0.95].reindex(insitu_data.index).loc[filter]
    #
    # filter = insitu_data["bhi"] > 50
    # (bhi_qs[0.05].reindex(insitu_data.index).loc[filter] < insitu_data["bhi"].loc[filter]).mean()
    # (bhi_qs[0.25].reindex(insitu_data.index).loc[filter] < insitu_data["bhi"].loc[filter]).mean()
    # (bhi_qs[0.50].reindex(insitu_data.index).loc[filter] < insitu_data["bhi"].loc[filter]).mean()
    # (bhi_qs[0.75].reindex(insitu_data.index).loc[filter] < insitu_data["bhi"].loc[filter]).mean()
    # (bhi_qs[0.95].reindex(insitu_data.index).loc[filter] < insitu_data["bhi"].loc[filter]).mean()

    return ghi_qs, dhi_qs, bhi_qs


def poa_scns(lat, long, alt, tilt, surface_azimuth,
             ghi: pd.Series,
             quantiles=[0.05, 0.25, 0.5, 0.75, 0.95],
             aoi_step=5,
             sat_source="cams_pvlib",
             light=False):

    # get_poa_limits(tilt, azimuth, solar_position)
    kpoa, poa_extra, _ = get_kpoa(ghi.index, lat, long, alt, tilt, surface_azimuth, ghi=ghi)
    kpoa_qs = kpoaq_idr_fc(ghi, lat, long, alt, tilt, surface_azimuth, quantiles,
                           aoi_step=aoi_step, light=light, sat_source=sat_source)
    # Separate indexes
    poa_qs = pd.DataFrame(data=np.nan, index=ghi.index, columns=quantiles)
    for q in quantiles:
        kpoa_q = kpoa_qs[q]

        poa_qs.loc[kpoa_q.index, q] = (kpoa_q * poa_extra.loc[kpoa_q.index]).fillna(0)

    # poa_qs = poa_qs.clip(lower=ghi_limit["lower"], upper=ghi_limit["upper"], axis=0).fillna(0)
    # poa_qs.plot()

    return poa_qs
