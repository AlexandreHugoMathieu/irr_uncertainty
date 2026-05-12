"""Scripts to get satellite and in-situ irradiance data"""
# Created by A. MATHIEU at 14/12/2022
import numpy as np
import urllib
import urllib.request
import io
import zipfile
import os
import pandas as pd
import warnings

from datetime import datetime
from pathlib import Path
from tqdm import tqdm

from pvlib.iotools import get_cams, get_bsrn
from pvlib.irradiance import dni, get_extra_radiation, clearness_index, aoi
from pvlib.location import Location
from pvlib.iotools import get_pvgis_hourly

from irr_uncertainty.config import DATA_PATH, Config
from irr_uncertainty.data.solar_data import get_filter_v2, solarpos, get_solar_position_1m
from irr_uncertainty.data.station_metadata import bsrn_lat_long_alt, pvlive_lat_long_alt
from irr_uncertainty.models.irr_limits import get_irr_limits
from irr_uncertainty.models.optic_model import erbs_simple, get_kt, get_kpoa

PVLIVE_BASE_URL = 'https://zenodo.org/record/7311989/files/'


def filter_dates(df, start, end):
    df = df.loc[((df.index) >= start) & ((df.index) < end)]
    df = df.sort_index()
    df = df[~df.index.duplicated()].copy()
    return df


def ghi_dhi_bhi_pvgis_2015(lat: float, long: float, print=False):
    """
    Retrieve or compute GHI, BHI, and DHI solar irradiation values for given coordinates using PVGIS ERA5 data (2015),
    and store the data locally to speed up future access.

    :param lat: Latitude of the location (float)
    :param long: Longitude of the location (float)
    :param print: Whether to print status messages during execution (bool, default False)

    :return: List containing [GHI, BHI, DHI] values for the specified location in 2015
    """
    filename = DATA_PATH / "ghi_dhi_bhi_pvgis_2015.csv"

    if os.path.exists(filename):
        df = pd.read_csv(filename, index_col=0, sep=";").astype(float)
    else:
        df = pd.DataFrame(columns=["lat", "long", "ghi", "bhi", "dhi", "dni"])

    str_index = '{0:.2f}'.format(lat) + "_" + '{0:.2f}'.format(long)

    if str_index not in df.index:
        data, meta_data, legend = get_pvgis_hourly(lat, long, 2015, 2015, "PVGIS-ERA5", surface_tilt=0)
        df.loc[str_index, "lat"] = lat
        df.loc[str_index, "long"] = long
        df.loc[str_index, "ghi"] = data[['poa_direct', 'poa_sky_diffuse', 'poa_ground_diffuse']].sum().sum()
        df.loc[str_index, "bhi"] = data["poa_direct"].sum()
        df.loc[str_index, "dhi"] = data["poa_sky_diffuse"].sum()

        df = df.sort_index()
        df.to_csv(filename, sep=";")
        if print:
            print(f"{str_index} fetched")

    elif (str_index in df.index) and (df.loc[str_index, ["ghi", "bhi", "dhi"]].isna().sum() > 0):
        data, meta_data, legend = get_pvgis_hourly(lat, long, 2015, 2015, "PVGIS-ERA5", surface_tilt=0)

        df = pd.read_csv(filename, index_col=0, sep=";").astype(float)
        df.loc[str_index, "lat"] = lat
        df.loc[str_index, "long"] = long
        df.loc[str_index, "ghi"] = data[['poa_direct', 'poa_sky_diffuse', 'poa_ground_diffuse']].sum().sum()
        df.loc[str_index, "bhi"] = data["poa_direct"].sum()
        df.loc[str_index, "dhi"] = data["poa_sky_diffuse"].sum()

        df = df.sort_index()
        df.to_csv(filename, sep=";")
        if print:
            print(f"{str_index} fetched")
    else:
        if print:
            print(f"{str_index} extracted from file")

    return list(df.loc[str_index, ["ghi", "bhi", "dhi"]].astype(float).values)


