# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from astropy.io import fits
from astropy import units
from astropy.nddata import Cutout2D
import os


class SensorData:

    def __init__(self, cropsize=(100, 100), pedestal=10000,
                 offset_correction=0):

        self.cropsize = cropsize
        self.pedestal = pedestal
        self.offset_correction = offset_correction


        # set up the data structures

        self.data_set = pd.DataFrame()

        # this is for the individual subs as they are read in
        self.data_set = pd.DataFrame(columns=[
            'file',                     # file name
            'img_type',                 # frame type - light, dark, bias, flat
            'exptime',                  # exposure time
            'ccd_temp',                 # exposure ccd temp
            'ff_geometry',              # full frame geometry
            'crop_geometry',            # crop geometry
            'offset',                   # this is the bias crop signal
            'min',                      # minimum value of the crop
            'max',                      # maximum value of the crop
            'signal',                   # average value of the crop
            'std_dev',                  # standard deviation of the crop
            'signal-offset',            # signal of a single frame - bias offset
            'data',                     # raw data of crop
        ])

        # analysis table derived from data_set
        #self.data_summary = pd.DataFrame(columns=[
        self.data_summary_cols = [
            'ccd_temp',             # exposure ccd temp
            'exptime',              # exposure time
            'img_type',             # frame type - light, dark, bias, flat
            'avg_signal',           # data_set.signal.mean()
            'avg_signal-offset',    # data_set
            'avg_std_dev',
            'delta_std_dev',        # (sub1 + 5000) - sub2
            'total_noise',          # data_set.std_dev.mean()
            'shot+read',              # std_dev_delta.sqrt()
            'read(DN)',
            'FPN',
            'sig_shot',
            'offset_correction'
            ]

    def addFile(self, file):

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
        crop_size = units.Quantity(self.cropsize, units.pixel)  # crop to 100x100
        img_crop = Cutout2D(img_data, crop_center, crop_size)  # makes the crop

        # stuff in a pd.Series
        data_record = pd.Series({
            'file': file.split('/')[-1],
            'img_type': img_type,
            'ff_geometry': img_data.shape,
            'crop_geometry': img_crop.shape,
            'exptime': img_header[0].header['EXPTIME'],
            'ccd_temp': img_header[0].header['CCD-TEMP'],
            'min': np.min(img_crop.data),
            'max': np.max(img_crop.data),
            'signal': np.mean(img_crop.data),
            'std_dev': np.std(img_crop.data),
            'data': img_crop.data
        })

        # append to self.data_set
        self.data_set = self.data_set.append(data_record, ignore_index=True)

    def addFiles(self, datapath):

        count = 0
        # discover the fits files in the directory
        files = os.listdir(datapath)

        # add them to the SensorData object
        for file in files:
            if '.fit' in file:
                infile = os.path.join(datapath, file)



                self.addFile(infile)
                print('Added file: {}'.format(file))
                count += 1

        print('Added {} files.'.format(count))

    def getBiasStats(self):

        d = self.data_set
        self.BiasStats = d.loc[d.img_type == 'bias', :]\
            .groupby('ccd_temp').mean()

    def calcStats(self):

        d = self.data_set

        # get the bias stats
        self.getBiasStats()
        offset = self.BiasStats.signal
        readDN = self.BiasStats.std_dev

        # add offset, signal-offset, read(DN) to data_set

        for temp, val in offset.iteritems():
            d.loc[d['ccd_temp'] == temp, 'offset'] = \
                offset[temp]

            d.loc[d['ccd_temp'] == temp, 'signal-offset'] = \
                d.signal - val - self.offset_correction

            d.loc[d['ccd_temp'] == temp, 'read(DN)'] = \
                readDN[temp]

        # group by ccd_temp & exptime
        g = d.groupby(['ccd_temp', 'exptime'])

        # build the  summary df called ds
        ds = pd.DataFrame()

        # get stats for each group
        for x in g.groups:

            # this would be a bias sub
            if x[1] < 1:
                continue

            # extract the rows for the group
            grp = g.get_group(x)

            # create a pd.Series
            h = pd.Series()
            h.loc['ccd_temp'] = x[0]
            h.loc['exptime'] = x[1]
            h.loc['img_type'] = grp.iloc[0].img_type

            # avg_signal-offset
            h.loc['avg_signal'] = grp['signal'].mean()
            h.loc['avg_signal-offset'] = grp['signal-offset'].mean()

            # avg_std_dev, delta_std_dev
            h.loc['avg_std_dev'] = grp['std_dev'].mean()
            h.loc['delta_std_dev'] = \
                ((grp.iloc[-1].loc['data'] + self.pedestal) -
                    grp.iloc[0].loc['data']).std()

            # total_noise
            h.loc['total_noise'] = grp['std_dev'].mean()

            # shot+read
            h.loc['shot+read'] = h.loc['delta_std_dev'] / np.sqrt(2)

            # read(DN)
            h.loc['read(DN)'] = self.BiasStats.loc[x[0], 'std_dev']

            # FPN
            h.loc['FPN'] = np.sqrt(h.loc['total_noise'] ** 2 -
                                   h.loc['shot+read'] ** 2)

            # sig_shot
            h.loc['sig_shot'] = np.sqrt(h.loc['shot+read'] ** 2 -
                                        h.loc['read(DN)'] ** 2)

            # offset correction
            h.loc['offset_correction'] = self.offset_correction

            # append to ds
            ds = ds.append(h, ignore_index=True)

        self.data_set = d.sort_values(by=['ccd_temp', 'exptime'])
        # self.data_summary = self.data_summary.append(ds, ignore_index=True) \
        #     .sort_values(by=['ccd_temp', 'exptime'])
        self.data_summary = \
            ds.sort_values(by=['ccd_temp', 'exptime']) \
            .reindex(columns=self.data_summary_cols)

