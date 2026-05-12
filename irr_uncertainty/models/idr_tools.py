import gc
import numpy as np
import os
import pandas as pd

from isodisreg import idr
from tqdm import tqdm
from isodisreg.modeling_evaluation import idrobject
from scipy.stats import norm
from scipy.optimize import brentq
from statsmodels.nonparametric.bandwidths import bw_silverman

from irr_uncertainty.config import Config, DATA_PATH
from irr_uncertainty.data.irr_data import load_pvlive_data, load_bsrn_welev
from irr_uncertainty.data.station_metadata import pvlive_lat_long_alt
from irr_uncertainty.data.station_metadata import stations_pv_live
from irr_uncertainty.models.optic_model import get_kt, get_kpoa, erbs_simple
from irr_uncertainty.models.uncertainty_config import euro_stations, START_BSRN, END_BSRN, YEARS, YEARS_5y


def get_idr_path(elev, indice, light=False, sat_source="cams_pvlib"):
    path = DATA_PATH / "idr_objects" / f"{indice}_idrless{elev}_light{light}_{sat_source}.npz"
    return path


def npz_idr_save(fitted_idr, path):
    np.savez_compressed(path,
                        ecdf=fitted_idr.ecdf.astype("float32"),
                        thresholds=fitted_idr.thresholds.astype("float32"),
                        indices=fitted_idr.indices,
                        X=fitted_idr.X.astype("float32"),
                        y=fitted_idr.y,
                        groups=fitted_idr.groups,
                        orders=fitted_idr.orders,
                        constraints=fitted_idr.constraints)
    return None


def npz_idr_load(path):
    if os.path.exists(path):
        with np.load(path, allow_pickle=True) as idr_load:
            idr_obj = idrobject(idr_load["ecdf"],
                                idr_load["thresholds"],
                                pd.DataFrame(idr_load["indices"]),
                                pd.DataFrame(idr_load["X"]),
                                pd.DataFrame(idr_load["y"]),
                                idr_load["groups"].item(),
                                idr_load["orders"].item(),
                                idr_load["constraints"])
    else:
        idr_obj = None
    return idr_obj


def idrs_fit(cases, k_sats, k_insitus, paths, k_indice: str):
    for case in tqdm(cases, desc=f"{k_indice}-IDR fitting process"):
        if len(k_sats[case]) > 100:
            # Fitting process
            fitted_idr = idr(k_insitus[case], pd.Series(k_sats[case]).to_frame())

            # Save
            _ = npz_idr_save(fitted_idr, paths[case])

            del fitted_idr  # Free up some memory temporary
    return None


def extend_idr_fit(cases, ts_sats, paths):
    ## Treatment for small elev
    for case in cases:
        if len(ts_sats[case]) < 100:
            path = paths[case]
            for case_higher in cases:
                if case_higher > case:
                    path_elev_higher = paths[case_higher]
                    if os.path.exists(str(path_elev_higher)):
                        fitted_idr = npz_idr_load(path_elev_higher)

                        # Save
                        _ = npz_idr_save(fitted_idr, path)

                        break

    ## Treatment for higher elev
    for case in cases:
        path = paths[case]
        if (len(ts_sats[case]) < 100) and not os.path.exists(str(path)):
            path = paths[case]
            for elev_lower in cases[::-1]:
                if elev_lower < case:
                    path_elev_lower = paths[elev_lower]
                    if os.path.exists(str(path_elev_lower)):
                        fitted_idr = npz_idr_load(path_elev_lower)

                        # Save
                        _ = npz_idr_save(fitted_idr, path)

                        break
    return None


