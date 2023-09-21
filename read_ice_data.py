
#from read_config import read_configfile
#configs=read_configfile()

######################################################

def read_ice_data(configs):
    import xarray as xr
    icedataraw = xr.open_mfdataset(configs['ice_filename']) # Will try to infer automatically in which dimension (e.g. time) the files should be concatenated.
#    icedataraw = xr.open_mfdataset(configs['ice_filename'], concat_dim=configs['coordinates']['time_name'])
      
    # Sanity checks
    ######################
    # ToDO: Check if all provided variable names actually exist in icedataraw
    # to be implemented
    
    # Check if NCAT matches to dimensions in icedataraw:
    if configs['multiCAT']:
        # Check siitdconc
        if icedataraw[configs['variables']['siitdconc_name']][configs['coordinates']['ncat_name']].shape[0] != configs['coordinates']['ncat']:
            raise RuntimeError("The given number for NCAT doesn't match the dimension 'ncat_name' for siitdconc_name.")
        # Check siitdthick or siitdvol
        if configs['Lvol']:
            if icedataraw[configs['variables']['siitdvol_name']][configs['coordinates']['ncat_name']].shape[0] != configs['coordinates']['ncat']:
                raise RuntimeError("The given number for NCAT doesn't match the dimension 'ncat_name' for siitdvol_name.")
        else: # Lvol=False
            if icedataraw[configs['variables']['siitdthick_name']][configs['coordinates']['ncat_name']].shape[0] != configs['coordinates']['ncat']:
                raise RuntimeError("The given number for NCAT doesn't match the dimension 'ncat_name' for siitdthick_name.")
    
    
    
    # Calculate ice thickness if only ice volume is given (thick=vol/conc)
    #########################################
    if configs['Lvol']:
        if configs['multiCAT']:
            icedataraw['siitdthick']=icedataraw[configs['variables']['siitdvol_name']]/icedataraw[configs['variables']['siitdconc_name']]
#            icedataraw['siitdthick'][icedataraw[configs['variables']['siitdconc_name']]==0] = 0.
            icedataraw['siitdthick']=icedataraw['siitdthick'].fillna(0.)
            configs['variables']['siitdthick_name']='siitdthick'
        elif configs['multiCAT']==False:
            icedataraw['sithick']=icedataraw[configs['variables']['sivol_name']]/icedataraw[configs['variables']['siconc_name']]
            configs['variables']['sithick_name']='sithick'
    
    
    ## Select relevant variables from input file(s) and assign them standard names
    ##########################################
    if configs['multiCAT']:
        relevantvars_list=[configs['variables']['siitdconc_name'], configs['variables']['siitdthick_name']]
        rename_vardict={configs['variables']['siitdconc_name']:'siitdconc', configs['variables']['siitdthick_name']:'siitdthick'}
    elif configs['multiCAT']==False:
        relevantvars_list=[configs['variables']['siconc_name'], configs['variables']['sithick_name']]
        rename_vardict={configs['variables']['siconc_name']:'siconc', configs['variables']['sithick_name']:'sithick'}
    
    if configs['RIOmethod']['Lage']:
        relevantvars_list.append(configs['variables']['siage_name'])
        rename_vardict.update({configs['variables']['siage_name']:'siage'})
    
    if configs['RIOmethod']['Lsal']:
        relevantvars_list.append(configs['variables']['sisali_name'])
        rename_vardict.update({configs['variables']['sisali_name']:'sisali'})
       
    icedata = icedataraw[relevantvars_list].rename(rename_vardict)
    
    return(icedata)
