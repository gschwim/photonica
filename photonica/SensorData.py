# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from astropy.io import fits
from astropy import units
from astropy.nddata import Cutout2D
import os


class SensorData:

    def __init__(self, cropsize=(100, 100)):

        self.cropsize = cropsize
        self.pedestal = 5000
        self.offset_correction = 0


        # set up the data structures

        self.data_set = pd.DataFrame()

        # this is for the individual subs as they are read in
        # self.data_set = pd.DataFrame(columns=[
        #     'file',                     # file name
        #     'img_type',                 # frame type - light, dark, bias, flat
        #     'ff_geometry',              # full frame geometry
        #     'crop_geometry',            # crop geometry
        #     'exptime',                  # exposure time
        #     'ccd_temp',                 # exposure ccd temp
        #     'data',                     # raw data of crop
        #     'offset',                   # this is the bias crop signal
        #     'min',                      # minimum value of the crop
        #     'max',                      # maximum value of the crop
        #     'signal',                   # average value of the crop
        #     'std_dev',                  # standard deviation of the crop
        #     'sub_signal-offset',    # signal of a single frame - bias offset

            # TODO - this should be in a summary dataframe for each type
            # 'avg_signal-offset',        # avg signal of multiple frames - bias offset

            # TODO
            # 'std_dev_delta',
            # 'Total Noise',
            # 'Shot + RD',
            # 'Read DN',
            # 'FPN',
            # 'Shot Signal',
        # ])

        # # analysis table derived from data_set
        # self.data_summary = pd.DataFrame(columns=[
        #     'img_type',             # frame type - light, dark, bias, flat
        #     'ff_geometry',          # full frame geometry
        #     'crop_geometry',        # crop geometry used
        #     'exptime',              # exposure time
        #     'ccd_temp',             # exposure ccd temp
        #     'offset',               # this is the bias crop signal
        #     'avg_min',              # data_set.min.mean()
        #     'avg_max',              # data_set.max.mean()
        #     'avg_signal',           # data_set.signal.mean()
        #     'avg_signal-offset'     # data_set
        #     'total_noise',          # data_set.std_dev.mean()
        #     'std_dev_delta',        # (sub1 + 5000) - sub2
        #     'shot+rd',              # std_dev_delta.sqrt()

        #     ])

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
        crop_size = units.Quantity((100,100), units.pixel)  # crop to 100x100
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

        # add signal-offset and read(DN) to data_set

        for temp, val in offset.iteritems():
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

            # create a pd.Series
            h = pd.Series()
            h.loc['ccd_temp'] = x[0]
            h.loc['exptime'] = x[1]

            # extract the rows for the group
            grp = g.get_group(x)

            # delta_std_dev
            h.loc['delta_std_dev'] = \
                ((grp.iloc[-1].loc['data'] + self.pedestal) -
                    grp.iloc[0].loc['data']).std()

            # avg_signal-offset
            h.loc['avg_signal-offset'] = grp['signal-offset'].mean()

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

            # append to ds
            ds = ds.append(h, ignore_index=True)

        self.data_set = d
        self.data_summary = ds
