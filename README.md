# GPSFitsSync
Some python scripts to synchornize astronomical observations with cheap GPS devices.

+ ``logGPS.py``: connects to an USB GPS and records a log of computer times + GPS time.
+ ``updateFITSDate.py``: updates the headers of all FITS files in a folder adjusting the DATE-OBS according to the GPS time recorded by ``logGPS.py``.
+ ``revertFITSDate.py``: reverts any changes done by ``updateFITSDate.py`` to the headers of the FITS files in a folder.
