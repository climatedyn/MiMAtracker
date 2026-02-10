#!/bin/bash
#set -e
#set -x

ROOTDIR=..
TRACKVAR=Mslp # variable to track
FREQ=6 # data frequency in hours
SIM=$1 # name of simulation
INDS=$2 # XXXX index of first simulation file. gives name of folder containing output files
INDE=$3 # XXXX index of last simulation file. gives name of folder containing output files
YEAR=1960 # calendar year of zero index simulation file. could be same as INDS
# if time period includes year 2000, the dates in output file tracks_2000.dat file should be checked and corrected if necessary
FILE_TRUNK=atmos_${FREQ}hr.nc # generic filename for simulation output files

SECONDS=0  # to time script


# Load necessary module
module load nco
mkdir -p outputs
mkdir -p tracks
mkdir -p data

FIRST_YR=$(( $YEAR+$(printf "%g" $INDS) ))
LAST_YR=$(( $YEAR+$(printf "%g" $INDE) ))

PREV="none"
# Loop over each input file
for i in $(seq -f "%04g" $INDS $INDE); do
    ii=$(printf "%g" $i)
    let INDX=$YEAR+$ii
    echo "iteration $i, year $INDX"
    input_file="${ROOTDIR}/${i}/${i}.${FILE_TRUNK}"
    output_file="data/${SIM}.${TRACKVAR}.${INDX}.${FREQ}hr.nc"
    outtrack_file="tracks/tracks_${INDX}.dat"

    
    # Extract necessary variables and convert time format
    ncks -O -v zsurf,slp "$input_file" "$output_file"
    ncap2 -s "time=float(time)" "$output_file" -O "$output_file"
    
    # get December from year before
    let j=$ii-1
    IND_MINUS=$(printf "%04g" $j)
    PREV="${ROOTDIR}/${IND_MINUS}/${IND_MINUS}.${FILE_TRUNK}"
    if [ -f $PREV ]
    then
	ncks -d time,-124, -v slp,zsurf ${PREV} tmp.nc
	ncrcat -O tmp.nc $output_file $output_file
	rm tmp.nc
	let BEF=$INDX-1
    else
	BEF=${INDX}
    fi
    
    python convert_calendar.py -i $output_file -u $YEAR -o tmp.nc #$output_file
    mv tmp.nc $output_file
    
    #echo "Running run_nc2cmp.topo : convert .nc topography file to cmp file format"
    ncrename -v .zsurf,topo "$output_file"
    #./run-nc2cmp.topo SIM > /dev/null 2>&1
    ./run-nc2cmp.topo ${SIM} ${INDX} ${TRACKVAR} ${FREQ}hr > outputs/output_run-nc2cmp.topo_${i}.log 2>&1  # save output log

    #echo "Running run-nc2cmp : convert .nc pressure data file to cmp file format"
    ./run-nc2cmp ${SIM} ${INDX} ${TRACKVAR} ${FREQ}hr > outputs/output_run-nc2cmp_${i}.log 2>&1

    # set year in tracker inputs
    cp namelists/incycloc.${FREQ}hr.0S incycloc.tmp
    cp namelists/intrack.${FREQ}hr intrack.tmp
    TWOYRS=$(( $BEF - $BEF/100*100 ))
    sed -i "s/YY/${TWOYRS}/" incycloc.tmp
    sed -i "s/YY/${TWOYRS}/g" intrack.tmp
    TWOYRS=$(( $INDX - $INDX/100*100 ))
    sed -i "s/ZZ/${TWOYRS}/" incycloc.tmp
    sed -i "s/ZZ/${TWOYRS}/g" intrack.tmp
    if [[ $BEF == $INDX ]]
    then
	MONTH="01"
    else
	MONTH="12"
    fi
    sed -i "s/MM/${MONTH}/" incycloc.tmp
    sed -i "s/MM/${MONTH}/" intrack.tmp
    
    #echo "Running run-cyc : identify the cyclone locations in the given input data set"
    ./run-cyc ${SIM} ${INDX} 0S ${TRACKVAR} > outputs/output_run-cyc_${i}.log 2>&1

    #echo "Cleaning tracks : replace '********' by '  999999' in cyclone tracks"
    python clean_tracks.py -i out.${TRACKVAR}_${SIM}/cycdat.${SIM}.${INDX}.0S -o out.${TRACKVAR}_${SIM}/cycdat.${SIM}.${INDX}.0S

    #echo "Running run-trk : connects cyclone locations to full cyclone tracks"
    ./run-trk ${SIM} ${INDX} no no 0S ${TRACKVAR} > outputs/output_run-trk_${i}.log 2>&1

    #echo "Running maketracks_UM.awk"
    touch "$outtrack_file"
    awk -f maketracks_UM.awk trackfile > "$outtrack_file"

    echo "Finished processing $input_file, output saved to $outtrack_file"
done

cd tracks
tar -czf MiMA_cyclonetracks_cmip6_surface_${SIM}_None_${FIRST_YR}${LAST_YR}.tar.gz tracks_*.dat
mv *.tar.gz ../

# cleaning up
rm -rf data topo tracks out.Mslp_${SIM} cmp_${SIM}

# Convert SECONDS to minutes and seconds
elapsed_min=$((SECONDS / 60))
elapsed_sec=$((SECONDS % 60))
echo "Total execution time: ${elapsed_min}m:${elapsed_sec}s"
