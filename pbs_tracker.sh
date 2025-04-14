#!/bin/bash
#PBS -q normalsl
#PBS -l ncpus=1
#PBS -l walltime=48:00:00
#PBS -l mem=30GB
#PBS -o /home/563/mxj563/pbs_outputs/pbs_tracker.out
#PBS -e /home/563/mxj563/pbs_outputs/pbs_tracker.err
#PBS -m ea
#PBS -M martin.jucker@unsw.edu.au
#PBS -l storage=gdata/up6+gdata/hh5+scratch/up6
#PBS -l wd
#PBS -P zk74

source ~/.bashrc


module use /g/data/hh5/public/modules
module load conda/analysis3-23.10

sh run_all.sh 0020 0059

