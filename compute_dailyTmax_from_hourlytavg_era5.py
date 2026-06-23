import xarray as xr
import matplotlib.pyplot as plt
import numpy as np

import pandas as pd
from datetime import datetime
import flox


dz = xr.open_dataset('/home/ghervieux/SCRIPTS/GEV/era5_global_time_zone.nc')
time_zone = xr.zeros_like(dz['time_zone']).astype('int')

time_zone.loc[{'lat':dz['lat'],'lon':np.arange(180.00,202.25+0.25,0.25)}] = -12 + 3
time_zone.loc[{'lat':dz['lat'],'lon':np.arange(202.25,247.25+0.25,0.25)}] = - 9 + 3
time_zone.loc[{'lat':dz['lat'],'lon':np.arange(247.25,292.25+0.25,0.25)}] = - 6 + 3
time_zone.loc[{'lat':dz['lat'],'lon':np.arange(292.25,337.25+0.25,0.25)}] = - 3 + 3
time_zone.loc[{'lat':dz['lat'],'lon':np.arange(337.25,359.57+0.25,0.25)}] = - 0 + 3

time_zone.loc[{'lat':dz['lat'],'lon':np.arange( 0    , 22.25+0.25,0.25)}] = 0 + 3
time_zone.loc[{'lat':dz['lat'],'lon':np.arange( 22.25, 67.25+0.25,0.25)}] = 3 + 3
time_zone.loc[{'lat':dz['lat'],'lon':np.arange( 67.25,112.25+0.25,0.25)}] = 6 + 3
time_zone.loc[{'lat':dz['lat'],'lon':np.arange(112.25,157.25+0.25,0.25)}] = 9 + 3
time_zone.loc[{'lat':dz['lat'],'lon':np.arange(157.25,179.75+0.25,0.25)}] = 12 + 3


for year in range(1941,2026+1):

  ds = xr.open_mfdataset([f'/Projects/era5/monolevel/tmax.2m.{iyear}.nc' for iyear in [year-1,year,year+1]])
  ds = ds.sel(time=slice(f'{year-1}-12-30',f'{year+1}-01-01'))
  ds = ds.load()

  anntime=ds['time'].sel(time=slice(f'{year}-01-01',f'{year}-12-31'))
  tmax = xr.zeros_like(ds['tmax'].sel(time=anntime).groupby(anntime.dt.dayofyear).mean())

  for tz in np.unique(time_zone.values):
    offset = tz
    local_time = ds['time'] + np.timedelta64(offset, 'h')
    air_tz = ds['tmax'].where(time_zone == tz)
    air_tz = air_tz.assign_coords(local_time=local_time)
    air_tz = air_tz.swap_dims({"time": "local_time"})
    air_tz = air_tz.sel(local_time=slice(f'{year}-01-01',f'{year}-12-31'))
    local_day = air_tz.local_time.dt.dayofyear

    tmax = xr.where(time_zone == tz,air_tz.groupby(local_day).max("local_time"),tmax)



  tmax.attrs['long_name'] = ds['tmax'].attrs['long_name'].replace('3-hourly','daily')
  tmax.attrs['units'] = ds['tmax'].attrs['units']
  tmax.attrs['standard_name'] = ds['tmax'].attrs['standard_name']
  tmax.attrs['description'] = 'computed from 3-hourly with solar day time'

  dsout = tmax.to_dataset(name='tmax')

  dsout = dsout.swap_dims({"dayofyear": "time"})
  dsout['time'] = anntime.resample(time='1D').mean()
  # Define encoding to use 'days since' units
  time_encoding = { "time": {"units": "days since 1900-01-01",\
                            "calendar": "proleptic_gregorian",\
                            "dtype": "float64"}}
  outfile = f'/Projects/RAPrototype/ERA5/SolarDayTime/tmax.2m.{year}.FromSolarDayTime.nc'
  dsout.to_netcdf(outfile,unlimited_dims=["time"],encoding=time_encoding)
