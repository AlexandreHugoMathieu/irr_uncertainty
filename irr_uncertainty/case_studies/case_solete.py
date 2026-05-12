import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from irr_uncertainty.config import DATA_PATH, Config
from irr_uncertainty.models.uncertainty_model import irrh_scenarios_v2
from irr_uncertainty.data.solar_data import solarpos
from irr_uncertainty.data.irr_data import cams_data_pvlib


def SOLETE_data(start, end, resolution="1min"):
    """https://figshare.com/articles/dataset/The_SOLETE_dataset/17040767?file=40097803"""

    file_path = str(DATA_PATH / f"SOLETE_Pombo_{resolution}.h5")
    data = pd.read_hdf(file_path)

    data = data.tz_localize("UTC")
    data = data.loc[(data.index >= start) & (data.index < end)]

    return data


def SOLETE_data_hourly(start, end, resolution="1min"):
    """https://figshare.com/articles/dataset/The_SOLETE_dataset/17040767?file=40097803"""

    data = SOLETE_data(start - pd.Timedelta(hours=1), end, resolution)

    data = data.resample("h").mean().shift(1)
    data = data.loc[(data.index >= start) & (data.index < end)]

    return data


lat, long = 55.6867, 12.0985
alt = 50

start = pd.to_datetime("20180601").tz_localize("CET")
end = pd.to_datetime("20190801").tz_localize("CET")

sat_data = cams_data_pvlib(lat, long, alt, start, end)
ghi_qs, dhi_qs, bhi_qs = irrh_scenarios_v2(lat, long, alt, sat_data["ghi"], quantiles=[0.025, 0.975], light=True)
data_solete = SOLETE_data_hourly(start, end, resolution="1min").resample("H").mean()
ghi_insitu = (data_solete['GHI[kW1m2]'].tz_convert("CET") * 1000)
# data_solete = data_solete.shift(-1)


ghi_qs.tz_convert("CET").plot()
ghi_insitu.plot(color="black", marker=".")
plt.legend()

solar_position = solarpos(sat_data.index, lat, long, alt)

df = pd.DataFrame(columns=["95%", "elevation", "azimuth"])
filter = solar_position["elevation"]>0
for idx in solar_position["elevation"].loc[filter].index:
    df.loc[idx, "elevation"] = solar_position.loc[idx, "elevation"]
    df.loc[idx, "azimuth"] =solar_position.loc[idx, "azimuth"]

    bool = (ghi_qs.loc[idx, 0.025] < ghi_insitu.loc[idx]) & (ghi_qs.loc[idx, 0.975] > ghi_insitu.loc[idx])
    df.loc[idx, "95%"] = bool


colors = df['95%'].map({True: 'white', False: 'red'})

# 3. Create the plot
plt.figure(figsize=(10, 6))

plt.scatter(
    df['azimuth'],
    df['elevation'],
    c=colors,
    alpha=0.6,      # Transparency
    s=100,          # Size of dots
    edgecolors='black'  # White border for better visibility
)

# 4. Formatting
plt.xlabel('Azimuth (°)')
plt.ylabel('Elevation (°)')
plt.title('Solar Position Scatter Plot')
plt.grid(True, linestyle='--', alpha=0.3)


plt.legend()

plt.show()

