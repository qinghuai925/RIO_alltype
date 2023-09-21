Installation
#############

Software requirements:
Python 3.9 with following packages:
  - numpy
  - xarray (including dask, netCDF4 and bottleneck)
  - pyyaml
  - schedule
  - matplotlib

Use the provided file conda-env_NOCOS-RIO.yml to install a suitable conda environment.

Prepare data
############
ECMWF S2S can be accessed through ECMWF's File Storage system(ECFS). One can use teleport SSH access. 
https://confluence.ecmwf.int/display/UDOC/Teleport+SSH+Access+-+Linux+configuration
After slected file has been saved to personal folder on ECFS, run Download_S2S_from_ECFS.py(Trim_S2S_ice_data.py should be contained in the same directory) if other source S2S data are avliable, this can be skipped.
Copernicus can be directly downloaded from ftp server, the download and cropping of the data is already included in RIOengine_NOCOS.py.
DMI data are obtained from DMI colleague.

Select datatype in engine
############
There are currently three data types: ECMWF_S2S, COpernicus, DMI. Set the datatype in use to True in RIOengine_NOCOS.py. If plots are needed, set plot to be true, else set it to false.

Running
############
1) Adjust the configuration file config_RIOcalc_default.yml or make a new one and provide its name inside RIOengine_NOCOS.py
typically for ECMWFS2S data the config filename is config_RIOcalc_ECMWF.yml, for copernicus data is config_RIOcalc_Copernicus.yml and for DMI data is config_RIOcalc_DMI-HYCOM-CICE.yml 
2) conda activate rioNOCOS
3) python3 RIOengine_NOCOS.py

Info
#############

We use variable names as defined by CMIP6/CMOR:
siconc
sithick
sivol
siitdconc
siitdthick
siage
sisali
(See explanations in config_RIOcalc_default.yml)