def process_bsrn(station: str,
                 start: datetime,
                 end: datetime,
                 username=Config().bsrn()[0],
                 password=Config().bsrn()[1],
                 resample_freq: str = "H",
                 filtered: bool = False,
                 overwrite: bool = False):
    """
    Fetch data from BSRN stations (Store it locally to make it accessible faster)

    :param station: Station to fetch data for (3 characters)
    :param start: Start to fetch data for
    :param end: End to fetch data for
    :param username: BSRN username
    :param password: BSRN password
    :param resample_freq: resampling frequencies
    :param filtered: Filter in-situ data according to "get_filter_v2"
    :param overwrite: Fetch data even if already locally stored and overwrite pkl file

    :return: In-situ data
    """
    pkl_name = DATA_PATH / "bsrn_data" / f"{station.lower()}_{resample_freq}_{start.strftime('%Y%m%d')}_" \
                                         f"{end.strftime('%Y%m%d')}.pkl"

    lat, lon, alt = bsrn_lat_long_alt(station)
    if not overwrite and pkl_name.exists():
        data = pd.read_pickle(pkl_name)
    else:
        # Fetch year by year to avoid to have the query staling
        data = pd.DataFrame()
        for s_tmp in tqdm(pd.date_range(start, end, freq="YS")):
            e_tmp = s_tmp + pd.DateOffset(years=1)

            # Check if pkl file already exists at the yearly level
            pkl_tmp = DATA_PATH / "bsrn_data" / f"{station.lower()}_{resample_freq}_{s_tmp.strftime('%Y%m%d')}_" \
                                                f"{e_tmp.strftime('%Y%m%d')}.pkl"
            if ((not pkl_tmp.exists()) or overwrite):
                # Fetch data
                data_tmp, _ = get_bsrn(station=station, start=s_tmp, end=e_tmp, username=username, password=password)

                if filtered:
                    if (not data_tmp.empty):
                        # Calculate BHI based on solar position from DNI
                        solpos_1m = get_solar_position_1m(data_tmp.index, lat, lon, alt, pkl=False)
                        solpos_1m = solpos_1m.reindex(data_tmp.index)

                        # Compute BHI for filtering purpose
                        cos_z = np.cos(solpos_1m["apparent_zenith"].fillna(solpos_1m["zenith"]) * np.pi / 180)
                        data_tmp["bhi"] = (data_tmp["dni"] * cos_z).clip(lower=0)

                        # Apply filters
                        filter = get_filter_v2(data_tmp, solpos_1m)

                        # 85% of the values (Helioclim convention with start of time integration)
                        data_15min = \
                            data_tmp.loc[filter].resample("15min").mean().loc[
                            data_tmp.loc[filter, "ghi"].resample("15min").count() >= 13, :]
                        ghi_15min = data_15min["ghi"]

                        # 75% of the values (Helioclim convention with start of time integration)
                        data_H = data_15min.resample("60min").mean().loc[ghi_15min.resample("60min").count() >= 3]
                    else:
                        data_H = data_tmp

                if not filtered:
                    data_H = data_tmp.resample(resample_freq).mean() if (not data_tmp.empty) else data_tmp
                data_H.to_pickle(pkl_tmp)
            else:
                data_H = pd.read_pickle(pkl_tmp)
            data = pd.concat([data, data_H], axis=0)
        data.to_pickle(pkl_name)

    data = filter_dates(data, start, end)

    return data


def cams_data_pvlib(lat, lon, alt, start, end, cams_folder=DATA_PATH / "cams_data"):
    """
    Fetch CAMS data with the pvlib function (Store it locally to make it accessible faster)

    pvlib function: "get_cams". https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.iotools.get_cams.html

    :param lat: Latitude
    :param lon: Longitude
    :param alt: Altitude
    :param start: Start to fetch data for
    :param end: End to fetch data for
    :param cams_folder: Folder where to store the data

    :return: pd.DataFrame with GHI/DHI/DNI/BHI data
    """
    pkl_file = cams_folder / f"CAMS_{lat}_{lon}_{alt}_{start.strftime('%Y%m%d')}_{end.strftime('%Y%m%d')}_pvlib.pkl"

    if pkl_file.exists():
        data_all = pd.read_pickle(pkl_file)

    else:
        data, metadata = get_cams(lat, lon, start, end, altitude=alt, email=Config().cams(),
                                  identifier="cams_radiation", timeout=60 * 5)

        # overwrite label convention with start-of-Time integration
        obs_period = data['Observation period'].str.split('/')
        data.index = pd.to_datetime(obs_period.str[0], utc=True)

        # Save only relevant data in local time
        data = data.tz_convert('CET')
        data_all = data[["ghi", "bhi", "dhi", "dni"]]
        data_all.to_pickle(pkl_file)

    data_all = filter_dates(data_all, start, end)

    return data_all


