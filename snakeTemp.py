###############################################################
#                      __      ______
#    _________  ____ _/ /_____/_  __/__  ____ ___  ____
#   / ___/ __ \/ __ `/ //_/ _ \/ / / _ \/ __ `__ \/ __ \
#  (__  ) / / / /_/ / ,< /  __/ / /  __/ / / / / / /_/ /
# /____/_/ /_/\__,_/_/|_|\___/_/  \___/_/ /_/ /_/ .___/
#                                              /_/
###############################################################
# Filename: snakeTemp.py
# Author: Jonas Werner (https://jonamiki.com)
# Version: 3.0
###############################################################

import os
import glob
import time
import json
import redis
from influxdb import InfluxDBClient
from datetime import datetime

base_dir        = '/sys/bus/w1/devices/'
locations       = ["DS18b20_hotZoneMat", "DS18b20_coldZoneHide", "DS18b20_midBack", "DS18b20_midFront", "DS18b20_waterbowl"]

# InfluxDB connection details
host        =   "127.0.0.1"
port        =   "8086"
user        =   "someuser"
password    =   "somepass"
dbname      =   "somedb"


# Redis connection details
redisHost   =   "127.0.0.1"
redisPort   =   "6379"


def influxDBconnect():
   influxDBConnection = InfluxDBClient(host, port, user, password, dbname)
   return influxDBConnection


def redisDBconnect():
   redisDBConnection = redis.Redis(host=redisHost, port=redisPort)
   return redisDBConnection


def influxDBwrite(device, sensorName, sensorValue):

   timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

   measurementData = [
       {
           "measurement": device,
           "tags": {
               "gateway": "snakePi2",
               "location": "Tokyo"
           },
           "time": timestamp,
           "fields": {
               sensorName: sensorValue
           }
       }
   ]

   influxDBConnection.write_points(measurementData, time_precision='ms')



def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp():
    lines = read_temp_raw()

    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()

    equals_pos = lines[1].find('t=')

    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c


if __name__ == "__main__":

    influxDBConnection = influxDBconnect()
    redisDBConnection  = redisDBconnect()

    while True:

        for i in range(0,len(locations)):
            device_folder = glob.glob(base_dir + '28*')[i]
            device_file = device_folder + '/w1_slave'

            temp = read_temp()
            print("Temperature at: %s: %s - Index: %s" % (locations[i], temp, i))
            if int(temp) < 80:
               influxDBwrite(locations[i], "Temperature", temp) # Write values to InfluxDB
               redisDBConnection.mset({locations[i]: temp})     # Write values to Redis

        time.sleep(10)
