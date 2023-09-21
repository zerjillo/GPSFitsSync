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

import time, serial
import serial.tools.list_ports
from datetime import datetime, timezone
import threading
import argparse
import sys

rotatingCursor = 0;
rotatingCursorChars = ["-", "\\", "|", "/", "*", "+", "^"]
                       
def printGPSMessage(msg, printIt):  # printIt is a boolean. If false nothing will be printed
    global args
    global rotatingCursor
    global rotatingCursorChars
                       
    if (args.verbose):
        if printIt:
            rotatingCursor = (rotatingCursor + 1) % len(rotatingCursorChars)
            print("                                                                      ", end="\r")
            print(rotatingCursorChars[rotatingCursor] + " " + msg, end="\r")
    
def readGPS(csvFile, gpsPort, baudrate):
    global endThread
    global args
    
    f = open(csvFile, "w")

    ser = serial.Serial(gpsPort, baudrate=baudrate)

    # Open SerialPort
    if not ser.isOpen():
        ser.open()
        
    if (args.verbose):
        print('GPS Time  -  PC Time  -  Latitude,Longitude')

    alreadyBegunToSaveTimes = False
    
    while not endThread:
        line = ser.readline()
        timePc = datetime.now(timezone.utc)
        line2 = line.decode('latin-1').strip()
        #print(line2, end="")
        if line2[0:2] == "$G" and line2[3:6] == "RMC":             #Read the line start with G*RMC
            splitted = line2.split(",")
            valid = splitted[2]
            time = splitted[1]
            date = splitted[9]
            latitude = splitted[3]
            latitudeNS = splitted[4]
            longitude = splitted[5]
            longitudeEW = splitted[6]

            if (len(time) > 0) and (valid == "A"):
                alreadyBegunToSaveTimes = True

                gpsTime = "20" + date[4:6] + "-" + date[2:4] + "-" + date[0:2] + " " + time[0:2] + ':' + time[2:4] + ':' + time[4:]

                pcTime = str(timePc)

                lat = int(latitude[0:2]) + float(latitude[2:]) / 60.0
                if (latitudeNS == "S"):
                    lat = lat * -1

                lon = int(longitude[0:3]) + float(longitude[3:]) / 60.0
                if (longitudeEW == "W"):
                    lon = lon * -1

                print("                                                                                                        ", end="\r")
                print(gpsTime + "  -  " + pcTime + "  -  " + str(lat) + "," + str(lon), end="\r")
                
                f.write(gpsTime + "," + pcTime + "," + str(lat) + "," + str(lon) + "\n")
                f.flush()
            else:
                printGPSMessage(line2, not alreadyBegunToSaveTimes)
        else:
            pass
            #printGPSMessage(line2, not alreadyBegunToSaveTimes)
            
    f.close()
    
    return


def selectGPSPort():
    ports = serial.tools.list_ports.comports()    
    
    if (len(ports) == 0):
        print("No ports detected. Is the GPS connected?")
        sys.exit(-1)
    
    if (len(ports) == 1):
        return ports[0]
    else:
        for n, f in enumerate(ports):
            print(f"%i.- %s" % (n + 1, f))
            
        num = input(f"Select a port (1 - %i): " % len(ports))
        
        try:
            num = int(num) - 1
        except:
            print("No port was selected")
                
            sys.exit(-1)
        
        if (num < 0) or (num > len(ports) - 1):
            print("No port was selected")
            
            sys.exit(-1)
            
        return ports[num]


argParser = argparse.ArgumentParser(prog = 'logGPS.py',
                    description = 'Logs into a CVS file the date and time from an USB GPS compliant wioth the NMEA protocol.',
                    epilog = 'Problems or more info: https://github.com/zerjillo/GPSFitsSync')

argParser.add_argument('-o', '--outputFile', help='File of the CVS file to log data. If not present "gps_xxxxxx.csv" will be created.')
argParser.add_argument("-v", "--verbose", action='store_true', help="Be verbose. Show more info about the process")

args = argParser.parse_args()

if (args.outputFile == None):
    currentDate = str(datetime.now())[:10] + '_' + str(datetime.now())[11:13] + '-' +str(datetime.now())[14:16] + '-' +str(datetime.now())[17:19] 
    csvFile = "gps_" + currentDate + ".csv"
else:
    csvFile = args.outputFile
    


baudrate = 9600



gpsPort = selectGPSPort().device
    
if (args.verbose):
    print(f"Selected GPS port: '%s'" %(gpsPort))


endThread = False
thread = None

thread = threading.Thread(target=readGPS, args=(csvFile, gpsPort, baudrate))

thread.start()

r = input("Press ENTER to stop\n")

endThread = True
