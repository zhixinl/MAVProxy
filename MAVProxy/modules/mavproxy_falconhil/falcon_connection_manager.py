#!/usr/bin/env python
'''
FalconConnection

This class is used to manage sdk connection.

'''

import sdk
from pymavlink.dialects.v10 import common
import time
import threading


class FalconConnectionManager:

    def __init__(self, mpstate):
        print("FalconConnection __init__ +++")
        self.mpstate = mpstate
        self.__falcon_is_on = False
        self._fake_data = True

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
                i = self.__vehicle.create_connection("169.254.149.19", 65101)
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
                time.sleep(.3)
            except:
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

    def stop_loop_thread(self):
        self.__falcon_is_on = False
