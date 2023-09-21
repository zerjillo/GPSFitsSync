#!/usr/bin/env python
#
# Copyright 2023 Sergio Alonso & Javier Flores
#
# This file is part of GPSFitsSync.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import glob
from datetime import datetime
from astropy.io import fits
import argparse
import sys

def getComputerTime(time, computerTimes):
    for index, t in enumerate(computerTimes):
        #print (t)
        #print(time)
        if (t > time):
            return index - 1
        
    return None
        
def selectFile(files):
    if (len(files) == 1):
        return files[0]
    else:
        for n, f in enumerate(files):
            print(f"%i.- %s" % (n + 1, f))
            
        num = input(f"Select a file (1 - %i): " % len(files))
        
        try:
            num = int(num) - 1
        except:
            print("No file was selected")
                
            sys.exit(-1)
        
        if (num < 0) or (num > len(files) - 1):
            print("No file was selected")
            
            sys.exit(-1)
            
        return files[num]

argParser = argparse.ArgumentParser(prog = 'updateFITSDate.py',
                    description = 'Updates the header of some FITS files with a corrected GPS time. The GPS time is got for a CSV file. See "GPS-logger.py" to create the CSV file.',
                    epilog = 'Problems or more info: https://github.com/zerjillo/GPSFitsSync')

argParser.add_argument('directory', help="Directory with the CSV file and FITS files")
argParser.add_argument("-s", "--suffix", help="Suffix of the updated files. If not present, the original files will be updated.")
argParser.add_argument("-v", "--verbose", action='store_true', help="Be verbose. Show more info about the process")

args = argParser.parse_args()



folder = args.directory
createCopy = False
path = folder + r'/*.[cC][sS][vV]'
files = glob.glob(path)

if (len(files) == 0):
    print(f"No CSV files found in '%s'" % folder)
    
    sys.exit(-1)
    
csvfile = selectFile(files)

if (args.verbose):
    print(f'Using "%s" for the GPS log.' % (csvfile))

with open(csvfile) as f:
    lines = f.readlines()
    
gpsTimes = []
computerTimes = []
latitudes = []
longitudes = []

for line in lines:
    #print(line, end="")
    
    gpsTime, computerTime, latitude, longitude = line.split(",")
    
    #print(gpsTime)
    gpsTime = datetime.strptime(gpsTime+"+00:00", "%Y-%m-%d %H:%M:%S.%f%z")
    computerTime = datetime.strptime(computerTime.strip(), "%Y-%m-%d %H:%M:%S.%f%z")
    #print(computerTime)
    
    gpsTimes.append(gpsTime)
    computerTimes.append(computerTime)
    latitudes.append(latitude)
    longitudes.append(longitude.strip())

if (args.verbose):
    print(f"Found %i GPS times." % len(gpsTimes))

path = folder + '/*.[fF][iI][tT][sS]'
files = sorted(glob.glob(path))

latitude = latitudes[int(len(latitudes) / 2)]
longitude = longitudes[int(len(longitudes) / 2)]

for file in files:
    if (args.verbose):    
        print(f'Parsing file "%s".' %(file))
    
    hdul = fits.open(file)
    header = hdul[0].header
    
    fitsTime = header['DATE-OBS']
        
    dotPosition = fitsTime.rfind(".")
    
    if (dotPosition != -1):
        aux = fitsTimeDecimalPlaces = len(fitsTime) - dotPosition
        if (fitsTimeDecimalPlaces > 7):
            fitsTime = fitsTime[:7-(fitsTimeDecimalPlaces)]
    

    fitsTime = datetime.strptime(fitsTime+"+00:00", "%Y-%m-%dT%H:%M:%S.%f%z")
    
    if (args.verbose):
        print(f'  DATE-OBS: %s' % (fitsTime))
    
    idTime = getComputerTime(fitsTime, computerTimes)
       
    if (idTime == None):
        print(f'"%s" DATE_OBS is not in the CSV times. Maybe GPS was not being logged when the image was taken.' % file)
    else:
        if (args.verbose):
            print(f'  Computer-log: %s < %s < %s' % (computerTimes[idTime], fitsTime, computerTimes[idTime + 1]))
        
        interval = computerTimes[idTime + 1] - computerTimes[idTime] 
        shift = fitsTime - computerTimes[idTime]
        perc = shift / interval
        
        if (args.verbose):
            print(f'  Position in interval: %f' % (perc))
            
        if (args.verbose):
            print(f'  GPS-log: %s < %s' % (gpsTimes[idTime], gpsTimes[idTime + 1]))
            
        interval = gpsTimes[idTime + 1] - gpsTimes[idTime]
        
        newTime = gpsTimes[idTime] + interval * perc
        newTime = newTime.strftime("%Y-%m-%dT%H:%M:%S.%f")
        
        if (args.verbose):
            print(f'  GPS update time: %s' % (newTime))
        

        # Updating HEADER            
        header['DATE-OLD'] = header['DATE-OBS']
        header.comments['DATE-OLD'] = header.comments['DATE-OBS']
        header['HISTORY'] = "DATE_OLD is the original DATE_OBS. Updated with GPS time."

        header['DATE-OBS'] = newTime
        header.comments['DATE-OBS'] = 'UTC time, updated with GPS time'

        header['LATITUDE'] = latitude
        header.comments['LATITUDE'] = "Degrees. North positive. Updated with GPS."

        header['LONGITUD'] = longitude
        header.comments['LONGITUD'] = "Degrees. East positive. Updated with GPS."

        
        if (args.suffix):
            savingFile = str(file) + str(args.suffix)
        else:
            savingFile = file
            
        if (args.verbose):
            print(f'  Saving file: %s' % (savingFile)) 
        
        hdul.writeto(savingFile, overwrite=True)
    hdul.close()
