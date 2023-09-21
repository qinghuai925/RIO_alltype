def Download_fromFTP(configs):
    import datetime
    import os
    import subprocess
    import tarfile
    import glob
    import shutil
    import ftplib
    import schedule
    import time
    from ftplib import FTP
    # FTP server details
    ftp_host = 'nrt.cmems-du.eu'
    ftp_username = 'xzhang41'
    ftp_password = 'Zxc_19990115'
    ftp_directory = '/Core/ARCTIC_ANALYSIS_FORECAST_PHYS_002_001_a/dataset-topaz4-arc-myoceanv2-be'
    for i in range(len(configs['Dates']['targetdates'])):
        # Pattern for filenames
        filename_pattern = configs['Dates']['targetdates'][i]+'_dm-metno-MODEL-topaz4-ARC-b????????-fv02.0.nc'

        # Connect to the FTP server
        ftp = FTP(ftp_host)
        ftp.login(user=ftp_username, passwd=ftp_password)
        ftp.cwd(ftp_directory)
        if not os.path.exists(configs['output']['output_folder']):
            # Create the directory
            os.makedirs(configs['output']['output_folder'])
        # List files in the directory
        file_list = ftp.nlst()

        # Download files matching the filename pattern
        for file_name in file_list:
            if file_name.endswith('.nc') and file_name.startswith(configs['Dates']['targetdates'][i]+'_dm-metno-MODEL-topaz4-ARC-b'):
                # Download the file
                local_path = os.path.join(configs['output']['output_folder'], file_name)
                with open(local_path, 'wb') as local_file:
                    ftp.retrbinary('RETR ' + file_name, local_file.write)
                print(f"Downloaded: {file_name}")

    # Close the FTP connection
    ftp.quit()
    heredir = configs['output']['output_folder']
    os.chdir(heredir)
    file_paths = glob.glob(f"{heredir}/????????_dm-metno-MODEL-topaz4-ARC-b????????-fv02.0.nc")
    print(heredir)
    processed_dir= configs['Dates']['targetdates'][0]+"_processed"
    if not os.path.exists(processed_dir):
        os.mkdir(processed_dir)
    os.chdir(f"{heredir}/{processed_dir}")
    for ifile in file_paths:
        subprocess.run(["cdo", "selname,fice,hice", ifile, f"{heredir}/{processed_dir}/icevar_{os.path.basename(ifile)}"])
    subprocess.run(["cdo", "mergetime", "icevar_*.nc", "Copernicus_alltimes.nc"])
    os.chdir("..")
    if not os.path.exists("ready"):
        os.mkdir("ready")
    # Specify the source and destination directories
    source_dir = heredir+"/*_processed"
    destination_dir = heredir+'/ready'

    # Match the file paths using glob
    file_path = f"{heredir}/{processed_dir}/Copernicus_alltimes.nc"

    # Create symbolic links in the destination directory

    link_name = os.path.join(destination_dir, os.path.basename(file_path))
    os.symlink(file_path, link_name)
    os.chdir(heredir)
    os.chdir('ready')
    for td in configs['Dates']['targetdates']:
        seldate = td

        year = seldate[:4]
        lastyear = str(int(year) - 1)
        month = seldate[4:6]
        day = seldate[6:8]

        print("Selecting date:", seldate)
        file_pattern = "Copernicus_alltimes.nc"
        files = glob.glob(file_pattern)
        for file in files:
            print(file)
            outfile = file[:10] + "_" + seldate + "_box.nc"
            subprocess.run(["cdo", "seldate,{}-{}-{}T00:00:00".format(year, month, day), file,
                                f"{outfile}"])
