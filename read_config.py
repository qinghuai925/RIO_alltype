
def read_configfile(*argv):
    import yaml
    
# Open the config file
######################
    if len(argv)==1:
        config_filename=argv[0]  # Given as input argument
    elif len(argv)==0:
        config_filename='config_RIOcalc_default.yml' # Default filename
    else:
        raise RuntimeError("READ_CONFIGFILE can only be called with zero or one argument, not with "+str(len(argv)))
        
    with open(config_filename,"r") as ymlfile:
         configs = yaml.load(ymlfile,  Loader=yaml.Loader)
    
# Derived setting variables and sanity checks
###############################################
# a) Read NCAT, do sanity checks and set configs['multiCAT'] flag
# b) Set configs['Lvol'] flag based on whether thickness or volume variable is provided
    
    # Mono-category
    if configs['coordinates']['ncat'] == 1:
        configs['multiCAT']=False
        if configs['variables']['siconc_name']==None:
            raise RuntimeError("IF NCAT is 1, you need to specify 'siconc_name'")
        if configs['variables']['sithick_name']==None and configs['variables']['sivol_name']==None :
            raise RuntimeError("IF NCAT is 1, you need to specify either 'sithick_name' or 'sivol_name'")
        else:
            if configs['variables']['sithick_name']==None:
                configs['Lvol']=True
            else:
                configs['Lvol']=False
    
    # Multi-category
    elif configs['coordinates']['ncat'] > 1:
        configs['multiCAT']=True
        if configs['coordinates']['ncat_name']==None:
            raise RuntimeError("IF NCAT > 1, you have to provide the name of the ice category dimension NCAT_NAME.")
        if configs['variables']['siitdconc_name']==None:
            raise RuntimeError("IF NCAT is >1, you need to specify 'siitdconc_name'")
        if configs['variables']['siitdthick_name']==None and configs['variables']['siitdvol_name']==None :
            raise RuntimeError("IF NCAT is >1, you need to specify either 'siitdthick_name' or 'siitdvol_name'")
        else:
            if configs['variables']['siitdthick_name']==None:
                configs['Lvol']=True
            else:
                configs['Lvol']=False
    
    else:
        raise RuntimeError("NCAT needs to be positive > 0.") 
    
# c) Make sure that only one of Lthick, Lage or Lsal is set.
    if sum([configs['RIOmethod'][i] for i in configs['RIOmethod']]) != 1:
        raise RuntimeError("You need to set exactly one of Lthick, Lage or Lsal to True.")
    
# d) Check that siage and sisali variables are given
    if configs['RIOmethod']['Lage'] and configs['variables']['siage_name']==None:
        raise RuntimeError("If 'Lage' is true, you need to provide 'siage_name'.")
    if configs['RIOmethod']['Lsal'] and configs['variables']['sisali_name']==None:
        raise RuntimeError("If 'Lsal' is true, you need to provide 'sisali_name'.")
        
# e) Check if ship classes make sense 
    shipclassNUMlist=[] # Empty list to collect requested shipclasses as integer numbers
    for shipc in configs['output']['shipclasses']:
        if   shipc == 'PC1': shipclassNUMlist.append(1)
        elif shipc == 'PC2': shipclassNUMlist.append(2)
        elif shipc == 'PC3': shipclassNUMlist.append(3)
        elif shipc == 'PC4': shipclassNUMlist.append(4)
        elif shipc == 'PC5': shipclassNUMlist.append(5)
        elif shipc == 'PC6': shipclassNUMlist.append(6)
        elif shipc == 'PC7': shipclassNUMlist.append(7)
        elif shipc == '1ASuper': shipclassNUMlist.append(10)
        elif shipc == '1A': shipclassNUMlist.append(11)
        elif shipc == '1B': shipclassNUMlist.append(12)
        elif shipc == '1C': shipclassNUMlist.append(13)
        elif shipc == 'noclass': shipclassNUMlist.append(20)
        else: raise RuntimeError(shipc+' is not a valid shipclass. Check your config.yml file.')
        
    configs['output']['shipclassNUMs']=shipclassNUMlist
    
# f) Check output settings
    if configs['output']['filename_automatic']!=True and configs['output']['filename']==None:
        raise RuntimeError("You need to set FILENAME_AUTOMATIC to True if you don't provide an output filename.")
    if configs['output']['output_folder']==None:
        configs['output']['output_folder']="."  # If no output folder is given, set it to the current working directory
    
    print("These are the configurations you have chosen:")
    print(configs)
    print()
    
    return configs

