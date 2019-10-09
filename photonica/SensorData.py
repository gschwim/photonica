# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from astropy.io import fits
from astropy import units
from astropy.nddata import Cutout2D


class SensorData:

    def __init__(self, cropsize=(100, 100)):

        self.cropsize = cropsize

        # set up the data structures
        self.data_set = pd.DataFrame(columns=[
            'file',                     # file name
            'img_type',                 # frame type - light, dark, bias, flat
            'ff_geometry',              # full frame geometry
            'crop_geometry',            # crop geometry
            'exptime',                  # exposure time
            'CCD-TEMP',                 # exposure ccd temp
            'data'                      # raw data of crop
            'min',
            'max',
            'signal',
            'std_dev',
            # TODO
            # 'std_dev_delta',
            # 'Offset',
            # 'Signal - Offset',
            # 'Average Signal - Offset',
            # 'Total Noise',
            # 'Shot + RD',
            # 'Read DN',
            # 'FPN',
            # 'Shot Signal',
        ])

    def add_file(self, file):

        # verify the file exists

        # read the header and data
        img_header = fits.open(file)
        img_data = fits.getdata(file)

        # determine file type
        # TODO flesh this out
        if img_header[0].header['PICTTYPE'] == 2:
            img_type = 'bias'
        elif img_header[0].header['PICTTYPE'] == 3:
            img_type = 'dark'
        else:
            img_type = 'undefined'

        # perform the crop
        crop_center = ((img_data.shape[1] / 2), (img_data.shape[0] / 2))  # center of full image
        crop_size = units.Quantity((100,100), units.pixel)  # crop to 100x100
        img_crop = Cutout2D(img_data, crop_center, crop_size)  # makes the crop

        # stuff in a pd.Series
        data_record = pd.Series({
            'file': file.split('/')[-1],
            'img_type': img_type,
            'ff_geometry': img_data.shape,
            'crop_geometry': img_crop.shape,
            'exptime': img_header[0].header['EXPTIME'],
            'CCD-TEMP': img_header[0].header['CCD-TEMP'],
            'min': np.min(img_crop.data),
            'max': np.max(img_crop.data),
            'signal': np.mean(img_crop.data),
            'std_dev': np.std(img_crop.data),
            'data': img_crop.data
        })

        # append to self.data_set
        self.data_set = self.data_set.append(data_record, ignore_index=True)