def kt_idr_fit(
        overwrite=False,
        train_index=euro_stations[:int(0.75 * len(euro_stations))],
        user=Config().bsrn()[0],
        password=Config().bsrn()[1],
        sat_source="cams_pvlib",
        elev_step: int = 5,
        light=False):
    """
    Computes and stores the fitted kt-Isotonic Distribution Regression.

    If a precomputed IDR exists, it loads the data from a pickle file unless `overwrite=True`.
    Optionally, it can also plot the distributions for each interval.

    :param overwrite: Boolean flag to force recalculation of kd-error distributions if set to True. Default is False.
    :param train_index: List of station indices used for training. Default is 75% of `euro_stations`.
    :param user: Username for accessing BSRN data. Default is retrieved from `Config().bsrn()`.
    :param password: Password for accessing BSRN data. Default is retrieved from `Config().bsrn()`.
    :param sat_source: Satellite source: "cams_pvlib" as only option for now.
    :param legend: print the legend ?
    :param elev_step

    :return: A pandas DataFrame containing the estimated kd-error distributions and fitted parameters.
    """

    elevs = np.arange(0, 90, elev_step)
    paths = {elev: get_idr_path(elev, "kt", light, sat_source) for elev in elevs}

    if (not any([os.path.exists(str(path)) for _, path in paths.items()])) or overwrite:

        kt_sats = {elev: np.array([]) for elev in elevs}
        kt_insitus = {elev: np.array([]) for elev in elevs}

        for i, station in tqdm(enumerate(train_index), total=len(train_index),
                               desc="Collecting station data for kt-IDR fitting process"):
            sat_data, insitu_data, solar_position, elevation = \
                load_bsrn_welev(START_BSRN, END_BSRN, station, user, password, sat_source="cams_pvlib")

            ghi_sat = sat_data["ghi"]
            ghi_insitu = sat_data["ghi"]
            kt_sat = sat_data["kt"]
            kt_insitu = insitu_data["kt"]

            # Filters
            filter = (ghi_insitu > 0) & (ghi_sat > 0) & (~kt_insitu.isna())
            if light:
                filter = filter & (np.isin(insitu_data.index.year, YEARS_5y[station]))
            else:
                filter = filter & (np.isin(insitu_data.index.year, YEARS[station]))

            for elev in elevs:
                index_pos_elev = ghi_sat[filter & (elevation >= elev) & (elevation < elev + elev_step)].index

                kt_sats[elev] = np.append(kt_sats[elev], kt_sat.loc[index_pos_elev].values)
                kt_insitus[elev] = np.append(kt_insitus[elev], kt_insitu.loc[index_pos_elev].values)

        _ = idrs_fit(elevs, kt_sats, kt_insitus, paths, k_indice="kt")
        _ = extend_idr_fit(elevs, kt_sats, paths)

    return None


def kd_idr_fit(
        overwrite=False,
        train_index=euro_stations[:int(0.75 * len(euro_stations))],
        user=Config().bsrn()[0],
        password=Config().bsrn()[1],
        sat_source="cams_pvlib",
        elev_step: int = 5,
        light=False):
    """
    Computes and stores the fitted kd-Isotonic Distribution Regression.

    If a precomputed IDR exists, it loads the data from a pickle file unless `overwrite=True`.
    Optionally, it can also plot the distributions for each interval.

    :param overwrite: Boolean flag to force recalculation of kd-error distributions if set to True. Default is False.
    :param train_index: List of station indices used for training. Default is 75% of `euro_stations`.
    :param user: Username for accessing BSRN data. Default is retrieved from `Config().bsrn()`.
    :param password: Password for accessing BSRN data. Default is retrieved from `Config().bsrn()`.
    :param sat_source: Satellite source: "cams_pvlib" as only option for now.
    :param legend: print the legend ?
    :param elev_step

    :return: A pandas DataFrame containing the estimated kd-error distributions and fitted parameters.
    """

    elevs = np.arange(0, 90, elev_step)
    paths = {elev: get_idr_path(elev, "kd", light, sat_source) for elev in elevs}

    if (not any([os.path.exists(str(path)) for _, path in paths.items()])) or overwrite:

        kd_sats = {elev: np.array([]) for elev in elevs}
        kd_insitus = {elev: np.array([]) for elev in elevs}

        for i, station in tqdm(enumerate(train_index), total=len(train_index),
                               desc="Collecting station data for kd-IDR fitting process"):
            sat_data, insitu_data, solar_position, elevation = \
                load_bsrn_welev(START_BSRN, END_BSRN, station, user, password, sat_source="cams_pvlib")

            kd_sat = sat_data["kd"]
            ghi_sat = sat_data["ghi"]
            ghi_insitu = insitu_data["ghi"]
            kd_insitu = insitu_data["dhi"] / sat_data["ghi"]

            # Positive filters
            filter = (ghi_insitu > 0) & (ghi_sat > 0) & (~kd_insitu.isna())
            if light:
                filter = filter & (np.isin(insitu_data.index.year, YEARS_5y[station]))
            else:
                filter = filter & (np.isin(insitu_data.index.year, YEARS[station]))

            for elev in elevs:
                index_pos_elev = ghi_sat[filter & (elevation >= elev) & (elevation < elev + elev_step)].index

                kd_sats[elev] = np.append(kd_sats[elev], kd_sat.loc[index_pos_elev].values)
                kd_insitus[elev] = np.append(kd_insitus[elev], kd_insitu.loc[index_pos_elev].values)

        _ = idrs_fit(elevs, kd_sats, kd_insitus, paths, k_indice="kt")
        _ = extend_idr_fit(elevs, kd_sats, paths)

    return None


