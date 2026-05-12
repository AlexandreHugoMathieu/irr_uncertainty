import os
import pandas as pd

from irr_uncertainty.config import DATA_PATH

def stations_bsrn():
    """
    Get irradiance weather in-situ station meta data

    The CSV file is imported from https://github.com/AssessingSolar/solarstations/blob/main/solarstations.csv and stored locally
    """

    path = DATA_PATH / "bsrn_data" / "solarstations_v2.csv"
    if os.path.exists(path):
        data = pd.read_csv(path)
    else:
        data = pd.read_csv(
            "https://raw.githubusercontent.com/AssessingSolar/solarstations/refs/heads/main/solarstations.csv")
        data.to_csv(path)
    return data


def bsrn_lat_long_alt(station):
    """Get Latitude, Longitude and Altitude of BSRN station from its 3-letter abbreviation"""
    meta_data = stations_bsrn()
    meta_station = meta_data.loc[meta_data["Abbreviation"].str.lower() == station].copy().astype("str").iloc[0]
    lat, lon, alt = float(meta_station.loc["Latitude"]), float(meta_station.loc["Longitude"]), float(
        meta_station.loc["Elevation"])
    return lat, lon, alt

def bsrn_name(station):
    """Get BSRN station name from its 3-letter abbreviation"""
    meta_data = stations_bsrn()
    meta_station = meta_data.loc[meta_data["Abbreviation"].str.lower() == station].copy().astype("str").iloc[0]
    name = str(meta_station.loc["Station name"])
    return name


def stations_pv_live():
    """
    PV-live station metadata

    Manually written from https://zenodo.org/records/7311989 (metadatafile)
    """
    stations = pd.DataFrame(
        columns=['ID', 'Station name', 'Latitude', 'Longitude', 'Altitude'],
        data=[
            [1, 'Wendlingen', 48.667, 9.399, 276],
            [2, 'Stuttgart', 48.83, 9.196, 294],
            [3, 'St. Leon-Rot', 49.245, 8.641, 108],
            [4, 'Ketsch', 49.356, 8.532, 102],
            [5, 'Freiburg', 48.009, 7.835, 256],
            [6, 'Mahlberg', 48.28, 7.787, 170],
            [7, 'Murr', 48.968, 9.263, 212],
            [8, 'Fünfstetten', 48.837, 10.773, 504],
            [9, 'Freudenstadt', 48.459, 8.425, 669],
            [10, 'Karlsruhe', 49.008, 8.344, 115],
            [11, 'Oberndorf', 48.298, 8.552, 667],
            [12, 'Ulm', 48.422, 10.006, 552],
            [13, 'Bad Rappenau', 49.268, 9.059, 288],
            [14, 'Offenburg', 48.473, 7.939, 151],
            [15, 'Grünstadt', 49.562, 8.188, 157],
            [16, 'Löffingen', 47.885, 8.4, 745],
            [17, 'Aitrach', 47.927, 10.09, 601],
            [18, 'Neusass', 49.612, 9.35, 441],
            [19, 'Tuttlingen', 47.957, 8.78, 649],
            [20, 'Hechingen', 48.36, 8.966, 490],
            [21, 'Leutkirch', 47.836, 9.988, 648],
            [22, 'Königsbronn', 48.751, 10.169, 637],
            [23, 'Lörrach', 47.613, 7.655, 284],
            [24, 'Ingoldingen', 47.996, 9.699, 573],
            [25, 'Eberbach', 49.465, 8.987, 137],
            [26, 'Zwiefaltendorf', 48.207, 9.513, 523],
            [27, 'Krautheim', 49.396, 9.605, 382],
            [28, 'Pforzheim', 48.899, 8.746, 312],
            [29, 'Weikersheim', 49.457, 9.889, 370],
            [30, 'Konstanz', 47.674, 9.163, 402],
            [31, 'Leibertingen', 48.064, 9.068, 763],
            [32, 'Crailsheim', 49.132, 10.054, 416],
            [33, 'Ravensburg', 47.786, 9.608, 432],
            [34, 'Herdwangen-Schönach', 47.854, 9.137, 660],
            [35, 'Schwäbisch Hall', 49.117, 9.774, 399],
            [36, 'Baden-Baden', 48.787, 8.189, 127],
            [37, 'Neubulach', 48.649, 8.654, 621],
            [38, 'Waldshut-Tiengen', 47.624, 8.255, 345],
            [39, 'Schwäbisch Gmünd', 48.803, 9.8, 326],
            [40, 'Berghülen', 48.455, 9.778, 667]
        ])
    stations = stations.set_index("ID")
    return stations


def pvlive_lat_long_alt(station):
    """Get Latitude, Longitude and Altitude of a PV station from its ID-number"""
    stations = stations_pv_live()
    lat, long, alt = stations.loc[station, "Latitude"], stations.loc[station, "Longitude"], \
                     stations.loc[station, "Altitude"]
    return lat, long, alt
