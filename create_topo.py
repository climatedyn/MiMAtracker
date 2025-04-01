import xarray as xr
import numpy as np

def preprocess(ds):
    '''change the calendar attribute of the time variable'''
    if ds.time.attrs['calendar'] == '360':
        ds.time.attrs['calendar'] = '360_day'
    return ds

ds = xr.open_mfdataset('data/atmos_daily.nc', preprocess=preprocess, decode_times=False)
ds['time'].attrs['units'] = "days since 1959-01-01 00:00:00"
# Avoid conflict when writing file due to encoding attributes: _FillValue is nan, while missing_value is -1.0
del ds['slp'].encoding['_FillValue'] 
ds['slp'].encoding['missing_value'] = -1.0 
# set the topo unit attribute to "M"
ds.topo.attrs['units'] = "M"

# change to float32
for coor in ds.coords:
    ds[coor] = ds[coor].astype(np.float32)
    
# write file
ds.to_netcdf('data/SIM.Mslp.59.3hr.nc',mode='w')