def kb_idr_fit(
        overwrite=False,
        train_index=euro_stations[:int(0.75 * len(euro_stations))],
        user=Config().bsrn()[0],
        password=Config().bsrn()[1],
        sat_source="cams_pvlib",
        elev_step: int = 5,
        light=False):
    """
    Computes and stores the fitted kd-Isotonic Distribution Regression.

    If a precomputed IDR exists, it loads the data from a pickle file unless `overwrite=True`.
    Optionally, it can also plot the distributions for each interval.

    :param overwrite: Boolean flag to force recalculation of kd-error distributions if set to True. Default is False.
    :param train_index: List of station indices used for training. Default is 75% of `euro_stations`.
    :param user: Username for accessing BSRN data. Default is retrieved from `Config().bsrn()`.
    :param password: Password for accessing BSRN data. Default is retrieved from `Config().bsrn()`.
    :param sat_source: Satellite source: "cams_pvlib" as only option for now.
    :param legend: print the legend ?
    :param elev_step

    :return: A pandas DataFrame containing the estimated kd-error distributions and fitted parameters.
    """

    elevs = np.arange(0, 90, elev_step)
    paths = {elev: get_idr_path(elev, "kb", light, sat_source) for elev in elevs}

    if (not any([os.path.exists(str(path)) for _, path in paths.items()])) or overwrite:

        kb_sats = {elev: np.array([]) for elev in elevs}
        kb_insitus = {elev: np.array([]) for elev in elevs}

        for i, station in tqdm(enumerate(train_index), total=len(train_index),
                               desc="Collecting station data for kb-IDR fitting process"):
            sat_data, insitu_data, solar_position, elevation = \
                load_bsrn_welev(START_BSRN, END_BSRN, station, user, password, sat_source="cams_pvlib")

            kb_sat = sat_data["kb"]
            ghi_sat = sat_data["ghi"]
            ghi_insitu = insitu_data["ghi"]
            kb_insitu = insitu_data["bhi"] / sat_data["ghi"]

            # Positive filters
            filter = (ghi_insitu > 0) & (ghi_sat > 0) & (~kb_insitu.isna())
            if light:
                filter = filter & (np.isin(insitu_data.index.year, YEARS_5y[station]))
            else:
                filter = filter & (np.isin(insitu_data.index.year, YEARS[station]))

            for elev in elevs:
                index_pos_elev = ghi_sat[filter & (elevation >= elev) & (elevation < elev + elev_step)].index

                kb_sats[elev] = np.append(kb_sats[elev], kb_sat.loc[index_pos_elev].values)
                kb_insitus[elev] = np.append(kb_insitus[elev], kb_insitu.loc[index_pos_elev].values)

        _ = idrs_fit(elevs, kb_sats, kb_insitus, paths, k_indice="kb")
        _ = extend_idr_fit(elevs, kb_sats, paths)

    return None


def kpoa_idr_fit(
        overwrite=False,
        train_index=list(stations_pv_live().index)[:int(0.25 * len(list(stations_pv_live().index)))],
        sat_source="cams_pvlib",
        aoi_step: int = 5,
        light=False):
    """
    Computes and stores the fitted kpoa-Isotonic Distribution Regression.

    If a precomputed IDR exists, it loads the data from a pickle file unless `overwrite=True`.
    Optionally, it can also plot the distributions for each interval.

    :param overwrite: Boolean flag to force recalculation of kd-error distributions if set to True. Default is False.
    :param train_index: List of station indices used for training. Default is 25% of `pv_live stations`.
    :param sat_source: Satellite source: "cams_pvlib" as only option for now
    :param legend: print the legend ?
    :param elev_step

    :return: A pandas DataFrame containing the estimated kd-error distributions and fitted parameters.
    """

    aois = np.arange(0, 180, aoi_step)
    paths = {aoi_i: get_idr_path(aoi_i, "kpoa", light, sat_source) for aoi_i in aois}

    if (not any([os.path.exists(str(path)) for _, path in paths.items()])) or overwrite:

        kpoa_sats = {aoi_i: np.array([]) for aoi_i in aois}
        kpoa_insitus = {aoi_i: np.array([]) for aoi_i in aois}

        train_index_tmp = train_index[:(int(len(train_index) / 2))] if light else train_index

        for i, station in tqdm(enumerate(train_index_tmp), total=len(train_index_tmp),
                               desc="Collecting station data for kpoa-IDR fitting process"):

            sat_data, insitu_h, insitu_s, insitu_e, insitu_w, solar_position = \
                load_pvlive_data(station=station, sat_source=sat_source)

            ghi_sat = sat_data["ghi"]
            ghi_insitu = insitu_h["Gg_pyr"]

            # Positive filters
            filter = (ghi_insitu > 0) & (ghi_sat > 0)

            for aoi_i in aois:
                for orientation, df in {"e": insitu_e, "s": insitu_s, "w": insitu_w}.items():
                    index_sat = ghi_sat[filter].index
                    index_insitu = df[(df["aoi"] >= aoi_i) & (df["aoi"] < aoi_i + aoi_step)].dropna().index
                    index_filter = index_sat.intersection(index_insitu)

                    kpoa_sats[aoi_i] = np.append(kpoa_sats[aoi_i],
                                                 sat_data.loc[index_filter, f"kpoa_{orientation}"].values)
                    kpoa_insitus[aoi_i] = np.append(kpoa_insitus[aoi_i], df.loc[index_filter, "kpoa"].values)

        _ = idrs_fit(aois, kpoa_sats, kpoa_insitus, paths, k_indice="kpoa")
        _ = extend_idr_fit(aois, kpoa_sats, paths)

    return None


