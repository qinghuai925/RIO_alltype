# -*- coding: utf-8 -*-
"""

@author: Andrea Gierisch, DMI
"""
# Load RIO functions
from read_config import read_configfile
from read_ice_data import read_ice_data
from save_RIO_toNetCDF import save_toNetcdf
from calculate_RIO import calcRIO_multicat
from calculate_RIO import calcRIO_monocat
from plot_RIO import PLOT
from Download_Copernicus_from_ftp import Download_fromFTP


ECMWF_S2S     = False
Copernicus    = False
DMI           = True
RIOplot       = True

# Read config file
#configs=read_configfile() # Reads config_RIOcalc_default.yml
if ECMWF_S2S:
    configs=read_configfile('config_RIOcalc_ECMWF.yml')
elif DMI:
    configs=read_configfile('config_RIOcalc_DMI-HYCOM-CICE.yml')
else:
    configs=read_configfile('config_RIOcalc_Copernicus.yml')
    Download_fromFTP(configs)
icedata=read_ice_data(configs)
# Calculate RIO
if configs['multiCAT']==True:
    riodata=calcRIO_multicat(icedata,configs)
elif configs['multiCAT']==False:
    riodata=calcRIO_monocat(icedata,configs)
# Save RIO data to netcdf file
save_toNetcdf(riodata,icedata,configs)
# plot RIO data
if RIOplot:
    PLOT(configs)



