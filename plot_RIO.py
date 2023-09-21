def PLOT(configs):
    import os
    import numpy as np
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from matplotlib.colors import LinearSegmentedColormap
    import xarray as xr
    for ship_class in configs['output']['shipclasses']:
        # Construct the full path for the ship class directory
        ship_class_folder = os.path.join(configs['output']['output_folder'], "plots", ship_class)

        # Check if the directory doesn't exist and create it if needed
        if not os.path.exists(ship_class_folder):
            os.makedirs(ship_class_folder)
    riomethod=[i for i in configs['RIOmethod'] if configs['RIOmethod'][i]==True][0]
    if configs['output']['filename_automatic']==True:
        filename=configs['output']['output_folder']+'/RIO-'+riomethod+'_'+os.path.basename(configs['ice_filename']).replace('*','XXX').replace('?','X')
    else:
        filename=configs['output']['output_folder']+configs['output']['filename']
    
    f = xr.open_dataset(filename, decode_times=True, use_cftime=True)
    #If the area is too big (including 2 poles or so), the land maks is lost for some reason
    jifrom = 0
    jito = -1
    riomapAGI2 = LinearSegmentedColormap.from_list('riomap', [(0. , 'red'),
                                                        (   0.0001, 'yellow'),
                                                        (   0.5, 'yellow'),
                                                        (   0.5001, 'lightgreen' ),
                                                        (   0.9, 'green' ),
                                                        (    1., (0.0,0.45,0.45))])            
    for i in range(len(f.RIO)):
        plt.figure(18,figsize=(11,8))
        plt.clf()

        #m = Basemap(projection='laea', width =5000*400, height=5000*200, lat_ts=81., lat_0=81.05, lon_0=9.2, resolution='i')  resolution: c l i h f
        #m = Basemap(projection='npstere',boundinglat=50,lon_0=0,resolution='c')
        #Reapply mask:
        riotoplot=np.array(f.RIO[i,0,:,:])
        lonrio = np.array(f[configs['coordinates']['lon_name']][:, :])
        latrio = np.array(f[configs['coordinates']['lat_name']][:, :])
        datatoplot = np.ma.array(riotoplot[:,jifrom:jito],mask=np.isnan(riotoplot[:,jifrom:jito]))  
        lontoplot = lonrio[:,jifrom:jito]
        lattoplot = latrio[:,jifrom:jito]
        print('lonshape:',lontoplot.shape)
        print('lonmin:',lontoplot.min())
        print('lonmax:',lontoplot.max())
        print('latshape:',lattoplot.shape)
        print('latmin:',lattoplot.min())
        print('llatmax:',lattoplot.max())
        ax = plt.axes(projection=ccrs.Orthographic(central_longitude=0.0, central_latitude=90, globe=None))
        ax.set_extent([-180, 180, 65, 90], crs=ccrs.PlateCarree())# Set the desired geographic extent
        parallels = ax.gridlines(crs=ccrs.PlateCarree(),draw_labels=True,linewidth=0.5,color='black',alpha=1,linestyle='--')
        parallels.ylocator = plt.FixedLocator(range(40, 90, 10))
        parallels.xlocator = plt.FixedLocator(range(-180, 180, 30))
        parallels.xlabel_style = {'fontsize': 16}
        parallels.ylabel_style = {'fontsize': 16}
        parallels.top_labels = False
        pcolorhandle2 = ax.pcolormesh(lontoplot, lattoplot, datatoplot, zorder=2,cmap=riomapAGI2,vmin=-10,vmax=10,transform=ccrs.PlateCarree(),linewidth=0,rasterized=True)
        ax.add_feature(cfeature.COASTLINE,zorder=3)
        cbar = plt.colorbar(pcolorhandle2, shrink=0.7, pad=0.1, aspect=15, extend='both')
        cbar.ax.tick_params(labelsize=16)
        cbar.set_label('RIO', fontsize=16)
        plt.text(2750000,-2500000,configs['Plot']['title'],fontsize=11)    


        #Plot     
        #                pcolorhandle1 = plt.pcolormesh(elonplot,elatplot,tmaskori[2:-2,2:-2],zorder=2, rasterized=True,cmap=eismapAGI)  #zorder 2 heisst, dass es NACH dem HAMSOM patch geplottet werden soll dass es NACH dem HAMSOM patch geplottet werden soll
        plt.title('Ship class: '+configs['output']['shipclasses'][0]+', Forecast for '+configs['Dates']['targetdates'][i])
        plt.savefig(configs['output']['output_folder']+'plots/'+configs['output']['shipclasses'][0]+'/'+configs['Datasource']+'_RIO_'+configs['output']['shipclasses'][0]+'-for-'+configs['Dates']['targetdates'][i]+'_pdf', dpi=None, facecolor='w', edgecolor='w', format='pdf',transparent=False,  pad_inches=0.1, bbox_inches='tight')
        #put this in to a plot function.py read config outfile ship class basedate and target date to fit in the title and filename
        

