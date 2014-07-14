#!/usr/bin/env python
# coding: utf-8
from grk_pyping import ping
import sys
import getopt
from pprint import pprint
import urllib2
import xml.etree.ElementTree as ET
import logging
from datetime import datetime, timedelta
import time

sys.stderr.write("Checking for SNM940 being connected, ")
SNM940="192.168.88.3"
#SNM940="192.168.253.15"
#SNM940="cell.snm940.com"

GOOGLE="8.8.8.8"

timeout = 1500
download_timeout=30
count = 3
packet_size = 55
udp = True
Test_Size="100K"
Test_Size="1MB"
#Test_Size="5MB"
Test_File=Test_Size+".tst"
sleep_between=15

download_time_100K=0

result=ping(SNM940, timeout=2000, packet_size=packet_size, count=2, quiet_output=True, udp=udp)


if result.packet_lost == 2:
   sys.stderr.write("\nError: Could not detect device at "+SNM940+". \n")
   quit()
else:
   sys.stderr.write("Detected\n")

sys.stderr.write("Checking for internet access, ")

result=ping(GOOGLE, timeout=timeout, packet_size=packet_size, count=3, quiet_output=True, udp=udp)
if result.packet_lost == 3:
   sys.stderr.write("\nError: Could not check the connection to "+GOOGLE+". \n")
   quit()
else :
   sys.stderr.write("Connected\n")

sys.stderr.write("Starting measurement\n") #Bell

Lat="0"
Long="0"
Height=0.0
H_Precision=0.0

while True:
    starttime=time.time()
    try:

# We do the ping first to bracket the GPS information
# This all really should be done at once of course

#        sys.stderr.write("Checking Ping, ")
        result=ping(GOOGLE, timeout=timeout, packet_size=packet_size, count=count, quiet_output=True, udp=udp)
#        sys.stderr.write("Finished\n")


#        sys.stderr.write("Getting GPS,")
        reply=urllib2.urlopen("http://"+SNM940+"/telematics/request?get=CellRSSI&get=CellNetworkSpeedCurrent&get=CellNetworkSpeedsAllowed&get=CellSignalStrengthPercentage&get=CellSignalStrengthBars&get=GPSALL",None,10).read()
#        sys.stderr.write("Got GPS\n")
# The reply is of the following
        """
<Telematics>
  <CellRSSI>-65</CellRSSI>
  <CellNetworkSpeedCurrent>3G</CellNetworkSpeedCurrent>
  <CellNetworkSpeedsAllowed>2G,3G</CellNetworkSpeedsAllowed>
  <CellSignalStrengthPercentage>77</CellSignalStrengthPercentage>
  <CellSignalStrengthBars>4</CellSignalStrengthBars>
  <GPSUTC>Sun Jun  1 04:30:58 2014</GPSUTC>
  <GPSLat>40.2954736</GPSLat>
  <GPSLong>-104.9979583</GPSLong>
  <GPSAlt>1510.7830000</GPSAlt>
  <GPSAccuracy>2.6100000</GPSAccuracy>
</Telematics>
        """
        doc = ET.fromstring(reply)
#        ET.dump(doc)

        Lat=doc.find("GPSLat").text.strip()
        Long=doc.find("GPSLong").text.strip()
        Height=float(doc.find("GPSAlt").text.strip())
        H_Precision=float(doc.find("GPSAccuracy").text.strip())
        Current=doc.find("CellNetworkSpeedCurrent").text.strip()
        Allowed=doc.find("CellNetworkSpeedsAllowed").text.strip()
        Percent=doc.find("CellSignalStrengthPercentage").text.strip()
        Bars=doc.find("CellSignalStrengthBars").text.strip()
        RSSI=doc.find("CellRSSI").text.strip()


        try:
            gettime=time.time()
            sys.stderr.write("Downloading http://trimbletools.com/100K.tst, ")
            bytes_down_100K=0

            reply=urllib2.urlopen("http://trimbletools.com/100K.tst",None,download_timeout);
            timeout_time=gettime+download_timeout;
            downloaded=True
            while reply.read(1):
                current_time=time.time()
                bytes_down_100K+=1
                if current_time > timeout_time :
                    sys.stderr.write("Timed out. Downloaded {:.1f}K\n".format(bytes_down_100K/1024))
                    downloaded=False
                    download_time_100K=-1
                    download_time_1MB=-2
                    break

#                print "Got data"
            if downloaded :
                download_time_100K=current_time-gettime
                sys.stderr.write("Downloaded in {:.1f}s.\n".format(download_time_100K))
                try:
                    sys.stderr.write("Downloading http://trimbletools.com/1MB.tst, ")
                    bytes_down_1MB=0
                    reply=urllib2.urlopen("http://trimbletools.com/1MB.tst",None,download_timeout)
                    gettime=time.time()
                    timeout_time=gettime+download_timeout;
                    downloaded=True
                    while reply.read(1):
                        current_time=time.time()
                        bytes_down_1MB+=1
                        if current_time > timeout_time :
                            downloaded=False
                            download_time_1MB=-1
                            download_rate_1MB=bytes_down_1MB/(current_time-gettime)/1024
                            sys.stderr.write("Timed out. {}s Downloaded {:.1f}K, Rate: {:.1f}\n".format(download_timeout,(bytes_down_1MB/1024),download_rate_1MB))
                            break

                    if downloaded :
                        download_time_1MB=current_time-gettime
                        download_rate_1MB=bytes_down_1MB/download_time_1MB/1024
                        sys.stderr.write("Downloaded in {:.1f}s., Rate: {:.1f} \n".format(download_time_1MB,download_rate_1MB))

                except :
                    download_rate_1MB=-20
                    download_rate_1MB=-1
                    sys.stderr.write("Failed to connect\n")
                    print "{},{},{},{},{},-1".format(starttime,Lat,Long,Height,H_Precision)
                    sys.stdout.flush()

        except :
#            e = sys.exc_info()[0]
#            pprint (e)
            download_time_100K=-10
            download_time_1MB=-2
            sys.stderr.write("Failed!!!\n")


#        print "{},{},{},{},{},{},{},{},\"{}\",{},{},{},{},{},{},{}".format(starttime,Lat,Long,Height,H_Precision, download_time_100K,download_time_1MB,Current,Allowed,RSSI,Bars,Percent,count-result.packet_lost,result.min_rtt,result.avg_rtt,result.max_rtt)

        print "{},{},{},{:.3f},{:.3f},{:.1f},{:.1f},{},\"{}\",{},{},{},{},{},{},{}".format(starttime,Lat,Long,Height,H_Precision, download_time_100K,download_rate_1MB,Current,Allowed,RSSI,Bars,Percent,count-result.packet_lost,result.min_rtt,result.avg_rtt,result.max_rtt)
        sys.stdout.flush()

    except (KeyboardInterrupt, SystemExit):
        sys.stdout.flush()
        quit()
    except:
#        sys.stderr.write("Failed to get GPS\n")
        print "{},{},{},{},{},-1".format(starttime,Lat,Long,Height,H_Precision)
        time.sleep(1)

    sys.stderr.write("Location complete, move on\n") #Bell
    sys.stderr.write(chr(7)) #Bell
    time.sleep (sleep_between)
    sys.stderr.write("Stop\n") #Bell
    sys.stderr.write(chr(7)) #Bell
    sys.stderr.write(chr(7)) #Bell
    time.sleep (5)
    sys.stderr.write("Starting measurement\n") #Bell
    sys.stdout.flush()



