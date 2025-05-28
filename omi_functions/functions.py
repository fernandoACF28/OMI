import os 
import h5py
import numpy as np
import pandas as pd
from typing import Tuple
from tqdm import tqdm
from glob import glob as gb
from haversine import haversine, Unit



class OzoneMonitoringInstrument:
    def __init__(self,path: str, index: int, coordinates: Tuple[float,float],
                station_name: str, name_folder: str, year_data: str,
                var_select: str = "ColumnAmountO3", radius: int = None,
                path_finaly_csv: str = None):
        self.path = path
        self.coordinates = coordinates
        self.index = index
        self.station_name = station_name
        self.name_folder = name_folder
        self.year_data = year_data
        self.var_select = var_select
        self.radius = radius
        self.path_finaly_csv = path_finaly_csv
    def extract_omi_csv_from_HDF(self):
        logger = []
        try:
            with h5py.File(self.path,'r') as f:
                try:
                    lat_data = f['HDFEOS/SWATHS/OMI Column Amount O3/Geolocation Fields/Latitude'][:]
                    lon_data = f['HDFEOS/SWATHS/OMI Column Amount O3/Geolocation Fields/Longitude'][:]
                    o3_data = f['HDFEOS/SWATHS/OMI Column Amount O3/Data Fields/' + self.var_select][:]
                    time_data = f['HDFEOS/SWATHS/OMI Column Amount O3/Geolocation Fields/Time'][:]
                except KeyError as e:
                        raise KeyError(f'variable not found HDF5: {str(e)}')
                
                var_path = 'HDFEOS/SWATHS/OMI Column Amount O3/Data Fields/' + self.var_select
                attrs = f[var_path].attrs
                
                fill_value = attrs.get('_FillValue', -1.2676506e+30)
                scale_factor = attrs.get('scale_factor', 1.0)  # Valor padrão 1.0 se não existir
                valid_range = attrs.get('ValidRange', [50, 700])  # Valores padrão para O3
        except Exception as e:
            logger.append(f'Error opening HDF5: {self.path} | {str(e)}')
            return logger
        try: 
            o3_data = o3_data * scale_factor
            o3_data[(o3_data == fill_value) | (o3_data < valid_range[0]) | (o3_data > valid_range[1])] = np.nan
        except: 
            logger.append(f'error in open the file {self.path}')
        try: times = pd.to_datetime(time_data,unit='s',origin='1993-01-01')
        except: times = pd.Series(time_data).astype(str)
        
        if o3_data.ndim == 2: o3_data = o3_data[np.newaxis, :, :]

        results = []
        try:
            if self.radius is not None:
                spatial_mask = np.zeros_like(o3_data[0], dtype=bool)
                for i in range(lat_data.shape[0]):
                    for j in range(lat_data.shape[1]):

                        try: 
                            dist = haversine((lat_data[i,j], lon_data[i,j]), (self.coordinates[0], self.coordinates[1]), unit=Unit.KILOMETERS)
                            if dist <= self.radius:
                                spatial_mask[i,j] = True
                        except: 
                            msg = 'the file dont have lat and lon'+self.path
                            logger.append(msg)
                for t in range(o3_data.shape[0]):
                    time_slice = o3_data[t]
                    valid_values = time_slice[spatial_mask & ~np.isnan(time_slice)]
                    if len(valid_values) > 0:
                        results.append({'time': times[t],
                            f'{self.var_select}_{self.radius}km': np.nanmean(valid_values),
                            f'{self.var_select}_{self.radius}km_std': np.nanstd(valid_values)})
            else:
                dist = np.sqrt((lat_data - self.coordinates[0])**2 + (lon_data - self.coordinates[1])**2)
                idx = np.unravel_index(np.nanargmin(dist), dist.shape)
                for t in range(o3_data.shape[0]):
                    if not np.isnan(o3_data[t, idx[0], idx[1]]):
                        results.append({'time': times[t], f'{self.var_select}_point': o3_data[t, idx[0], idx[1]]})
        except Exception as e:
            raise RuntimeError(f'error in processing spatial data: {str(e)}')
        
        try:
            if not results:
                raise ValueError('Any data was found')

            df = pd.DataFrame(results)
            os.makedirs(self.name_folder, exist_ok=True)
            output_path = os.path.join(self.path_finaly_csv if self.path_finaly_csv else '', 
                                    self.name_folder, 
                                    f'OMTO3_{self.year_data}_{self.station_name}_{self.index}.csv')
            df.to_csv(output_path, index=False)
            return logger
        except: 
            return logger