class IDRSmooth:
    def __init__(self, data: np.array):
        self.data = np.asarray(data)
        self.h = bw_silverman(self.data) if len(self.data) > 1 else self.data[0]

        # Pre-compute the Quantile Grid for Linear Interpolation
        x_range = np.linspace(self.data.min() - 3 * self.h, self.data.max() + 3 * self.h, 100)
        p_range = self.cdf(x_range)
        self.p_range = p_range
        self.x_range = x_range

    def cdf(self, x):
        """Calcule P(X <= x)"""
        x = np.atleast_1d(x)
        z = (x[:, np.newaxis] - self.data) / self.h
        weights = np.ones(len(self.data)) / len(self.data)
        return np.sum(weights * norm.cdf(z), axis=1)

    def _compute_exact_ppf(self, q_values):
        """Internal solver to find exact roots for the grid."""
        res = []
        low, high = self.data[0] - 5 * self.h, self.data[-1] + 5 * self.h
        if not type(q_values) is list:
            q_values = [q_values]
        for val in q_values:
            root = brentq(lambda x: self.cdf(x)[0] - val, low, high)
            res.append(root)
        return np.array(res)

    def ppf(self, q):
        #  Backwards interpolation
        return np.interp(q, self.p_range, self.x_range)

    def sample(self, n_samples=1):
        indices = np.random.choice(len(self.data), size=n_samples, p=self.weights)
        return self.data[indices] + np.random.normal(0, self.h, size=n_samples)


def elev_dicts(all_elevs, elev_step):
    elevs = np.arange(0, 90, elev_step)
    elev_bool = {}
    for elev in elevs:
        filter_elev = (all_elevs >= elev) & (all_elevs < (elev + elev_step))
        elev_bool[elev] = True if len(all_elevs[filter_elev]) > 0 else None
    return elev_bool


def aoi_dicts(all_aois, aoi_step):
    aois = np.arange(0, 180, aoi_step)
    aoi_bool = {}
    for aoi_i in aois:
        filter_aoi = (all_aois >= aoi_i) & (all_aois < (aoi_i + aoi_step))
        aoi_bool[aoi_i] = True if len(all_aois[filter_aoi]) > 0 else None
    return aoi_bool


def idr_fc(cases, case_step, cases_bool, case_ts, path_cases, ts, quantiles, k_indice: str):
    # disable garbage collector (to go faster)
    gc.disable()
    fc_array_list = []
    for case in tqdm(cases, desc=f"{k_indice} IDR inference"):
        if cases_bool[case]:
            # Filter on the cases
            filter = (case_ts >= case) & (case_ts < (case + case_step))
            ts_filter = ts.loc[filter]

            # Import and predict the IDR
            path = path_cases[case]
            fitted_idr = npz_idr_load(path)
            fcs = fitted_idr.predict(pd.DataFrame(ts_filter.values))
            del fitted_idr  # Remove space

            # Compute quantiles point per point
            fc_array = np.zeros((len(ts_filter.index), len(quantiles)))
            for i, fc in enumerate(fcs.predictions):
                sd = IDRSmooth(data=fc.points)
                q_values = sd.ppf(quantiles)
                fc_array[i] = q_values

            fc_array_list += [pd.DataFrame(fc_array, index=ts_filter.index, columns=quantiles)]

    # enable garbage collector again
    gc.enable()

    fc_q = pd.concat(fc_array_list)
    fc_q = fc_q.sort_index()

    return fc_q


