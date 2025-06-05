# irr_uncertainty

This repo enables to generate irradiance (horizontal and plane-of-array) 95%-intervals anywhere in Europe with latitude and longitude between [35°,60°] and [-20°,40°] respectively, excluding atypical locations such as high-altitude snowy locations.

The intervals are generated with the basis of satellite (CAMS) data.

## Package

This repo can be used with Python 3.9 [python docs](https://docs.python.org/3/using/unix.html#getting-and-installing-the-latest-version-of-python) as a package by running the following commands.

```bash
pip install irr_uncertainty
```

### Example

The following lines generate Monte Carlo simulations to obtain the 95% interval for one orientation.

```bash
import pandas as pd

from irr_uncertainty.data.irr_data import cams_data_pvlib
from irr_uncertainty.data.solar_data import solarpos
from irr_uncertainty.models.uncertainty_model import irrh_scenarios, transpo_scenarios

start = pd.to_datetime("20220812").tz_localize("UTC")
end = pd.to_datetime("20220816").tz_localize("UTC")
n_scenarios = 1000

# Grenoble, FRANCE
lat = 45.16
long = 5.72
alt = 212

# Installation's orientation
tilt = 25
azimuth = 180

# Fetch CAMS data and get hourly solar position (with same convention)
sat_data = cams_data_pvlib(lat, long, alt, start, end)
solar_position = solarpos(sat_data.index, lat, long, alt).shift(-1)

# Compute Monte Carlo simulations for horizontal plans
ghi_scns, dhi_scns, bhi_scns = irrh_scenarios(lat, long, alt, solar_position, sat_data["ghi"],
                                              n_scenarios=n_scenarios)

# Generate Monte Carlo simulations for one orientation
poa_scns_s, _, _, _ = \
    transpo_scenarios(tilt, azimuth, lat, long, alt, solar_position, ghi_scns, dhi_scns, n_scenarios=n_scenarios)

# Plot GHI and POA intervals
import matplotlib.pyplot as plt
from irr_uncertainty.utils import q_plot
fig, axes = plt.subplots(2, 1, figsize=(8, 5), sharex=True, sharey=True)
axes[0] = q_plot(ghi_scns.loc[:], color="blue", ax=axes[0], label="GHI")
axes[1] = q_plot(poa_scns_s.loc[:], color="seagreen", ax=axes[1], label="POA-south")
```

Then, typical intervals can be computed by following the notebook "notebooks/irr_interval_generation_example.ipynb" with more details as in the Figure below.

![Illustration quantiles](https://raw.githubusercontent.com/AlexandreHugoMathieu/irr_uncertainty/refs/heads/main/irr_uncertainty/local_data/irr_data/images/illustration_poa_all_quantiles.png)


### Mandatory credentials

A secret file "secret.ini" should be placed in the "irr_uncertainty/local_data/" folder with the credentials for:

- [Soda-pro](https://www.soda-pro.com/help/cams-services/cams-radiation-service/automatic-access): for the CAMS data - to generate 95% interval for any location.
- [BSRN](https://bsrn.awi.de/data/data-retrieval-via-ftp/) with a email request - to access BSRN station data and recreate the methodology Figures.

The "secret.ini" should have this format (replacing "your_user_bsrn", "your_password_bsrn", "your_user_cams"):

```
[BSRN]
user = your_user_bsrn
password = your_password_bsrn

[CAMS]
user = your_user_cams
```

### Command files

Two command files ease the creation of virtual environment and the execution of jupyter notebooks:

- create_env.cmd: Create a virtual environment and installed all the required packages
- notebook_start.cmd: Create a kernel to link with the virtual environment in order to use within the notebook and open the jupyter notebook

## Contact

Created by [@Alex](https://alexandrehugomathieu.github.io/alexandremathieu.github.io//) - feel free to contact me for any concerns and happy to receive feedbacks !
