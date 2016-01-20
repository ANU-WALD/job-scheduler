# -*- coding: utf-8 -*-
"""
Created on Wed May 20 19:02:52 2015

@author: adh157
"""
import datetime 

import numpy as np

from osgeo import gdal
from osgeo import gdalconst
from osgeo import osr

short_names = ["rad", "tmax", "tmin", "precip"]
kelvin_to_celcius_offset = - 273.15
joules_to_megajoules_scale = (1e-6)
metres_to_mm_scale = 1000
no_data_value = -9999


    
#    % Create dimensions
#    timedimID = netcdf.defDim(ncid,'time',1);
#    latdimID = netcdf.defDim(ncid,'latitude',mappar.rows);
#    londimID = netcdf.defDim(ncid,'longitude',mappar.cols);
#    dimids = [londimID latdimID timedimID];
#    
#    % Create variables for assigning data to
#    varid = netcdf.defVar(ncid, var, 'NC_FLOAT', dimids);
#    timevarid = netcdf.defVar(ncid, 'time', 'NC_LONG', timedimID);
#    latvarid = netcdf.defVar(ncid, 'latitude', 'NC_FLOAT', latdimID);
#    lonvarid = netcdf.defVar(ncid, 'longitude', 'NC_FLOAT', londimID);
#
#    % Put attributes on variables
#    netcdf.putAtt(ncid,varid,'_FillValue',single(nodatavalue));
#    netcdf.putAtt(ncid,varid,'long_name',long_name);
#    netcdf.putAtt(ncid,varid,'units',unit);
#    netcdf.putAtt(ncid,timevarid,'long_name','time');
#    netcdf.putAtt(ncid,timevarid,'units','days since 1800-01-01 0:0:0');
#    netcdf.putAtt(ncid,latvarid,'long_name','latitude');
#    netcdf.putAtt(ncid,latvarid,'units','degrees_north');
#    netcdf.putAtt(ncid,lonvarid,'long_name','longitude');
#    netcdf.putAtt(ncid,lonvarid,'units','degrees_east');

##ERA-Int Vars
#    Vars.long_names={'Surface_solar_radiation_downwards';
#    'Maximum_temperature_at_2_metres_since_previous_post-processing';
#    'Minimum_temperature_at_2_metres_since_previous_post-processing';
#    'Total_precipitation'};
#Vars.short_names={'rad'; 'tmax'; 'tmin'; 'precip'};
#Vars.out_units={'MJ m-2'; 'degC'; 'degC'; 'mm'};

##FC Vars    
#    Vars.long_names={   'Net_Short-Wave_Radiation_Flux_Surface';
#    'Temperature';
#    'Temperature';
#    'Total_precipitation'};
#Vars.short_names={'NETrad'; 'tmax'; 'tmin'; 'precip'};
#Vars.out_units={'MJ m-2'; 'degC'; 'degC'; 'mm'};

def flatten_netcdf(input_filename, output_filename, param_short_name):
    #Open the file
    ds_in = gdal.Open(input_filename)
    rasterband = ds_in.GetRasterBand(1)
    scale = rasterband.GetScale()
    offset = rasterband.GetOffset()
    fillValue = rasterband.GetNoDataValue()

    hoursSince1900 = int(rasterband.GetMetadataItem('NETCDF_DIMENSION_time'))
    ref_date = datetime.datetime(1900, 01, 01, 0, 0, 0)
    data_date = ref_date + datetime.timedelta(hours=hoursSince1900)
    
    data = ds_in.ReadAsArray()
    no_data_mask = (np.any((data == fillValue), axis=0))
    
    #Scale and offset
    data = data * scale + offset
    
    #Flatten the data
    if param_short_name == "rad":
        flat = data.sum(axis = 0) * joules_to_megajoules_scale
        short_name = 'rad'
        long_name = 'Surface solar radiation downwards'
        unit = 'MJ m-2'
    if param_short_name == "NETrad":
        flat = data.sum(axis = 0) * joules_to_megajoules_scale
        short_name = 'NETrad'
        long_name = 'Net Short-Wave Radiation Flux Surface'
        unit = 'MJ m-2'
    elif param_short_name == "tmax":
        flat = data.max(axis = 0) + kelvin_to_celcius_offset
        short_name = 'tmax'
        long_name = 'Maximum temperature at 2 metres since previous post-processing'
        unit = 'degC'
    elif param_short_name == "tmin":
        flat = data.min(axis = 0) + kelvin_to_celcius_offset
        short_name = 'tmin'
        long_name = 'Minimum temperature at 2 metres since previous post-processing'
        unit = 'degC'
    elif param_short_name == "precip":
        flat = data.sum(axis = 0) * metres_to_mm_scale
        short_name = 'precip'
        long_name = 'Total precipitation'
        unit = 'mm'

    flat = flat.astype(np.float32)
    flat[no_data_mask] = no_data_value
        
    #Save the file
    x, y = ds_in.RasterXSize, ds_in.RasterYSize
    driver = ds_in.GetDriver()
    ds_out = driver.Create(output_filename, x, y, 1, gdal.GDT_Float32)
    ds_out.SetGeoTransform(ds_in.GetGeoTransform())
    band_out = ds_out.GetRasterBand(1)
    
    band_out.SetMetadataItem('NETCDF_VARNAME', short_name)
    band_out.SetMetadataItem('long_name', long_name)
    
    ref_date_out = datetime.datetime(1800, 01, 01, 0, 0, 0)
    date_diff = data_date - ref_date_out
    daysSince1800 = str(date_diff.days)
    band_out.SetMetadataItem('NETCDF_DIMENSION_time', daysSince1800)
    band_out.SetMetadataItem('NETCDF_time_units', 'days since 1800-01-01 0:0:0')

    band_out.SetMetadataItem('units', unit)
    band_out.SetNoDataValue(no_data_value)

    band_out.WriteArray(flat)
    band_out.FlushCache()
    
    ds_out.GetMetadata()
    
    band_out = None
    ds_out = None

if __name__ == '__main__':
    f_in = '/home/157/adh157/tmax_20131204.nc'
    f_out = '/home/157/adh157/tmax_20131204_flat.nc'
    flatten_netcdf(f_in, f_out, 'tmax')
