# -*- coding: utf-8 -*-
"""

@author: Andrea Gierisch, DMI
"""
def calcRIO_monocat(icedata,configs):

    import numpy as np
    import warnings
    import time # for sleep and cputime measurement
    import sys # For flushing of buffer to stdout
    if configs['coordinates']['ncat'] == 1:
        sithick= icedata.sithick
        siconc= icedata.siconc
        nt = icedata[configs['coordinates']['time_name']].shape[0] # Number of time steps
        ny = siconc.shape[1] # Number of grid points in y-direction
        print(siconc.shape,sithick.shape)
        nx = siconc.shape[2] # Number of grid points in x-direction 
    if configs['RIOmethod']['Lage']==True:
        siage= icedata.siage
    elif configs['RIOmethod']['Lsal']==True:
        sisali= icedata.sisali
        #salincat= icedata.sisalicat? # Snippet for multicat salinity
        salMY = 5.0 # [ppt] Limit for discrimination between FY and MY ice
    
    # List of requested ship classes
    shipclasses = configs['output']['shipclasses'] # a subset of ['PC1','PC2','PC3','PC4','PC5','PC6','PC7','1ASuper','1A','1B','1C','noclass']
    # RIO calculation method as string (Lthick, Lage or Lsal)
    riomethod=[i for i in configs['RIOmethod'] if configs['RIOmethod'][i]==True][0]
    
    ##########################################################
    # Function to add open water to the list of ice categories
    ##########################################################
    def addopenwater(siconc,sithick,*argv): # argv could be snthicat
        cww = np.array([1.-np.sum(siconc)]+[x for x in siconc])
        hww = np.array([0.]+[x for x in sithick])
        if len(argv) == 0 :
            return (cww,hww)
        elif len(argv) == 1 :
            sww = np.array([0.]+[x for x in argv[0]])
            return (cww,hww,sww)
        else:
            raise RuntimeError('The function ADDOPENWATER can only be called with 2 or 3 arguments, not with: '+str(len(argv)))    
    ##########################################################
    # Function to calculate RIO for one grid point
    ##########################################################
    # This is according to MSC Circ1
    def polaris(riomethod,shipclass,*argv):
        if riomethod == 'Lthick':
            if not len(argv)==2:
                raise RuntimeError("If riomethod is 'Lthick', then you have to provide 2 additional arguments: CCAT and HCAT.")
            else:
                ccat=argv[0]
                hcat=argv[1]
        elif riomethod == 'Lsal':
            if not len(argv)==3:
                raise RuntimeError("If riomethod is 'Lsal', then you have to provide 3 additional arguments: CCAT, HCAT and Sal.")
            else:
                ccat=argv[0]
                hcat=argv[1]
                sal=argv[2]                    
                # Use this if salinity is given per category
                #salcat=argv[2]                    
        elif riomethod == 'Lage':
            if not len(argv)==3:
                raise RuntimeError("If riomethod is 'Lage', then you have to provide 3 additional arguments: CCAT, HCAT and Age.")
            else:
                ccat=argv[0]
                hcat=argv[1]
                age=argv[2]
                # Use this if iage is given per categrory
                #agecat=argv[2]
        else:
            raise ValueError("riomethod has to be one of ['Lthick', 'Lsal', 'Lage'], not "+riomethod)
                        
        if np.sum(ccat) < 0.99:
            raise RuntimeError("The ice concentrations in CCAT do not sum up to 100%. Did you forget to include the open water fraction?")
    
        if not (shipclass in ['PC1','PC2','PC3','PC4','PC5','PC6','PC7','1ASuper','1A','1B','1C','noclass']):
            raise ValueError("shipclass has to be one of ['PC1','PC2','PC3','PC4','PC5','PC6','PC7','1ASuper','1A','1B','1C','noclass']")
        
        #########################
        # Define BetweenDict used for ice thickness ranges
        # http://joshuakugler.com/archives/30-BetweenDict,-a-Python-dict-for-value-ranges.html
        class BetweenDict(dict):
            def __init__(self, d = {}):
                for k,v in d.items():
                    self[k] = v
        
            def lookup(self, key):
                for k, v in self.items():
                    if k[0] <= key < k[1]:
                        return v
                warnings.warn("Key '%s' is not between any values in the BetweenDict" % key)
                return {np.nan:np.nan} #Andrea: Return a dictionary so that riv.lookup(thi[icl])[shipclass] will raise a KeyError.
                #Andrea: raise KeyError("Key '%s' is not between any values in the BetweenDict" % key)
        
            def setrange(self, key, value):
                try:
                    if len(key) == 2:
                        if key[0] < key[1]:
                            dict.__setitem__(self, (key[0], key[1]), value)
                        else:
                            raise RuntimeError('First element of a BetweenDict key '
                                               'must be strictly less than the '
                                               'second element')
                    else:
                        raise ValueError('Key of a BetweenDict must be an iterable '
                                         'with length two')
                except TypeError:
                    raise TypeError('Key of a BetweenDict must be an iterable '
                                     'with length two')
        
            def __contains__(self, key):
                try:
                    return bool(self[key]) or True
                except KeyError:
                    return False
        # End class BetweenDict
        
        
        ###############################
        # Define Risk Values (RIV) for different riomethods (Adopted from POLARIS Risk Value Table)
        # (We always use RIVs for winter because for decayed/summer conditions the state of decay has to be proven by captain)
        if riomethod == 'Lthick':  
            riv = BetweenDict()
            riv.setrange([0.  ,0.001],{'PC1':3,'PC2':3,'PC3':3,'PC4':3,'PC5':3,  'PC6':3,'PC7':3,  '1ASuper':3,'1A':3,'1B':3,'1C':3,'noclass':3}) # no ice
            riv.setrange([0.001,0.10],{'PC1':3,'PC2':3,'PC3':3,'PC4':3,'PC5':3,  'PC6':2,'PC7':2,  '1ASuper':2,'1A':2,'1B':2,'1C':2,'noclass':1}) # new ice
            riv.setrange([0.10,0.15],{'PC1':3,'PC2':3,'PC3':3,'PC4':3,'PC5':3,  'PC6':2,'PC7':2,  '1ASuper':2,'1A':2,'1B':2,'1C':1,'noclass':0}) # grey ice
            riv.setrange([0.15,0.30],{'PC1':3,'PC2':3,'PC3':3,'PC4':3,'PC5':3,  'PC6':2,'PC7':2,  '1ASuper':2,'1A':2,'1B':1,'1C':0,'noclass':-1}) # grey-white
            riv.setrange([0.30,0.50],{'PC1':2,'PC2':2,'PC3':2,'PC4':2,'PC5':2,  'PC6':2,'PC7':1,  '1ASuper':2,'1A':1,'1B':0,'1C':-1,'noclass':-2}) # thin FY 1
            riv.setrange([0.50,0.70],{'PC1':2,'PC2':2,'PC3':2,'PC4':2,'PC5':2,  'PC6':1,'PC7':1,  '1ASuper':1,'1A':0,'1B':-1,'1C':-2,'noclass':-3}) # thin FY 2
            riv.setrange([0.70,1.00],{'PC1':2,'PC2':2,'PC3':2,'PC4':2,'PC5':1,  'PC6':1,'PC7':0,  '1ASuper':0,'1A':-1,'1B':-2,'1C':-3,'noclass':-4}) # medium FY < 1m
            riv.setrange([1.00,1.20],{'PC1':2,'PC2':2,'PC3':2,'PC4':2,'PC5':1,  'PC6':0,'PC7':-1,  '1ASuper':-1,'1A':-2,'1B':-3,'1C':-4,'noclass':-5}) # medium FY > 1m
            riv.setrange([1.20,2.00],{'PC1':2,      'PC2':2,      'PC3':2      ,'PC4':1      ,'PC5':0,        'PC6':-1,      'PC7':-2,        '1ASuper':-2,      '1A':-3,      '1B':-4,      '1C':-5,      'noclass':-6}) # thick FY
            riv.setrange([2.00,2.50],{'PC1':2,      'PC2':1,      'PC3':1      ,'PC4':0      ,'PC5':-1      ,  'PC6':-2,      'PC7':-3,        '1ASuper':-3,      '1A':-4,      '1B':-5,      '1C':-6,      'noclass':-7}) # Second year
            riv.setrange([2.50,3.00],{'PC1':1,      'PC2':1,      'PC3':0      ,'PC4':-1     ,'PC5':-2,        'PC6':-3,      'PC7':-3,        '1ASuper':-4,      '1A':-5,      '1B':-6,      '1C':-7,      'noclass':-8}) # MY < 2.5
            riv.setrange([3.00,99.9],{'PC1':1,'PC2':0,'PC3':-1,'PC4':-2,'PC5':-2,  'PC6':-3,'PC7':-3,  '1ASuper':-4,'1A':-5,'1B':-6,'1C':-8,'noclass':-8}) # MY
    
        elif riomethod == 'Lsal':
            riv = BetweenDict()
            riv.setrange([0.  ,0.001],{'PC1':[3],'PC2':[3],'PC3':[3],'PC4':[3],'PC5':[3],  'PC6':[3],'PC7':[3],  '1ASuper':[3],'1A':[3],'1B':[3],'1C':[3],'noclass':[3]}) # no ice
            riv.setrange([0.001,0.10],{'PC1':[3],'PC2':[3],'PC3':[3],'PC4':[3],'PC5':[3],  'PC6':[2],'PC7':[2],  '1ASuper':[2],'1A':[2],'1B':[2],'1C':[2],'noclass':[1]}) # new ice
            riv.setrange([0.10,0.15],{'PC1':[3],'PC2':[3],'PC3':[3],'PC4':[3],'PC5':[3],  'PC6':[2],'PC7':[2],  '1ASuper':[2],'1A':[2],'1B':[2],'1C':[1],'noclass':[0]}) # grey ice
            riv.setrange([0.15,0.30],{'PC1':[3],'PC2':[3],'PC3':[3],'PC4':[3],'PC5':[3],  'PC6':[2],'PC7':[2],  '1ASuper':[2],'1A':[2],'1B':[1],'1C':[0],'noclass':[-1]}) # grey-white
            riv.setrange([0.30,0.50],{'PC1':[2],'PC2':[2],'PC3':[2],'PC4':[2],'PC5':[2],  'PC6':[2],'PC7':[1],  '1ASuper':[2],'1A':[1],'1B':[0],'1C':[-1],'noclass':[-2]}) # thin FY 1
            riv.setrange([0.50,0.70],{'PC1':[2],'PC2':[2],'PC3':[2],'PC4':[2],'PC5':[2],  'PC6':[1],'PC7':[1],  '1ASuper':[1],'1A':[0],'1B':[-1],'1C':[-2],'noclass':[-3]}) # thin FY 2
            riv.setrange([0.70,1.00],{'PC1':[2],'PC2':[2],'PC3':[2],'PC4':[2],'PC5':[1],  'PC6':[1],'PC7':[0],  '1ASuper':[0],'1A':[-1],'1B':[-2],'1C':[-3],'noclass':[-4]}) # medium FY < 1m
            riv.setrange([1.00,1.20],{'PC1':[2],'PC2':[2],'PC3':[2],'PC4':[2],'PC5':[1],  'PC6':[0],'PC7':[-1], '1ASuper':[-1],'1A':[-2],'1B':[-3],'1C':[-4],'noclass':[-5]}) # medium FY > 1m
            riv.setrange([1.20,2.00],{'PC1':[2,2],'PC2':[2,1],'PC3':[2,1],'PC4':[1,0],'PC5':[0,-1],  'PC6':[-1,-2],'PC7':[-2,-3],  '1ASuper':[-2,-3],'1A':[-3,-4],'1B':[-4,-5],'1C':[-5,-6],'noclass':[-6,-7]}) # thick FY / SY
            riv.setrange([2.00,2.50],{'PC1':[2,1],'PC2':[1,1],'PC3':[1,0],'PC4':[0,-1],'PC5':[-1,-2], 'PC6':[-2,-3],'PC7':[-3,-3],  '1ASuper':[-3,-4],'1A':[-4,-5],'1B':[-5,-6],'1C':[-6,-7],'noclass':[-7,-8]}) # SY / MY<2.5m
            riv.setrange([2.50,99.9],{'PC1':[1],'PC2':[0],'PC3':[-1],'PC4':[-2],'PC5':[-2],  'PC6':[-3],'PC7':[-3],  '1ASuper':[-4],'1A':[-5],'1B':[-6],'1C':[-8],'noclass':[-8]}) # MY
            # Class 1.2 to 2 m and 2 m to 2.5 m split up in single ice types depending on salinity
            # For better understanding of above numbers:
            #riv.setrange([thick FY],{'PC1':2,      'PC2':2,      'PC3':2      ,'PC4':1      ,'PC5':0,        'PC6':-1,      'PC7':-2,        '1ASuper':-2,      '1A':-3,      '1B':-4,      '1C':-5,      'noclass':-6}) # thick FY
            #riv.setrange([SY      ],{'PC1':2,      'PC2':1,      'PC3':1      ,'PC4':0      ,'PC5':-1      ,  'PC6':-2,      'PC7':-3,        '1ASuper':-3,      '1A':-4,      '1B':-5,      '1C':-6,      'noclass':-7}) # Second year
            #riv.setrange([MY <2.5 ],{'PC1':1,      'PC2':1,      'PC3':0      ,'PC4':-1     ,'PC5':-2,        'PC6':-3,      'PC7':-3,        '1ASuper':-4,      '1A':-5,      '1B':-6,      '1C':-7,      'noclass':-8}) # MY < 2.5
        
        elif riomethod == 'Lage':
            riv = BetweenDict()
            riv.setrange([0.  ,0.001],{'PC1':[3],'PC2':[3],'PC3':[3],'PC4':[3],'PC5':[3],  'PC6':[3],'PC7':[3],  '1ASuper':[3],'1A':[3],'1B':[3],'1C':[3],'noclass':[3]}) # no ice
            riv.setrange([0.001,0.10],{'PC1':[3],'PC2':[3],'PC3':[3],'PC4':[3],'PC5':[3],  'PC6':[2],'PC7':[2],  '1ASuper':[2],'1A':[2],'1B':[2],'1C':[2],'noclass':[1]}) # new ice
            riv.setrange([0.10,0.15],{'PC1':[3],'PC2':[3],'PC3':[3],'PC4':[3],'PC5':[3],  'PC6':[2],'PC7':[2],  '1ASuper':[2],'1A':[2],'1B':[2],'1C':[1],'noclass':[0]}) # grey ice
            riv.setrange([0.15,0.30],{'PC1':[3],'PC2':[3],'PC3':[3],'PC4':[3],'PC5':[3],  'PC6':[2],'PC7':[2],  '1ASuper':[2],'1A':[2],'1B':[1],'1C':[0],'noclass':[-1]}) # grey-white
            riv.setrange([0.30,0.50],{'PC1':[2],'PC2':[2],'PC3':[2],'PC4':[2],'PC5':[2],  'PC6':[2],'PC7':[1],  '1ASuper':[2],'1A':[1],'1B':[0],'1C':[-1],'noclass':[-2]}) # thin FY 1
            riv.setrange([0.50,0.70],{'PC1':[2],'PC2':[2],'PC3':[2],'PC4':[2],'PC5':[2],  'PC6':[1],'PC7':[1],  '1ASuper':[1],'1A':[0],'1B':[-1],'1C':[-2],'noclass':[-3]}) # thin FY 2
            riv.setrange([0.70,1.00],{'PC1':[2],'PC2':[2],'PC3':[2],'PC4':[2],'PC5':[1],  'PC6':[1],'PC7':[0],  '1ASuper':[0],'1A':[-1],'1B':[-2],'1C':[-3],'noclass':[-4]}) # medium FY < 1m
            riv.setrange([1.00,1.20],{'PC1':[2],'PC2':[2],'PC3':[2],'PC4':[2],'PC5':[1],  'PC6':[0],'PC7':[-1], '1ASuper':[-1],'1A':[-2],'1B':[-3],'1C':[-4],'noclass':[-5]}) # medium FY > 1m
            riv.setrange([1.20,2.00],{'PC1':[2,2,1],'PC2':[2,1,1],'PC3':[2,1,0],'PC4':[1,0,-1],'PC5':[0,-1,-2],  'PC6':[-1,-2,-3],'PC7':[-2,-3,-3],  '1ASuper':[-2,-3,-4],'1A':[-3,-4,-5],'1B':[-4,-5,-6],'1C':[-5,-6,-7],'noclass':[-6,-7,-8]}) # thick FY / SY / MY<
            riv.setrange([2.00,2.50],{'PC1':[2,2,1],'PC2':[1,1,1],'PC3':[1,1,0],'PC4':[0,0,-1],'PC5':[-1,-1,-2], 'PC6':[-2,-2,-3],'PC7':[-3,-3,-3],  '1ASuper':[-3,-3,-4],'1A':[-4,-4,-5],'1B':[-5,-5,-6],'1C':[-6,-6,-7],'noclass':[-7,-7,-8]}) # SY / SY / MY<
            riv.setrange([2.50,99.9],{'PC1':[1],'PC2':[0],'PC3':[-1],'PC4':[-2],'PC5':[-2],  'PC6':[-3],'PC7':[-3],  '1ASuper':[-4],'1A':[-5],'1B':[-6],'1C':[-8],'noclass':[-8]}) # MY
            # Class 1.2 to 2 m and 2 m to 2.5 m split up in single ice types depending on ice age
            # For better understanding of above numbers:
            #riv.setrange([thick FY],{'PC1':2,      'PC2':2,      'PC3':2      ,'PC4':1      ,'PC5':0,        'PC6':-1,      'PC7':-2,        '1ASuper':-2,      '1A':-3,      '1B':-4,      '1C':-5,      'noclass':-6}) # thick FY
            #riv.setrange([SY      ],{'PC1':2,      'PC2':1,      'PC3':1      ,'PC4':0      ,'PC5':-1      ,  'PC6':-2,      'PC7':-3,        '1ASuper':-3,      '1A':-4,      '1B':-5,      '1C':-6,      'noclass':-7}) # Second year
            #riv.setrange([MY <2.5 ],{'PC1':1,      'PC2':1,      'PC3':0      ,'PC4':-1     ,'PC5':-2,        'PC6':-3,      'PC7':-3,        '1ASuper':-4,      '1A':-5,      '1B':-6,      '1C':-7,      'noclass':-8}) # MY < 2.5
        #####################################
        # Calculate RIO based on Risk Values
        if riomethod == 'Lthick':
            thi=hcat #+ scat (we do not add snow thickness anymore because RIO definition was developed without taking care of snow)
            # RIO = (C1xRV1)+(C2xRV2)+(C3xRV3)+...(CnxRVn)
            rio = 0.
            for icl in range(len(ccat)): # ice categories
                try:
                    rio += (10.*ccat[icl]) * riv.lookup(thi[icl])[shipclass] # *10 because C is in ice concentration in tenths.        
                except KeyError: # This happens if POLARIS gets a NaN value (because of land grid cells). Then POLARIS's lookup returns an empty dictonary.
                    return np.nan # Return NaN to keep land areas masked.
            return rio
        
        elif riomethod == 'Lsal':
            thi=hcat #+ scat (we do not add snow thickness anymore because RIO definition was developed without taking care of snow)
            # RIO = (C1xRV1)+(C2xRV2)+(C3xRV3)+...(CnxRVn)
            rio = 0.
            for icl in range(len(ccat)): # 5 model ice categories
                try:
                    salindex=not(min(1,int(np.floor(sal/salMY)))) #0: saltier than salMY=> FY 1: fresh => less saline than salMY => MY  [more exactly: for 120-200 cm: FY (salty) or SY (fresh), for 200-150cm: SY (salty) or MY (fresh)]   
                    # Use this if isali is given per categroy:
                    #salindex=not(min(1,int(np.floor(salcat[icl]/salMY)))) #0: saltier than salMY=> FY 1: fresh => less saline than salMY => MY  [more exactly: for 120-200 cm: FY (salty) or SY (fresh), for 200-150cm: SY (salty) or MY (fresh)]   
                    riv_all =  2*riv.lookup(thi[icl])[shipclass] # lookup-table returns lists with 1 or 2 elements. We want to duplicate (times 2) all 1-element lists, because the respectice RIV is valid for ALL ice salinities. It does not hurt to duplicate also 2-element lists.
                    rio += (10.*ccat[icl]) * riv_all[salindex] # *10 because C is in ice concentration in tenths.  
                except KeyError: # This happens if POLARIS get a NaN value (because of land grid cells). Then POLARIS's lookup returns an empty dictonary.
                    return np.nan # Return NaN to keep land areas masked.
            return rio
                
        elif riomethod == 'Lage':
            thi=hcat #+ scat (we do not add snow thickness anymore because RIO definition was developed without taking care of snow)
            # RIO = (C1xRV1)+(C2xRV2)+(C3xRV3)+...(CnxRVn)
            rio = 0.
            for icl in range(len(ccat)): # 5 model ice categories
                try:
                    ageindex=min(2,int(np.floor(age))) # 0=FY, 1=SY, 2=MY
                    # Use this if iage is given per categroy:
                    #ageindex=min(2,int(np.floor(agecat[icl]))) # 0=FY, 1=SY, 2=MY
                    riv_all =  3*riv.lookup(thi[icl])[shipclass] # lookup-table returns lists with 1 or 3 elements. We want to duplicate (times 3) all 1-element lists, because the respectice RIV is valid for ALL ice ages. It does not hurt to duplicate also 3-element lists.
                    rio += (10.*ccat[icl]) * riv_all[ageindex] # *10 because C is in ice concentration in tenths.        
                except KeyError: # This happens if POLARIS get a NaN value (because of land grid cells). Then POLARIS's lookup returns an empty dictonary.
                    return np.nan # Return NaN to keep land areas masked.
            return rio
     
     # End function polaris
    ###############################################
    
    # Set up an empty output array
    riofinal=np.array(np.nan*np.zeros([nt,len(shipclasses),ny,nx]))
    
    #########################
    # Calculate RIO
    ########################
    
    # Loop through time steps
    for jt in range(nt):
        #Loop through ship classes
        for shipclassnr, shipclass in enumerate(shipclasses):
            print("Calculating RIO for shipclass "+shipclass+' for '+ str(icedata[configs['coordinates']['time_name']].data[jt]) )
            sys.stdout.flush()
            # Start measuring calculation time
            cputime=time.time()
            
            # Rio calculation is much faster, if normal arrays are used instead of masked arrays.
            #siitdconcJT=siitdconc.data[jt,:,:,:]
            #siitdconcJT[siitdconc.mask[jt,:,:,:]]=0.
            #siitdthicknomask=siitdthick.data[jt,:,:,:]
    
            siconcJT=siconc.data[jt,:,:].compute()
            #siitdconcJT[siitdconc.mask[jt,:,:,:]]=0.
            sithickJT=sithick.data[jt,:,:].compute()
            if riomethod=='Lsal':
                sisaliJT=sisali.data[jt,:,:].compute()
            elif riomethod=='Lage':
                siageJT=siage.data[jt,:,:].compute()
    
            #siagecatnomask=siagecat.data[jt,:,:,:]     
            #salincatnomask=salincat.data[jt,:,:,:]                   
    
            rioJT = np.nan*np.zeros([ny,nx])
            
            for jjk in range(ny):
                for jik in range(nx):
                    if np.isnan(siconcJT[jjk,jik].sum()):
                        rioJT[jjk,jik]=np.nan
                    elif siconcJT[jjk,jik].sum() <=0.: # If siitdconc.sum == 0 : open water
                        rioJT[jjk,jik]=30.
                    else:
                        (iconc_fullcat, ithick_fullcat) = addopenwater(np.array([siconcJT[jjk,jik]]),np.array([sithickJT[jjk,jik]]))
                        if riomethod=='Lthick':
                            rioJT[jjk,jik]=polaris(riomethod,shipclass,iconc_fullcat,ithick_fullcat)                        
                        elif riomethod=='Lsal':
                            rioJT[jjk,jik]=polaris(riomethod,shipclass,iconc_fullcat,ithick_fullcat,sisaliJT[jjk,jik])                        
                        elif riomethod=='Lage':
                            rioJT[jjk,jik]=polaris(riomethod,shipclass,iconc_fullcat,ithick_fullcat,siageJT[jjk,jik])                        
                        
                        ## This is only needed if sisali is given per category (sisalicat)
                        #(plotcww, plothww, plotsalww) = addopenwater(siitdconcJT[:,jjk,jik],siitdthickJT[:,jjk,jik],salincatnomask[:,jjk,jik])        
                        #rioJT[jjk,jik]=polaris('mod',shipclass,plotcww,plothww,plotsalww)
                        
                        ## This is only needed if siage is given per category (siagecat)
                        #(plotcww, plothww, plotageww) = addopenwater(siitdconcJT[:,jjk,jik],siitdthickJT[:,jjk,jik],siagecatnomask[:,jjk,jik])            
                        #rioJT[jjk,jik]=polaris('mod',shipclass,plotcww,plothww,plotageww)
                        
            # Reapply mask (if needed)
            riotoplot=np.where(siconc[jt,:,:]>=0,rioJT,np.nan)
            print("Calculation time: "+str(int(time.time()-cputime))+' s')
            
            riofinal[jt,shipclassnr,:,:]=riotoplot
            
        # End loop shipclasses    
    # End loop jt
    return(riofinal)

