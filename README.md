=========
photonica
=========

Camera performance analyser presented as python module pythonica. 

References for this process can be found in the references folder.

Thank you to Richard Crisp for sharing the analysis process.

Use
--------

Reference test_run.py for the basic workflow. In short:

* create a SensorData object
* run the addFiles() method to import the files
* run the calcStats() method to build the stats tables

Stats tables are pandas dataframes and can be saved out to csv for spreadsheet analysis. These tables are as follows:

* data_set - individual frame stats, includes:
** file name
** img_type - bias, dark, flat, light, established from the fits header
** exptime - exposure time, fits header
** ccd_temp - ccd temperature, fits header
** ff_geometry - measured geometry of the full image matrix
** crop_geometry - crop used for analysis
** offset - per the procedure
** min - min measured value in the crop
** max - max
** signal - mean value of the crop
** std_dev - standard deviation of the crop
** signal-offset - per the procedure
** read(DN) - per the procedure
** data - raw data from the crop

* data_summary - aggregated results by temperature and exposure time




NOTE: when creating the SensorData object you can set cropsize, offset_correction, and pedestal values as follows:

```python
x = photonica.SensorData(cropsize=(500,500), offset_correction=150, pedestal=10000)
```

Features
--------

* Loads fits files, auto-crops, builds statistics table
* Runs noise analysis on data, grouped by temperature and exposure

TODO
--------

 * Verify proper counts of each file type
 * Minimum Practical Exposure Time calculation
 * graphing
 * full report generation

 
