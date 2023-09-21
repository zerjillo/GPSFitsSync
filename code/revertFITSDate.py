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
from astropy.io import fits
import argparse
import sys
import copy

argParser = argparse.ArgumentParser(prog = 'revertFITSDate.py',
                    description = 'Updates the header of some FITS files to undo the changes that have been made by "updateFITSDate.py". Just in case that something has gone wrong. If the FITS have not been modified by "updateFITSDate.py" no changes are made to the files.',
                    epilog = 'Problems or more info: https://github.com/zerjillo/GPSFitsSync')

argParser.add_argument('directory', help="Directory with the FITS files")
argParser.add_argument("-v", "--verbose", action='store_true', help="Be verbose. Show more info about the process")

args = argParser.parse_args()

folder = args.directory


path = folder + '/*.[fF][iI][tT][sS]'
files = sorted(glob.glob(path))


for file in files:
    if (args.verbose):    
        print(f'Parsing file "%s".' %(file))
    
    hdul = fits.open(file)
    header = hdul[0].header
    
    if (header.get("DATE-OLD") != None):
        if (args.verbose):    
            print(f'  Updating headers.')
            
        header['DATE-OBS'] = header['DATE-OLD']
        header.comments['DATE-OBS'] = header.comments['DATE-OLD']
        
        del header["DATE-OLD"]
        
        if (header.get["LATITUDE"] != None):
            if (header.comments['LATITUDE'] == "Degrees. North positive. Updated with GPS."):
                del header["LATITUDE"]

        if (header.get["LONGITUD"] != None):
            if (header.comments['LONGITUD'] == "Degrees. East positive. Updated with GPS."):
                del header["LONGITUD"]


        # This ugly code is because Astropy.fits does not have a method to remove a line in a HISTORY card
        hist = header['HISTORY']
        
        newHistory = []
        for hi in hist:
            if (hi != "DATE_OLD is the original DATE_OBS. Updated with GPS time."):
                newHistory.append(hi)
                  
        header.remove("HISTORY", remove_all=True)
        
        for hi in newHistory:
            header.add_history(hi)

        if (args.verbose):
            print(f'  Saving file: %s' % (file)) 
        
        hdul.writeto(file, overwrite=True)
        
    else:
        if (args.verbose):    
            print(f'  The file was not modified by "updateFITSDate.py". Ignoring.')

    hdul.close()
