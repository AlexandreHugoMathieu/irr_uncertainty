import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from irr_uncertainty.config import DATA_PATH, Config
from irr_uncertainty.models.uncertainty_model import irrh_scenarios_v2
from irr_uncertainty.data.solar_data import solarpos
from irr_uncertainty.data.irr_data import cams_data_pvlib


def girona_data(start, end):
    """https://figshare.com/articles/dataset/The_SOLETE_dataset/17040767?file=40097803"""

    file_path = str(DATA_PATH / f"dhi_girona.txt")
    data = pd.read_csv(file_path)

    data.index = pd.to_datetime(data[['YEAR [UTC]', 'MONTH [UTC]', 'DAY [UTC]', 'HOUR [UTC]']]
        .rename(columns={
        'YEAR [UTC]': 'year',
        'MONTH [UTC]': 'month',
        'DAY [UTC]': 'day',
        'HOUR [UTC]': 'hour'
    }))

    data = data.tz_localize("UTC")
    data['DIF [kJ/m²]'] = pd.to_numeric(data['DIF [kJ/m²]'], errors='coerce')

    data["Wh"] = data['DIF [kJ/m²]'] * 1000 / 3600
    data = data.loc[(data.index >= start) & (data.index < end), "Wh"]

    return data

lat, long = 41.96338, 2.83128
alt = 118

start = pd.to_datetime("20160101").tz_localize("CET")
end = pd.to_datetime("20170101").tz_localize("CET")

dhi_insitu = girona_data(start, end)
sat_data = cams_data_pvlib(lat, long, alt, start, end)
ghi_qs, dhi_qs, bhi_qs = irrh_scenarios_v2(lat, long, alt, sat_data["ghi"], quantiles=[0.025, 0.975], light=True)


# 1. Identify the 'out of bounds' timesteps
# Assuming your index is already a DatetimeIndex from our previous step
lower = dhi_qs[0.025].reindex(dhi_insitu.index)
upper = dhi_qs[0.975].reindex(dhi_insitu.index)
mask = ((dhi_insitu < lower) | (dhi_insitu > upper)) & (dhi_insitu > 50)

dhi_insitu.max()
upper.max()


# 2. Plotting
plt.figure(figsize=(12, 6))

# Plot the actual DHI data
plt.plot(dhi_insitu.index, dhi_insitu, label='Actual DHI', color='black', lw=1, marker=".")

# Plot the quantile boundaries for reference
plt.fill_between(dhi_insitu.index, lower, upper, color='gray', alpha=0.2, label='95% Interval')

# 3. Add red zones for the 'Out of Bounds' timesteps
# We iterate through the index to find where our mask is True
out_of_bounds_idx = dhi_insitu.index[mask]

for ts in out_of_bounds_idx:
    plt.axvspan(ts, ts+pd.Timedelta(hours=1), color='red', alpha=0.3)

# Clean up the chart
plt.title('DHI vs 95% Confidence Interval')
plt.ylabel('DHI [W/m²]')
plt.legend()
plt.show()