def get_pvlive(station: str, start: datetime, end: datetime, pkl: bool = True,
               folder: Path = DATA_PATH / "pv_live"):
    """
    Code copied/pasted from https://solarstations.org/station_network_pvlive.html

    Retrieve ground measured irradiance data from the PV-Live network.

    The PV-Live network consists of 40 solar irradiance measurement stations
    across the German state of Baden-Württemberg. All stations measure global
    horizontal irradiance and temperature with a pyranometer, and global tilted
    irradiance in east, south, and west direction with tilt angles of 25° with
    three photovoltaic reference cells in minute resolution [1]_.

    Data is available from Zenodo [2]_.

    Parameters
    ----------
    station: int
        Station number (integer). All stations can be requested by specifying
        station='all'.
    start: datetime-like
        First day of the requested period
    end: datetime-like
        Last day of the requested period

    Returns
    -------
    data: DataFrame
        timeseries data from the PV-LIVE measurement network.
    metadata: dict
        metadata (not currently available).

    Warns
    -----
    UserWarning
        If one or more requested files are missing a UserWarning is returned.

    Notes
    -----
    Data is returned for the entire months between and including start and end.

    Examples
    --------
    >>> # Retrieve two months irradiance data PV-Live station 1
    >>> data, metadata = get_pvlive(station=1,  # doctest: +SKIP
    >>>     start=pd.Timestamp(2021,1,1), end=pd.Timestamp(2021,2,28),   # doctest: +SKIP

    References
    ----------
    .. [1] `High resolution measurement network of global horizontal and tilted solar
        irradiance in southern Germany with a new quality control scheme. Elke Lorenz
        et al. 2022. Solar Energy.
        <https://doi.org/10.1016/j.solener.2021.11.023/>`_
    .. [2] `Zenodo
       <https://doi.org/10.5281/zenodo.4036728>`_
    """  # noqa: E501

    months = pd.date_range(start, end.replace(day=1) + pd.DateOffset(months=1), freq='1M')

    dfs_inter_months = []  # Initialize list for holding dataframes
    for m in tqdm(months, disable=((len(months) < 5) or (pkl))):
        pkl_file = folder / f"{station}_{m.strftime('%Y%m')}.pkl"
        if os.path.exists(pkl_file) and pkl:
            df_month = pd.read_pickle(pkl_file)
        else:
            # Generate URL to the monthly ZIP archive
            url = f"{PVLIVE_BASE_URL}pvlive_{m.year}-{m.month:02}.zip?download=1"
            try:
                remotezip = urllib.request.urlopen(url)
            except urllib.error.HTTPError as e:
                if 'not found' in e.msg.lower():
                    warnings.warn('File was not found. The selected time period is probably '
                                  'outside the available time period')
                    pd.DataFrame([]).to_pickle(pkl_file)
                    continue
                else:
                    raise
            zipinmemory = io.BytesIO(remotezip.read())
            zip = zipfile.ZipFile(zipinmemory)

            dfs_intra_months = []
            for filename in zip.namelist():
                basename = os.path.basename(filename)  # Extract file basename
                # Parse file if extension is file starts wtih 'tng' and ends with '.tsv'
                if basename.startswith('tng') & basename.endswith('.tsv'):
                    # Extract station number from file name
                    station_number = int(basename[6:8])
                    if (station == 'all') | (station == station_number):
                        # Read data into pandas dataframe
                        dfi = pd.read_csv(io.StringIO(zip.read(filename).decode("utf-8")),
                                          sep='\t', index_col=[0], parse_dates=[0])

                        if station == 'all':
                            # Add station number to column names (MultiIndex)
                            dfi.columns = [[station_number] * dfi.shape[1], dfi.columns]
                        # Add dataframe to list
                        dfs_intra_months.append(dfi)
            df_month = pd.concat(dfs_intra_months, axis='columns')

            if pkl:
                df_month.to_pickle(pkl_file)

        dfs_inter_months.append(df_month)
    data = pd.concat(dfs_inter_months, axis='rows').tz_localize("UTC")

    meta = {}

    return data, meta


