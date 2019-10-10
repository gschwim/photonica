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

Stats tables are pandas dataframes and can be saved out to csv for spreadsheet analysis.

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

 
