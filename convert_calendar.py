import xarray as xr
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-i',dest='inFile')
parser.add_argument('-o',dest='outFile')
parser.add_argument('-u',dest='unitYear')
args = parser.parse_args()

ds = xr.open_dataset(args.inFile)
for attr in ['calendar_type','calendar']:
    if attr in ds.time.attrs:
        del ds.time.attrs[attr]
ds.to_netcdf(args.outFile,encoding={'time':{'dtype':"float32",'units':'days since {0}-01-01'.format(args.unitYear),'calendar':'standard'}})