def load_bsrn_data(start, end, station, user, password, overwrite=False, sat_source: str = "cams_pvlib"):
    """
    Load satellite (CAMS) and in-situ BSRN weather data at an hourly granularity at the BSRN station location.

    This function retrieves satellite data and BSRN in-situ data, processes them,
    and computes additional solar radiation parameters such as the clearness and diffuse indices (kt, kd).

    :param start: Datetime object representing the start date of the data extraction.
    :param end: Datetime object representing the end date of the data extraction.
    :param station: String representing the station identifier. three lower-case letters.
    :param user: String representing the username for accessing BSRN data.
    :param password: String representing the password for accessing BSRN data.
    :param overwrite: Boolean indicating whether to overwrite existing data (default is False).
    :param sat_source: What satellite provider ? "cams_pvlib" as only option for now

    :return: Tuple containing processed satellite data (DataFrame), processed BSRN data (DataFrame), and solar position data (DataFrame).
    """
    lat, lon, alt = bsrn_lat_long_alt(station)

    if sat_source == "cams_pvlib":
        sat_data = cams_data_pvlib(lat, lon, alt, start, end).tz_convert('CET')

    # Get BSRN
    insitu_data = process_bsrn(station=station, start=start, end=end, username=user, password=password,
                               resample_freq="H", overwrite=overwrite, filtered=True).tz_convert('CET')
    insitu_data = insitu_data.reindex(sat_data.index)

    # Get hourly solar position
    p_col = sat_data["pressure_pa"] if "pressure_pa" in sat_data.columns else None
    solar_position = solarpos(sat_data.index, lat, lon, alt, ta=None, p=p_col)

    # Indices
    sat_data["kt"] = get_kt(sat_data["ghi"], lat, lon, alt).clip(lower=0)
    sat_data["kd"] = erbs_simple(sat_data["kt"]).clip(lower=0, upper=1)
    sat_data["kb"] = 1 - sat_data["kd"]

    # Recalculate the horizontal components according to Erbs model
    sat_data["dhi"] = sat_data["kd"] * sat_data["ghi"]
    sat_data["bhi"] = sat_data["ghi"] - sat_data["dhi"]
    sat_data["dni"] = dni(sat_data["ghi"], sat_data["dhi"], solar_position["zenith"].dropna())

    if not insitu_data["ghi"].dropna().empty:
        filter = (insitu_data["ghi"] > 0) & (sat_data["ghi"] > 0)
        insitu_data.loc[filter, "kd"] = (insitu_data.loc[filter, "dhi"] / insitu_data.loc[filter, "ghi"])
        insitu_data["kt"] = get_kt(insitu_data.loc[filter, "ghi"], lat, lon, alt).clip(lower=0)

        # Make sure BHI = GHI - DHI
        # (Never really studied in the following parts, since it is kd and kt that are investigated)
        insitu_data["bhi"] = (insitu_data["ghi"] - insitu_data["dhi"]).clip(lower=0)

    return sat_data, insitu_data, solar_position


def load_bsrn_welev(start, end, station, user, password, sat_source: str = "cams_pvlib"):
    lat, long, alt = bsrn_lat_long_alt(station)
    sat_data, insitu_data, solar_position = load_bsrn_data(start, end, station, user, password,
                                                           sat_source=sat_source)
    _, _, _, elevation = get_kt(sat_data["ghi"], lat, long, alt, return_ghiextra_elev=True)
    return sat_data, insitu_data, solar_position, elevation


def filter_pyrano_d(insitu, filter_g, aoi_d, column_poag="Gg_si_south"):
    """Apply filters to pyranos (PV-live specific)"""
    df_d = insitu[filter_g & (aoi_d < 70) & (insitu[column_poag] > 50)]
    df_d_15min = df_d.resample("15min").mean()[df_d["flag_Gg_pyr"].resample("15min").count() >= 13]  # 85%
    insitu_d = df_d_15min.resample("60min").mean()[df_d_15min["flag_Gg_pyr"].resample("60min").count() >= 3]  # 75%
    return insitu_d