def ktq_idr_fc(ghi, lat, lon, alt, quantiles=[0.05, 0.25, 0.5, 0.75, 0.95], elev_step=5, light=False,
               sat_source="cams_pvlib"):
    # Fit
    _ = kt_idr_fit(elev_step=elev_step, light=light, sat_source=sat_source)

    # Compute the reference satellite clearness index
    kt_ts, _, _, elevation = get_kt(ghi, lat, lon, alt, return_ghiextra_elev=True)

    # Prepare the inputs for forecasting
    all_elevs = elevation.loc[ghi > 0]
    elev_bool = elev_dicts(all_elevs, elev_step)
    elevs = list(elev_bool.keys())
    path_elevs = {elev: get_idr_path(elev, "kt", light, sat_source) for elev in elevs}

    # Forecast
    kt_scns = idr_fc(elevs, elev_step, elev_bool, elevation, path_elevs, kt_ts, quantiles, "kt")

    return kt_scns.clip(lower=0)


def kdq_idr_fc(ghi, lat, lon, alt, quantiles=[0.05, 0.25, 0.5, 0.75, 0.95], elev_step=5, light=False,
               sat_source="cams_pvlib"):
    # Fit
    _ = kd_idr_fit(elev_step=elev_step, light=light, sat_source=sat_source)

    # Compute the reference satellite clearness index
    kt_ts, _, _, elevation = get_kt(ghi, lat, lon, alt, return_ghiextra_elev=True)
    kd_ts = erbs_simple(kt_ts)

    # Prepare the inputs for forecasting
    all_elevs = elevation.loc[ghi > 0]
    elev_bool = elev_dicts(all_elevs, elev_step)
    elevs = list(elev_bool.keys())
    path_elevs = {elev: get_idr_path(elev, "kd", light, sat_source) for elev in elevs}

    # Forecast
    kd_scns = idr_fc(elevs, elev_step, elev_bool, elevation, path_elevs, kd_ts, quantiles, "kd")

    return kd_scns.clip(lower=0)


def kbq_idr_fc(ghi, lat, lon, alt, quantiles=[0.05, 0.25, 0.5, 0.75, 0.95], elev_step=5, light=False,
               sat_source="cams_pvlib"):
    # Fit
    _ = kb_idr_fit(elev_step=elev_step, light=light, sat_source=sat_source)

    # Compute the reference satellite clearness index
    kt_ts, _, _, elevation = get_kt(ghi, lat, lon, alt, return_ghiextra_elev=True)
    kb_ts = 1 - erbs_simple(kt_ts)

    # Prepare the inputs for forecasting
    all_elevs = elevation.loc[ghi > 0]
    elev_bool = elev_dicts(all_elevs, elev_step)
    elevs = list(elev_bool.keys())
    path_elevs = {elev: get_idr_path(elev, "kb", light, sat_source) for elev in elevs}

    # Forecast
    kb_scns = idr_fc(elevs, elev_step, elev_bool, elevation, path_elevs, kb_ts, quantiles, "kb")

    return kb_scns.clip(lower=0)


def kpoaq_idr_fc(ghi, lat, lon, alt, tilt, surface_azimuth,
                 quantiles=[0.05, 0.25, 0.5, 0.75, 0.95], aoi_step=5, light=False,
                 sat_source="cams_pvlib"):
    # Fit
    _ = kpoa_idr_fit(aoi_step=aoi_step, light=light, sat_source=sat_source)

    # Compute the reference satellite clearness index
    _, _, _, elevation = get_kt(ghi, lat, lon, alt, return_ghiextra_elev=True)
    kpoa_ts, _, aoi_angle = get_kpoa(ghi.index, lat, lon, alt, tilt, surface_azimuth, ghi=ghi)
    aoi_angle_h = aoi_angle.resample("H").mean().reindex(kpoa_ts.index)

    # Prepare the inputs for forecasting
    aoi_ts = aoi_angle_h.loc[ghi > 0]
    kpoa_ts = kpoa_ts.loc[ghi > 0]
    aoi_bool = aoi_dicts(aoi_ts, aoi_step)
    aois = list(aoi_bool.keys())
    path_elevs = {aoi_i: get_idr_path(aoi_i, "kpoa", light, sat_source) for aoi_i in aois}

    kpoa_scns = idr_fc(aois, aoi_step, aoi_bool, aoi_ts, path_elevs, kpoa_ts, quantiles, "kpoa")

    return kpoa_scns.clip(lower=0)
