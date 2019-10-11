import photonica

# source directory for fits images here
datadir = '/home/schwim/Dropbox/Astrophotography/sensor_characterization/data'

d = photonica.SensorData(offset_correction=100)

d.addFiles(datadir)

d.calcStats()

# ### outputs the two tables as csv

# per-sub stats
d.data_set.drop(columns=['data']).to_csv('./data_set.csv')

# summary data w/ noise characteristics
d.data_summary.to_csv('./data_summary.csv')
