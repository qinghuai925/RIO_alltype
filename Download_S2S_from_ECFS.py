from read_config import read_configfile
from Trim_S2S_ice_data import Download_fromECFS

# Read config file
#configs=read_configfile() # Reads config_RIOcalc_default.yml
configs=read_configfile('config_RIOcalc_ECMWF.yml')
basedate=configs['Dates']['basedate']
targetdates=configs['Dates']['targetdates']
directory_path = '/home/zhang/Documents/python/'
Download_fromECFS(basedate,targetdates,directory_path)

