# MiMAtracker
Specific structure and suite of codes to run Melbourne University Tracker on MiMA output.

This assumes a very specific file structure for MiMA output:
- MiMA is run in yearly chunks, and stored in folders according to iteration.
- MiMA is run with Julian calendar and does not include full century years like year 100, year 1500, year 2000, etc. This is because that would make a difference to the Gregorian calendar used in the Melbourne Tracker.
- `MiMAtracker` is placed as a directory under the run directory, i.e. at same level as each yearly output, and contains all files in this repository
    - run directory/
        - MiMAtracker/
        - 0000/
            - 0000.atmos_6hr.nc
        - 0001/
            - 0001.atmos_6hr.nc
        - 0002/
            - 0002.atmos_6hr.nc
        - ...

The main run script is `run_all.sh`, which has some important variables stored at the beginning:
- `ROOTDIR`: MiMA's run directory as described above. By default this is `../` as per above file structure. But the tracker can also be run anywhere as long as `ROOTDIR` points to the data.
- `TRACKVAR`: Which variable to track (mean sea level or geopotential height). By default, this is `Mslp`, and any other choice would need adjustments throughout the script.
- `FREQ`: MiMA output frequency in hours. This is set to 6 and would need adjusting of `incycloc` and `intrack` templates. `FREQ` is used to find output files `atmos_${FREQ}hr.nc` and file templates.
- `SIM`: name of simulation. This is again used to find file templates and create output file names.
- `YEAR`: calendar year of the first output file in `0000/`. The actual year is then `YEAR` plus the name of the ouput directory (0000,0001,0002,...).
- `FILE_TRUNK`: generic filename to find output files. in above file tree, this is `atmos_${FREQ}hr.nc`.

There are two inputs:
- `$1`: index of first simulation file to track. This is of form XXXX and corresponds to iterations 0000,0001,0002, etc.
- `$2`: index of last simulation file to track. Same form as `$1`
The iterations `$1` to `$2` will be tracked. This structure offers the possibility to run tracking for each year in parallel.

## Requirements
These scripts run in `bash` and `python` and require `nco` and `xarray`. 
