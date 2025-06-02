# irr_uncertainty

This repo enables to generate irradiance (horizontal and plane-of-array) 95%-intervals anywhere in Europe with latitude and longitude between [35°,60°] and [-20°,40°] respectively, excluding atypical locations such as high-altitude snowy locations.

The intervals are generated based on satellite (CAMS) data.

## Package

This repo can be used as a package by running the following commands.

```bash
pip install irr_uncertainty
```

### Example

The following lines allow to generate  

```bash
import pandas as pd
from irr_uncertainty import

lat =
long =
start =
end = 


```

### Command files

Two command files ease the creation of virtual environment and the execution of jupyter notebooks:

- create_env.cmd: Create a virtual environment and installed all the required packages
- notebook_start.cmd: Create a kernel to link with the virtual environment in order to use within the notebook and open the jupyter notebook



## Setup

Install Python 3.9 [python docs](https://docs.python.org/3/using/unix.html#getting-and-installing-the-latest-version-of-python)

### Virtual Environment and depedenciies

Instructions for setting up a virtual environment can be found in the [python docs](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)

Once the virtual environment is setup and running, install dependencies by running:

```bash
pip install -r requirements.txt
```


## Contact
Created by [@Alex](https://alexandrehugomathieu.github.io/alexandremathieu.github.io//) - feel free to contact me!
