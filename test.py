import photonica

datadir = '/home/schwim/Dropbox/Astrophotography/sensor_characterization/-15c/raw_data/'

d = photonica.SensorData()

d.addFiles(datadir)

d.calcStats()