def calcRIO_multicat(icedata,configs):

    import numpy as np
    import warnings
    import time # for sleep and cputime measurement
    import sys # For flushing of buffer to stdout
    
    # Simpler names for relevant variables
    ############################################
    if configs['coordinates']['ncat'] > 1:
        siitdthick= icedata.siitdthick
        siitdconc= icedata.siitdconc
    
        nt = icedata[configs['coordinates']['time_name']].shape[0] # Number of time steps
        ny = siitdconc.shape[2] # Number of grid points in y-direction
        nx = siitdconc.shape[3] # Number of grid points in x-direction
    

   
    
    if configs['RIOmethod']['Lage']==True:
        siage= icedata.siage
    elif configs['RIOmethod']['Lsal']==True:
        sisali= icedata.sisali
        #salincat= icedata.sisalicat? # Snippet for multicat salinity
        salMY = 5.0 # [ppt] Limit for discrimination between FY and MY ice
    
    # List of requested ship classes
    shipclasses = configs['output']['shipclasses'] # a subset of ['PC1','PC2','PC3','PC4','PC5','PC6','PC7','1ASuper','1A','1B','1C','noclass']
    # RIO calculation method as string (Lthick, Lage or Lsal)
    riomethod=[i for i in configs['RIOmethod'] if configs['RIOmethod'][i]==True][0]
    
    ##########################################################
    # Function to add open water to the list of ice categories
    ##########################################################
    
    def addopenwater(siitdconc,siitdthick,*argv): # argv could be siagecat
        cww = np.array([1.-np.sum(siitdconc)]+[x for x in siitdconc])
        hww = np.array([0.]+[x for x in siitdthick])
        if len(argv) == 0 :
            return (cww,hww)
        elif len(argv) == 1 : # This is only necessary if ice salinity or ice age are given per categroy. This feature is not currently used.
            ageww = np.array([0.]+[x for x in argv[0]])
            return (cww,hww,ageww)
        else:
            raise RuntimeError('The function ADDOPENWATER can only be called with 2 or 3 arguments, not with: '+str(len(argv)))
    
    
    ##########################################################
    # Function to calculate RIO for one grid point
    ##########################################################
    # This is according to MSC Circ1
    def polaris(riomethod,shipclass,*argv):
        if riomethod == 'Lthick':
            if not len(argv)==2:
                raise RuntimeError("If riomethod is 'Lthick', then you have to provide 2 additional arguments: CCAT and HCAT.")
            else:
                ccat=argv[0]
                hcat=argv[1]
        elif riomethod == 'Lsal':
            if not len(argv)==3:
                raise RuntimeError("If riomethod is 'Lsal', then you have to provide 3 additional arguments: CCAT, HCAT and Sal.")
            else:
                ccat=argv[0]
                hcat=argv[1]
                sal=argv[2]                    
                # Use this if salinity is given per category
                #salcat=argv[2]                    
        elif riomethod == 'Lage':
            if not len(argv)==3:
                raise RuntimeError("If riomethod is 'Lage', then you have to provide 3 additional arguments: CCAT, HCAT and Age.")
            else:
                ccat=argv[0]
                hcat=argv[1]
                age=argv[2]
                # Use this if iage is given per categrory
                #agecat=argv[2]
        else:
            raise ValueError("riomethod has to be one of ['Lthick', 'Lsal', 'Lage'], not "+riomethod)
                        
        if np.sum(ccat) < 0.99:
            raise RuntimeError("The ice concentrations in CCAT do not sum up to 100%. Did you forget to include the open water fraction?")
    
        if not (shipclass in ['PC1','PC2','PC3','PC4','PC5','PC6','PC7','1ASuper','1A','1B','1C','noclass']):
            raise ValueError("shipclass has to be one of ['PC1','PC2','PC3','PC4','PC5','PC6','PC7','1ASuper','1A','1B','1C','noclass']")
        
        #########################
        # Define BetweenDict used for ice thickness ranges
        # http://joshuakugler.com/archives/30-BetweenDict,-a-Python-dict-for-value-ranges.html
        class BetweenDict(dict):
            def __init__(self, d = {}):
                for k,v in d.items():
                    self[k] = v
        
            def lookup(self, key):
                for k, v in self.items():
                    if k[0] <= key < k[1]:
                        return v
                warnings.warn("Key '%s' is not between any values in the BetweenDict" % key)
                return {np.nan:np.nan} #Andrea: Return a dictionary so that riv.lookup(thi[icl])[shipclass] will raise a KeyError.
                #Andrea: raise KeyError("Key '%s' is not between any values in the BetweenDict" % key)
        
            def setrange(self, key, value):
                try:
                    if len(key) == 2:
                        if key[0] < key[1]:
                            dict.__setitem__(self, (key[0], key[1]), value)
                        else:
                            raise RuntimeError('First element of a BetweenDict key '
                                               'must be strictly less than the '
                                               'second element')
                    else:
                        raise ValueError('Key of a BetweenDict must be an iterable '
                                         'with length two')
                except TypeError:
                    raise TypeError('Key of a BetweenDict must be an iterable '
                                     'with length two')
        
            def __contains__(self, key):
                try:
                    return bool(self[key]) or True
                except KeyError:
                    return False
        # End class BetweenDict
        
        
        ###############################
        # Define Risk Values (RIV) for different riomethods (Adopted from POLARIS Risk Value Table)
        # (We always use RIVs for winter because for decayed/summer conditions the state of decay has to be proven by captain)
        if riomethod == 'Lthick':  
            riv = BetweenDict()
            riv.setrange([0.  ,0.001],{'PC1':3,'PC2':3,'PC3':3,'PC4':3,'PC5':3,  'PC6':3,'PC7':3,  '1ASuper':3,'1A':3,'1B':3,'1C':3,'noclass':3}) # no ice
            riv.setrange([0.001,0.10],{'PC1':3,'PC2':3,'PC3':3,'PC4':3,'PC5':3,  'PC6':2,'PC7':2,  '1ASuper':2,'1A':2,'1B':2,'1C':2,'noclass':1}) # new ice
            riv.setrange([0.10,0.15],{'PC1':3,'PC2':3,'PC3':3,'PC4':3,'PC5':3,  'PC6':2,'PC7':2,  '1ASuper':2,'1A':2,'1B':2,'1C':1,'noclass':0}) # grey ice
            riv.setrange([0.15,0.30],{'PC1':3,'PC2':3,'PC3':3,'PC4':3,'PC5':3,  'PC6':2,'PC7':2,  '1ASuper':2,'1A':2,'1B':1,'1C':0,'noclass':-1}) # grey-white
            riv.setrange([0.30,0.50],{'PC1':2,'PC2':2,'PC3':2,'PC4':2,'PC5':2,  'PC6':2,'PC7':1,  '1ASuper':2,'1A':1,'1B':0,'1C':-1,'noclass':-2}) # thin FY 1
            riv.setrange([0.50,0.70],{'PC1':2,'PC2':2,'PC3':2,'PC4':2,'PC5':2,  'PC6':1,'PC7':1,  '1ASuper':1,'1A':0,'1B':-1,'1C':-2,'noclass':-3}) # thin FY 2
            riv.setrange([0.70,1.00],{'PC1':2,'PC2':2,'PC3':2,'PC4':2,'PC5':1,  'PC6':1,'PC7':0,  '1ASuper':0,'1A':-1,'1B':-2,'1C':-3,'noclass':-4}) # medium FY < 1m
            riv.setrange([1.00,1.20],{'PC1':2,'PC2':2,'PC3':2,'PC4':2,'PC5':1,  'PC6':0,'PC7':-1,  '1ASuper':-1,'1A':-2,'1B':-3,'1C':-4,'noclass':-5}) # medium FY > 1m
            riv.setrange([1.20,2.00],{'PC1':2,      'PC2':2,      'PC3':2      ,'PC4':1      ,'PC5':0,        'PC6':-1,      'PC7':-2,        '1ASuper':-2,      '1A':-3,      '1B':-4,      '1C':-5,      'noclass':-6}) # thick FY
            riv.setrange([2.00,2.50],{'PC1':2,      'PC2':1,      'PC3':1      ,'PC4':0      ,'PC5':-1      ,  'PC6':-2,      'PC7':-3,        '1ASuper':-3,      '1A':-4,      '1B':-5,      '1C':-6,      'noclass':-7}) # Second year
            riv.setrange([2.50,3.00],{'PC1':1,      'PC2':1,      'PC3':0      ,'PC4':-1     ,'PC5':-2,        'PC6':-3,      'PC7':-3,        '1ASuper':-4,      '1A':-5,      '1B':-6,      '1C':-7,      'noclass':-8}) # MY < 2.5
            riv.setrange([3.00,99.9],{'PC1':1,'PC2':0,'PC3':-1,'PC4':-2,'PC5':-2,  'PC6':-3,'PC7':-3,  '1ASuper':-4,'1A':-5,'1B':-6,'1C':-8,'noclass':-8}) # MY
    
        elif riomethod == 'Lsal':
            riv = BetweenDict()
            riv.setrange([0.  ,0.001],{'PC1':[3],'PC2':[3],'PC3':[3],'PC4':[3],'PC5':[3],  'PC6':[3],'PC7':[3],  '1ASuper':[3],'1A':[3],'1B':[3],'1C':[3],'noclass':[3]}) # no ice
            riv.setrange([0.001,0.10],{'PC1':[3],'PC2':[3],'PC3':[3],'PC4':[3],'PC5':[3],  'PC6':[2],'PC7':[2],  '1ASuper':[2],'1A':[2],'1B':[2],'1C':[2],'noclass':[1]}) # new ice
            riv.setrange([0.10,0.15],{'PC1':[3],'PC2':[3],'PC3':[3],'PC4':[3],'PC5':[3],  'PC6':[2],'PC7':[2],  '1ASuper':[2],'1A':[2],'1B':[2],'1C':[1],'noclass':[0]}) # grey ice
            riv.setrange([0.15,0.30],{'PC1':[3],'PC2':[3],'PC3':[3],'PC4':[3],'PC5':[3],  'PC6':[2],'PC7':[2],  '1ASuper':[2],'1A':[2],'1B':[1],'1C':[0],'noclass':[-1]}) # grey-white
            riv.setrange([0.30,0.50],{'PC1':[2],'PC2':[2],'PC3':[2],'PC4':[2],'PC5':[2],  'PC6':[2],'PC7':[1],  '1ASuper':[2],'1A':[1],'1B':[0],'1C':[-1],'noclass':[-2]}) # thin FY 1
            riv.setrange([0.50,0.70],{'PC1':[2],'PC2':[2],'PC3':[2],'PC4':[2],'PC5':[2],  'PC6':[1],'PC7':[1],  '1ASuper':[1],'1A':[0],'1B':[-1],'1C':[-2],'noclass':[-3]}) # thin FY 2
            riv.setrange([0.70,1.00],{'PC1':[2],'PC2':[2],'PC3':[2],'PC4':[2],'PC5':[1],  'PC6':[1],'PC7':[0],  '1ASuper':[0],'1A':[-1],'1B':[-2],'1C':[-3],'noclass':[-4]}) # medium FY < 1m
            riv.setrange([1.00,1.20],{'PC1':[2],'PC2':[2],'PC3':[2],'PC4':[2],'PC5':[1],  'PC6':[0],'PC7':[-1], '1ASuper':[-1],'1A':[-2],'1B':[-3],'1C':[-4],'noclass':[-5]}) # medium FY > 1m
            riv.setrange([1.20,2.00],{'PC1':[2,2],'PC2':[2,1],'PC3':[2,1],'PC4':[1,0],'PC5':[0,-1],  'PC6':[-1,-2],'PC7':[-2,-3],  '1ASuper':[-2,-3],'1A':[-3,-4],'1B':[-4,-5],'1C':[-5,-6],'noclass':[-6,-7]}) # thick FY / SY
            riv.setrange([2.00,2.50],{'PC1':[2,1],'PC2':[1,1],'PC3':[1,0],'PC4':[0,-1],'PC5':[-1,-2], 'PC6':[-2,-3],'PC7':[-3,-3],  '1ASuper':[-3,-4],'1A':[-4,-5],'1B':[-5,-6],'1C':[-6,-7],'noclass':[-7,-8]}) # SY / MY<2.5m
            riv.setrange([2.50,99.9],{'PC1':[1],'PC2':[0],'PC3':[-1],'PC4':[-2],'PC5':[-2],  'PC6':[-3],'PC7':[-3],  '1ASuper':[-4],'1A':[-5],'1B':[-6],'1C':[-8],'noclass':[-8]}) # MY
            # Class 1.2 to 2 m and 2 m to 2.5 m split up in single ice types depending on salinity
            # For better understanding of above numbers:
            #riv.setrange([thick FY],{'PC1':2,      'PC2':2,      'PC3':2      ,'PC4':1      ,'PC5':0,        'PC6':-1,      'PC7':-2,        '1ASuper':-2,      '1A':-3,      '1B':-4,      '1C':-5,      'noclass':-6}) # thick FY
            #riv.setrange([SY      ],{'PC1':2,      'PC2':1,      'PC3':1      ,'PC4':0      ,'PC5':-1      ,  'PC6':-2,      'PC7':-3,        '1ASuper':-3,      '1A':-4,      '1B':-5,      '1C':-6,      'noclass':-7}) # Second year
            #riv.setrange([MY <2.5 ],{'PC1':1,      'PC2':1,      'PC3':0      ,'PC4':-1     ,'PC5':-2,        'PC6':-3,      'PC7':-3,        '1ASuper':-4,      '1A':-5,      '1B':-6,      '1C':-7,      'noclass':-8}) # MY < 2.5
        
        elif riomethod == 'Lage':
            riv = BetweenDict()
            riv.setrange([0.  ,0.001],{'PC1':[3],'PC2':[3],'PC3':[3],'PC4':[3],'PC5':[3],  'PC6':[3],'PC7':[3],  '1ASuper':[3],'1A':[3],'1B':[3],'1C':[3],'noclass':[3]}) # no ice
            riv.setrange([0.001,0.10],{'PC1':[3],'PC2':[3],'PC3':[3],'PC4':[3],'PC5':[3],  'PC6':[2],'PC7':[2],  '1ASuper':[2],'1A':[2],'1B':[2],'1C':[2],'noclass':[1]}) # new ice
            riv.setrange([0.10,0.15],{'PC1':[3],'PC2':[3],'PC3':[3],'PC4':[3],'PC5':[3],  'PC6':[2],'PC7':[2],  '1ASuper':[2],'1A':[2],'1B':[2],'1C':[1],'noclass':[0]}) # grey ice
            riv.setrange([0.15,0.30],{'PC1':[3],'PC2':[3],'PC3':[3],'PC4':[3],'PC5':[3],  'PC6':[2],'PC7':[2],  '1ASuper':[2],'1A':[2],'1B':[1],'1C':[0],'noclass':[-1]}) # grey-white
            riv.setrange([0.30,0.50],{'PC1':[2],'PC2':[2],'PC3':[2],'PC4':[2],'PC5':[2],  'PC6':[2],'PC7':[1],  '1ASuper':[2],'1A':[1],'1B':[0],'1C':[-1],'noclass':[-2]}) # thin FY 1
            riv.setrange([0.50,0.70],{'PC1':[2],'PC2':[2],'PC3':[2],'PC4':[2],'PC5':[2],  'PC6':[1],'PC7':[1],  '1ASuper':[1],'1A':[0],'1B':[-1],'1C':[-2],'noclass':[-3]}) # thin FY 2
            riv.setrange([0.70,1.00],{'PC1':[2],'PC2':[2],'PC3':[2],'PC4':[2],'PC5':[1],  'PC6':[1],'PC7':[0],  '1ASuper':[0],'1A':[-1],'1B':[-2],'1C':[-3],'noclass':[-4]}) # medium FY < 1m
            riv.setrange([1.00,1.20],{'PC1':[2],'PC2':[2],'PC3':[2],'PC4':[2],'PC5':[1],  'PC6':[0],'PC7':[-1], '1ASuper':[-1],'1A':[-2],'1B':[-3],'1C':[-4],'noclass':[-5]}) # medium FY > 1m
            riv.setrange([1.20,2.00],{'PC1':[2,2,1],'PC2':[2,1,1],'PC3':[2,1,0],'PC4':[1,0,-1],'PC5':[0,-1,-2],  'PC6':[-1,-2,-3],'PC7':[-2,-3,-3],  '1ASuper':[-2,-3,-4],'1A':[-3,-4,-5],'1B':[-4,-5,-6],'1C':[-5,-6,-7],'noclass':[-6,-7,-8]}) # thick FY / SY / MY<
            riv.setrange([2.00,2.50],{'PC1':[2,2,1],'PC2':[1,1,1],'PC3':[1,1,0],'PC4':[0,0,-1],'PC5':[-1,-1,-2], 'PC6':[-2,-2,-3],'PC7':[-3,-3,-3],  '1ASuper':[-3,-3,-4],'1A':[-4,-4,-5],'1B':[-5,-5,-6],'1C':[-6,-6,-7],'noclass':[-7,-7,-8]}) # SY / SY / MY<
            riv.setrange([2.50,99.9],{'PC1':[1],'PC2':[0],'PC3':[-1],'PC4':[-2],'PC5':[-2],  'PC6':[-3],'PC7':[-3],  '1ASuper':[-4],'1A':[-5],'1B':[-6],'1C':[-8],'noclass':[-8]}) # MY
            # Class 1.2 to 2 m and 2 m to 2.5 m split up in single ice types depending on ice age
            # For better understanding of above numbers:
            #riv.setrange([thick FY],{'PC1':2,      'PC2':2,      'PC3':2      ,'PC4':1      ,'PC5':0,        'PC6':-1,      'PC7':-2,        '1ASuper':-2,      '1A':-3,      '1B':-4,      '1C':-5,      'noclass':-6}) # thick FY
            #riv.setrange([SY      ],{'PC1':2,      'PC2':1,      'PC3':1      ,'PC4':0      ,'PC5':-1      ,  'PC6':-2,      'PC7':-3,        '1ASuper':-3,      '1A':-4,      '1B':-5,      '1C':-6,      'noclass':-7}) # Second year
            #riv.setrange([MY <2.5 ],{'PC1':1,      'PC2':1,      'PC3':0      ,'PC4':-1     ,'PC5':-2,        'PC6':-3,      'PC7':-3,        '1ASuper':-4,      '1A':-5,      '1B':-6,      '1C':-7,      'noclass':-8}) # MY < 2.5
        
        #####################################
        # Calculate RIO based on Risk Values
        if riomethod == 'Lthick':
            thi=hcat #+ scat (we do not add snow thickness anymore because RIO definition was developed without taking care of snow)
            # RIO = (C1xRV1)+(C2xRV2)+(C3xRV3)+...(CnxRVn)
            rio = 0.
            for icl in range(len(ccat)): # ice categories
                try:
                    rio += (10.*ccat[icl]) * riv.lookup(thi[icl])[shipclass] # *10 because C is in ice concentration in tenths.        
                except KeyError: # This happens if POLARIS gets a NaN value (because of land grid cells). Then POLARIS's lookup returns an empty dictonary.
                    return np.nan # Return NaN to keep land areas masked.
            return rio
        
        elif riomethod == 'Lsal':
            thi=hcat #+ scat (we do not add snow thickness anymore because RIO definition was developed without taking care of snow)
            # RIO = (C1xRV1)+(C2xRV2)+(C3xRV3)+...(CnxRVn)
            rio = 0.
            for icl in range(len(ccat)): # 5 model ice categories
                try:
                    salindex=not(min(1,int(np.floor(sal/salMY)))) #0: saltier than salMY=> FY 1: fresh => less saline than salMY => MY  [more exactly: for 120-200 cm: FY (salty) or SY (fresh), for 200-150cm: SY (salty) or MY (fresh)]   
                    # Use this if isali is given per categroy:
                    #salindex=not(min(1,int(np.floor(salcat[icl]/salMY)))) #0: saltier than salMY=> FY 1: fresh => less saline than salMY => MY  [more exactly: for 120-200 cm: FY (salty) or SY (fresh), for 200-150cm: SY (salty) or MY (fresh)]   
                    riv_all =  2*riv.lookup(thi[icl])[shipclass] # lookup-table returns lists with 1 or 2 elements. We want to duplicate (times 2) all 1-element lists, because the respectice RIV is valid for ALL ice salinities. It does not hurt to duplicate also 2-element lists.
                    rio += (10.*ccat[icl]) * riv_all[salindex] # *10 because C is in ice concentration in tenths.  
                except KeyError: # This happens if POLARIS get a NaN value (because of land grid cells). Then POLARIS's lookup returns an empty dictonary.
                    return np.nan # Return NaN to keep land areas masked.
            return rio
                
        elif riomethod == 'Lage':
            thi=hcat #+ scat (we do not add snow thickness anymore because RIO definition was developed without taking care of snow)
            # RIO = (C1xRV1)+(C2xRV2)+(C3xRV3)+...(CnxRVn)
            rio = 0.
            for icl in range(len(ccat)): # 5 model ice categories
                try:
                    ageindex=min(2,int(np.floor(age))) # 0=FY, 1=SY, 2=MY
                    # Use this if iage is given per categroy:
                    #ageindex=min(2,int(np.floor(agecat[icl]))) # 0=FY, 1=SY, 2=MY
                    riv_all =  3*riv.lookup(thi[icl])[shipclass] # lookup-table returns lists with 1 or 3 elements. We want to duplicate (times 3) all 1-element lists, because the respectice RIV is valid for ALL ice ages. It does not hurt to duplicate also 3-element lists.
                    rio += (10.*ccat[icl]) * riv_all[ageindex] # *10 because C is in ice concentration in tenths.        
                except KeyError: # This happens if POLARIS get a NaN value (because of land grid cells). Then POLARIS's lookup returns an empty dictonary.
                    return np.nan # Return NaN to keep land areas masked.
            return rio
     
     # End function polaris
    ###############################################
    
    # Set up an empty output array
    riofinal=np.array(np.nan*np.zeros([nt,len(shipclasses),ny,nx]))
    
    #########################
    # Calculate RIO
    ########################
    
    # Loop through time steps
    for jt in range(nt):
        #Loop through ship classes
        for shipclassnr,shipclass in enumerate(shipclasses):
            print("Calculating RIO for shipclass "+shipclass+' for '+ str(icedata[configs['coordinates']['time_name']].data[jt]) )
            sys.stdout.flush()
            # Start measuring calculation time
            cputime=time.time()
            
            # Rio calculation is much faster, if normal arrays are used instead of masked arrays.
            #siitdconcJT=siitdconc.data[jt,:,:,:]
            #siitdconcJT[siitdconc.mask[jt,:,:,:]]=0.
            #siitdthicknomask=siitdthick.data[jt,:,:,:]
    
            siitdconcJT=siitdconc.data[jt,:,:,:].compute()
            #siitdconcJT[siitdconc.mask[jt,:,:,:]]=0.
            siitdthickJT=siitdthick.data[jt,:,:,:].compute()
            if riomethod=='Lsal':
                sisaliJT=sisali.data[jt,:,:].compute()
            elif riomethod=='Lage':
                siageJT=siage.data[jt,:,:].compute()
    
            #siagecatnomask=siagecat.data[jt,:,:,:]     
            #salincatnomask=salincat.data[jt,:,:,:]                   
    
            rioJT = np.nan*np.zeros([ny,nx])
            
            for jjk in range(ny):
                for jik in range(nx):
                    if np.isnan(siitdconcJT[:,jjk,jik].sum()):
                        rioJT[jjk,jik]=np.nan
                    elif siitdconcJT[:,jjk,jik].sum() <=0.: # If siitdconc.sum == 0 : open water
                        rioJT[jjk,jik]=30.
                    else:
                        (iconc_fullcat, ithick_fullcat) = addopenwater(siitdconcJT[:,jjk,jik],siitdthickJT[:,jjk,jik])
                        if riomethod=='Lthick':
                            rioJT[jjk,jik]=polaris(riomethod,shipclass,iconc_fullcat,ithick_fullcat)                        
                        elif riomethod=='Lsal':
                            rioJT[jjk,jik]=polaris(riomethod,shipclass,iconc_fullcat,ithick_fullcat,sisaliJT[jjk,jik])                        
                        elif riomethod=='Lage':
                            rioJT[jjk,jik]=polaris(riomethod,shipclass,iconc_fullcat,ithick_fullcat,siageJT[jjk,jik])                        
                        
                        ## This is only needed if sisali is given per category (sisalicat)
                        #(plotcww, plothww, plotsalww) = addopenwater(siitdconcJT[:,jjk,jik],siitdthickJT[:,jjk,jik],salincatnomask[:,jjk,jik])        
                        #rioJT[jjk,jik]=polaris('mod',shipclass,plotcww,plothww,plotsalww)
                        
                        ## This is only needed if siage is given per category (siagecat)
                        #(plotcww, plothww, plotageww) = addopenwater(siitdconcJT[:,jjk,jik],siitdthickJT[:,jjk,jik],siagecatnomask[:,jjk,jik])            
                        #rioJT[jjk,jik]=polaris('mod',shipclass,plotcww,plothww,plotageww)
                        
            # Reapply mask (if needed)
            #riotoplot=np.ma.array(rioJT,mask=siitdconc.mask[jt,0,:,:])
            print("Calculation time: "+str(int(time.time()-cputime))+' s')
            
            riofinal[jt,shipclassnr,:,:]=rioJT
            
        # End loop shipclasses    
    # End loop jt
    return(riofinal)
    
################################################
################################################

if __name__ == "__main__":
    # If this script is called directly without RIOengine_NOCOS-py, do everything necessary using config from config_RIOcalc.yml
    from read_config import read_configfile
    from read_ice_data import read_ice_data
    from save_RIO_toNetCDF import save_toNetcdf
    
    configs=read_configfile()
    icedata=read_ice_data(configs)
    riodata=calcRIO_multicat(icedata,configs)
    save_toNetcdf(riodata,icedata,configs)