def filter_pyrano(insitu, lat, long, alt):
    # Solar position and physical limits
    solar_position_1m = get_solar_position_1m(insitu.index, lat, long, alt, None, None, pkl=True)
    ghi_limit, _, _ = get_irr_limits(insitu.index, lat, long, alt, resample_freq="1min")

    # Calculate angle of incidence/GHI limits for filtering purposes
    solar_zenith_1m = solar_position_1m["apparent_zenith"].fillna(solar_position_1m["zenith"]).reindex(insitu.index)
    solar_azimuth_1m = solar_position_1m["azimuth"].reindex(insitu.index)
    aoi_s = aoi(25, 180, solar_zenith_1m, solar_azimuth_1m).reindex(insitu.index)
    aoi_e = aoi(25, 90, solar_zenith_1m, solar_azimuth_1m).reindex(insitu.index)
    aoi_w = aoi(25, 270, solar_zenith_1m, solar_azimuth_1m).reindex(insitu.index)

    # Horizontal has a special filter
    filter_g = (insitu["Gg_pyr"] > 50) & (insitu["flag_Gg_pyr"] == 0) & (insitu["flag_shading"] == 0)
    df_g = insitu[filter_g & (insitu["flag_T_pyr"] == 0) & (insitu["Gg_pyr"] > ghi_limit["lower"]) & (
            insitu["Gg_pyr"] < ghi_limit["upper"])]
    df_15min = df_g.resample("15min").mean()[df_g["flag_Gg_pyr"].resample("15min").count() >= 13]  # 85%
    insitu_h = df_15min.resample("60min").mean()[df_15min["flag_Gg_pyr"].resample("60min").count() >= 3]  # 75%

    # Other tilted orientations have the same filter
    insitu_s = filter_pyrano_d(insitu, filter_g, aoi_s, "Gg_si_south")
    insitu_e = filter_pyrano_d(insitu, filter_g, aoi_e, "Gg_si_east")
    insitu_w = filter_pyrano_d(insitu, filter_g, aoi_w, "Gg_si_west")

    return insitu_h, insitu_s, insitu_e, insitu_w


def add_kpoa(insitu_s, insitu_e, insitu_w, sat_data, lat, long, alt):
    insitu_s["kpoa"], insitu_s["poa_extra"], insitu_s["aoi"] = \
        get_kpoa(insitu_s.index, lat, long, alt, 25, 180, poa=insitu_s["Gg_si_south"])
    insitu_e["kpoa"], insitu_e["poa_extra"], insitu_e["aoi"] = \
        get_kpoa(insitu_e.index, lat, long, alt, 25, 90, poa=insitu_e["Gg_si_east"])
    insitu_w["kpoa"], insitu_w["poa_extra"], insitu_w["aoi"] = \
        get_kpoa(insitu_w.index, lat, long, alt, 25, 270, poa=insitu_w["Gg_si_west"])

    sat_data["kpoa_s"], sat_data["poa_extra_s"], _ = \
        get_kpoa(sat_data.index, lat, long, alt, 25, 180, ghi=sat_data["ghi"])
    sat_data["kpoa_e"], sat_data["poa_extra_e"], _ = \
        get_kpoa(sat_data.index, lat, long, alt, 25, 90, ghi=sat_data["ghi"])
    sat_data["kpoa_w"], sat_data["poa_extra_w"], _ = \
        get_kpoa(sat_data.index, lat, long, alt, 25, 270, ghi=sat_data["ghi"])

    return insitu_s, insitu_e, insitu_w, sat_data


def load_pvlive_data(start: datetime = pd.to_datetime("20200101").tz_localize("CET"),
                     end: datetime = pd.to_datetime("20240101").tz_localize("CET"),
                     station: int = 1,
                     sat_source: str = "cams_pvlib"):
    """
    Load satellite (CAMS) and in-situ PV-live weather data at an hourly granularity at the PV-live station location.

    :param start: Datetime object representing the start date of the data extraction.
    :param end: Datetime object representing the end date of the data extraction.
    :param station: Station identifier. decimal.
    :param sat_source: What satellite provider ? "cams_pvlib" as only option for now

    :return: Tuple containing processed satellite data (DataFrame), processed BSRN data (DataFrame), and solar position data (DataFrame).
    """
    # Get insitu data
    insitu, meta = get_pvlive(station=station, start=start, end=end)
    insitu = insitu.tz_convert("CET")

    # Get satellite data
    lat, long, alt = pvlive_lat_long_alt(station)
    if sat_source == "cams_pvlib":
        sat_data = cams_data_pvlib(lat, long, alt, start, end).tz_convert('CET')

    # Hourly solar position
    solar_position = solarpos(sat_data.index, lat, long, alt, None, None)  #
    solar_position = filter_dates(solar_position, start, end)

    # Apply filters
    insitu_h, insitu_s, insitu_e, insitu_w = filter_pyrano(insitu, lat, long, alt)

    #### Filter on dates
    sat_data = filter_dates(sat_data, start, end)
    insitu_h = filter_dates(insitu_h, start, end)
    insitu_s = filter_dates(insitu_s, start, end)
    insitu_e = filter_dates(insitu_e, start, end)
    insitu_w = filter_dates(insitu_w, start, end)

    # Add kpoa components
    insitu_s, insitu_e, insitu_w, sat_data = add_kpoa(insitu_s, insitu_e, insitu_w, sat_data, lat, long, alt)

    return sat_data, insitu_h, insitu_s, insitu_e, insitu_w, solar_position
