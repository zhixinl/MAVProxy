#!/usr/bin/env python
'''
FalconConnection

This class is used to manage sdk connection.

'''

import sdk
from pymavlink.dialects.v10 import common
import time, os
import threading
from falcon_util import FalconLogWriter
from pymavlink import mavutil
#import traceback

class FalconConnectionManager:

    def __init__(self, mpstate):
        print("FalconConnection __init__ +++")
        self.mpstate = mpstate
        self.__falcon_is_on = False
        self._fake_data = False
        self.logpath = os.path.join(self.mpstate.status.logdir, "falconlog.tlog")
        self.falconlog = FalconLogWriter(self.logpath)   # Open log 
        self.mode = 4
        self.falconlog.hil_log(self.heartbeat_packet_for_mode(self.mode)) # Send a heartbeat packet with default mode of GUIDED.

        # TODO remove me
        if self._fake_data:
            self.lat = -353632608
            self.lon = 1491652351
            self.hdg = 35260

    def create_connection(self, serviceHost, servicePort):
        print("create_connection +++")
        try:
            if self._fake_data is False:
                print "create sdk vehicle"
                self.__vehicle = sdk.Vehicle()
                print "Connecting to Navigation Services @ %s:%d ...\n" % (serviceHost, servicePort)
                # self.vehicle.createConnection(serviceHost, servicePort)
                i = self.__vehicle.create_connection("169.254.248.207", 65101)  # 169.254.149.19
                if i == 0:
                    print("connected sdk")
                    self.__falcon_is_on = True
                else:
                    print("Connection to sdk failed #######")
                    self.__vehicle = None
            else:
                self.__vehicle = sdk.Vehicle()

            # time.sleep(3)
            # start thread to fetch status from SDK
            self.loop_thread = threading.Thread(target=self.read_vehicle_status, name='LoopThread')
            self.loop_thread.start()
            return self.__vehicle
        except:
            print "Failed to connect sdk"

    def read_vehicle_status(self):
        print("read_vehicle_status +++")
        if self._fake_data is True:
            self.__falcon_is_on = True

        while self.__falcon_is_on:
            try:
                if self._fake_data is False:
                    gpsPosition = self.__vehicle.drone_control().gps_position().get_gps_position()
                    # print "Drone GPS position: ", gpsPosition
                    self.lat = gpsPosition['latitude']
                    self.lon = gpsPosition['longitude']
                    height = gpsPosition['height']

                    self.hdg = 35260

                    # print "####### lat: ", self.lat, " lon:", self.lon, " height", height
                else:
                    self.lat += 100  # = -353632608
                    self.lon += 100  # 1491652351
                    self.hdg = 35260

                globalPositionIntMsg = common.MAVLink_global_position_int_message(1000, self.lat, self.lon, 0, 0, 0, 0,
                                                                                  0, self.hdg)
                # dispatch MAVLink packet to other modules
                self.dispatch_status_packet(globalPositionIntMsg)
                globalPositionIntMsg.pack(self.mpstate.master().mav)
                # Write in the log.
                self.falconlog.hil_log(globalPositionIntMsg)
                time.sleep(.3)
            except:
                #traceback.print_exc()
                print "read_vehicle_status failed"
                # break

    def dispatch_status_packet(self, packet):
        try:
            # pass to modules
            for (mod, pm) in self.mpstate.modules:
                if not hasattr(mod, 'hil_packet'):
                    continue
                # try:
                mod.hil_packet(packet)
                # except Exception as msg:
        except:
            print "dispatch status packet failed"

    ''' 
    This method is used to generate HEARTBEAT packet that is going to send flightmode information for the image and the legend.
    It takes custom_mode int values. For more mapping modes look at mode_mapping_acm in mavutil.py
    default custom_mode 4 is GUIDED mode plotted in dark green
    '''
    
    def heartbeat_packet_for_mode(self, custom_mode=4):
        try:
            heartbeat_packet = common.MAVLink_heartbeat_message(mavutil.mavlink.MAV_TYPE_OCTOROTOR, mavutil.mavlink.MAV_AUTOPILOT_GENERIC, mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, custom_mode, 0, 0)
            heartbeat_packet.pack(self.mpstate.master().mav)
            return heartbeat_packet
        except:
            print "heart beat packet generation failed"
     

    def stop_loop_thread(self):
        self.__falcon_is_on = False
