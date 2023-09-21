def Download_fromECFS(basedate,targetdates, directory_path):
    import datetime
    import os
    import subprocess
    import tarfile
    import glob
    import shutil
    import ftplib
    import schedule
    import time
    
    S2S_filename=f"{basedate}_S2S"
    directory_file = os.path.join(directory_path, S2S_filename)
    if not os.path.exists(directory_file):
        # Create the directory
        os.makedirs(directory_file)
    # Specify the source and destination paths
    year = str(basedate)[:4]
    month = str(basedate)[4:6]
    day = str(basedate)[6:8]
    source_path = f"hpc-login:/ec/res4/scratch/fibl/nemo.{basedate}00.{year}.cf000.tar"
    destination_path = os.path.join(directory_file, f"nemo.{basedate}00.{year}.cf000.tar")
    # Execute the SCP command
    subprocess.call(["scp", source_path, destination_path])
    with tarfile.open(destination_path, 'r') as tar:
        tar.extractall(directory_file)

    # Delete the tar file
    os.remove(destination_path)
    # Store the current working directory
    os.chdir(directory_file)
    for member in os.listdir(directory_file):
        if "f0" in member:
            processed_dir = f"{member}_processed"
            if not os.path.exists(processed_dir):
                os.mkdir(processed_dir)
            os.chdir(member)

            for ifile in os.listdir("."):
                if ifile.startswith("0001_1d_20") and ifile.endswith("_icemod.nc"):
                    print(f"{member}/{ifile}")
                    subprocess.run(["cdo", "selname,iicethic,ileadfra", ifile, f"{directory_file}/{processed_dir}/icevar_{ifile}"])

            os.chdir(f"{directory_file}/{processed_dir}")
            subprocess.run(["cdo", "mergetime", "icevar_0001_1d_20??????_20??????_icemod.nc", "s2s_alltimes.nc"])
            subprocess.run(["cdo", "selindexbox,1,1442,700,1021", "s2s_alltimes.nc", f"s2s_{basedate}_{member}_alltimes_box.nc"])
    os.chdir("..")
    if not os.path.exists("ready"):
        os.mkdir("ready")
    # Specify the source and destination directories
    source_dir = directory_file+"/*_processed"
    destination_dir = directory_file+'/ready'

    # Match the file paths using glob
    file_paths = glob.glob(f"{source_dir}/s2s_20??????_?f0??_alltimes_box.nc")

    # Create symbolic links in the destination directory
    for file_path in file_paths:
        link_name = os.path.join(destination_dir, os.path.basename(file_path))
        os.symlink(file_path, link_name)
    os.chdir(directory_file+'/ready')
    
    for td in targetdates:
        seldate = str(td)

        year = seldate[:4]
        lastyear = str(int(year) - 1)
        month = seldate[4:6]
        day = seldate[6:8]

        print("Selecting date:", seldate)
        for file in os.listdir("."):
            if file.startswith("s2s_20") and file.endswith("_alltimes_box.nc"):
                outfile = f"{file[:18]}_{seldate}_box.nc"
                subprocess.run(["cdo", "seldate,{}-{}-{}T12:00:00".format(year, month, day), file,
                                f"{outfile}"])
    os.chdir('..')
    os.chdir('..')

