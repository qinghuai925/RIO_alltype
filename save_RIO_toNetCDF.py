
def save_toNetcdf(riodata,icedata,configs):

    import numpy as np
    import datetime
    import os
    
    # RIOmethod as string
    riomethod=[i for i in configs['RIOmethod'] if configs['RIOmethod'][i]==True][0]
    # Create the output filename
    if configs['output']['filename_automatic']==True:
        outfile=configs['output']['output_folder']+'/RIO-'+riomethod+'_'+os.path.basename(configs['ice_filename']).replace('*','XXX').replace('?','X')
    else:
        outfile=configs['output']['output_folder']+'/'+configs['output']['filename']
    
    # Make an empty dataset with basic coordinates for the netcdf file, copied from the icedata-file
    timespace_coords=[configs["coordinates"]["lon_name"], configs["coordinates"]["lat_name"], configs["coordinates"]["time_name"]]
    riods=icedata[timespace_coords] # Create an "empty" DataSet with same time and space dimentions as in icedata

    # Add coordinate for shipclasses
    shipclasses = configs['output']['shipclasses']
    riods.coords["shipclass"] =  np.array(configs['output']['shipclassNUMs'], dtype='int32') # Would be nice with ship classes as string values, but cdo cannot handle that. Therefore we use integer values.
    
    # Add the RIO variable with dimensions, attributes and data from riodata
    if configs['coordinates']['ncat']==1:
        rio_dims = (icedata.siconc.dims[0],'shipclass',icedata.siconc.dims[1],icedata.siconc.dims[2]) # (time, shipclass, y, x)
    elif configs['coordinates']['ncat']>1:    
        rio_dims = (icedata.siitdconc.dims[0],'shipclass',icedata.siitdconc.dims[2],icedata.siitdconc.dims[3]) # (time, shipclass, y, x)
    riods["RIO"] = (rio_dims, riodata)
    rio_attrs={'long_name':'Risk Index Outcome (POLARIS)',
                'units':'[]',
                'comment':"Ship classes included in this file: "+', '.join(shipclasses),
                'comment2':"Meaning of shipclass-dimension: 1:PC1, 2:PC2, 3:PC3, 4:PC4, 5:PC5, 6:PC6, 7:PC7, 10:1ASuper, 11:1A, 12:1B, 13:1C, 20:noclass" 
                }
    riods.RIO.attrs=rio_attrs

    ## Try to correct the attribute 'coordinates' of the RIO variable in netcdf. For DMI data, xarray's automatic does it wrongly. But this doesn't work:
    #rio_coords=configs["coordinates"]["lon_name"] +' '+ configs["coordinates"]["lat_name"] +' shipclass '+ configs["coordinates"]["time_name"]
    #riods["RIO"] = (rio_dims, riofinal, {'coordinates':rio_coords})
    #riods.RIO.encoding["coordinates"]=rio_coords
    
    # Set global attributes of the netcdf file
    riods.attrs={
    'title':configs['output']['title'],
    'histroy':'Created by RIOengine_NOCOS.py on '+datetime.datetime.today().strftime("%Y-%m-%d"),
    'description':'Used RIO calculation method: '+riomethod+'; number of ice categories: '+str(configs['coordinates']['ncat']),
    'institution':"Danish and Finnish Meteorological Institutes, DMI/FMI",
    'references':'https://www.nautinst.org/uploads/assets/uploaded/2f01665c-04f7-4488-802552e5b5db62d9.pdf'
    }
    
    # Write netcdf file
    riods.to_netcdf(outfile, unlimited_dims=configs["coordinates"]["time_name"], encoding={'RIO':{'_FillValue':np.nan},configs["coordinates"]["time_name"]:{"dtype": "double", 'units': "days since 1900-01-01 00:00:00"}})
    print("RIO output written to: "+outfile)
