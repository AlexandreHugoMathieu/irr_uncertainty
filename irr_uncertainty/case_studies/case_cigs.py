import matplotlib.pyplot as plt
import pandas as pd

from irr_uncertainty.config import DATA_PATH
from irr_uncertainty.models.uncertainty_model import poa_scns
from irr_uncertainty.data.solar_data import solarpos
from irr_uncertainty.data.irr_data import cams_data_pvlib


def CIGS_data(start, end):
    file_path = str(DATA_PATH / f"SCHWEIZER_Single.txt")
    data = pd.read_csv(file_path, index_col=0)

    data.index = pd.to_datetime(data.index)
    data =data.tz_localize(None)
    data = data.tz_localize("CET", ambiguous=False)
    data = data.resample("H").mean()
    data = data.loc[(data.index >= start) & (data.index < end)]

    return data


lat, long = 43.617, 7.05
lon = long
alt = 150

start = pd.to_datetime("20220701").tz_localize("CET")
end = pd.to_datetime("20220901").tz_localize("CET")

sat_data = cams_data_pvlib(lat, long, alt, start, end)
ghi = sat_data["ghi"]
poa_qs = poa_scns(lat, long, alt, 25, 180, sat_data["ghi"], quantiles=[0.025, 0.5, 0.975], light=False)
data_cigs = CIGS_data(start, end)

factor = poa_qs[0.5].max() / data_cigs['Gi'].max()
poa_insitu = (data_cigs['Gi'].tz_convert("CET")*factor)
#
# poa_qs.tz_convert("CET").plot()
# poa_insitu.plot(color="black", marker=".")
# plt.legend()




# 1. Identify the 'out of bounds' timesteps
# Assuming your index is already a DatetimeIndex from our previous step
poa_insitu = poa_insitu.reindex(poa_qs.index).fillna(0)
lower = poa_qs[0.025].reindex(poa_insitu.index)
upper = poa_qs[0.975].reindex(poa_insitu.index)
mask = ((poa_insitu < lower) | (poa_insitu > upper)) & (sat_data["ghi"].reindex(poa_insitu.index) > 50)


# 2. Plotting
plt.figure(figsize=(12, 6))

# Plot the actual DHI data
plt.plot(poa_insitu.index, poa_insitu, label='Actual POA', color='black', lw=1, marker=".")

# Plot the quantile boundaries for reference
plt.fill_between(poa_insitu.index, lower, upper, color='gray', alpha=0.5, label='95% Interval')

# 3. Add red zones for the 'Out of Bounds' timesteps
# We iterate through the index to find where our mask is True
out_of_bounds_idx = poa_insitu.index[mask]

for ts in out_of_bounds_idx:
    plt.axvspan(ts, ts+pd.Timedelta(hours=1), color='red', alpha=0.3)

# Clean up the chart
plt.title('POA vs 95% Confidence Interval')
plt.ylabel('POA [W/m²]')
plt.legend()
plt.show()


solar_position = solarpos(sat_data.index, lat, long, alt)

poa_qs= poa_qs.reindex(poa_insitu.index)
solar_position = solar_position.reindex(poa_insitu.index)
df = pd.DataFrame(columns=["95%", "elevation", "azimuth"])
filter = solar_position["elevation"]>0
for idx in solar_position["elevation"].loc[filter].index:
    df.loc[idx, "elevation"] = solar_position.loc[idx, "elevation"]
    df.loc[idx, "azimuth"] =solar_position.loc[idx, "azimuth"]

    bool = (poa_qs.loc[idx, 0.025] < poa_insitu.loc[idx]) & (poa_qs.loc[idx, 0.975] > poa_insitu.loc[idx])
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

