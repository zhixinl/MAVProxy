#!/usr/bin/env python
"""
FalconConnection

This class is used to manage sdk connection.
"""

import sdk
from pymavlink.dialects.v10 import common
import time
import threading
import traceback


class FalconConnectionManager:

    def __init__(self, mpstate):
        print("FalconConnection __init__ +++")
        self.mpstate = mpstate
        self.__falcon_is_on = False
        self.__fake_data = False

        # Fake data with GPS position info of Bayland Park, Sunnyvale CA USA
        if self.__fake_data:
            self.lat = 374118550
            self.lon = -1219942040
            self.hdg = 35260

    def create_connection(self, service_host, service_port):
        print("create_connection +++")
        try:
            if self.__fake_data is False:
                print "create sdk vehicle"
                self.__vehicle = sdk.Vehicle()
                print "Connecting to Navigation Services @ %s:%d ...\n" % (service_host, service_port)
                i = self.__vehicle.create_connection(service_host, service_port)
                if i == 0:
                    print("connected sdk")
                    self.__falcon_is_on = True
                else:
                    print("Connection to sdk failed #######")
                    self.__vehicle = None
            else:
                self.__vehicle = sdk.Vehicle()

            time.sleep(3)

            # start thread to fetch status from SDK
            self.loop_thread = threading.Thread(target=self.read_vehicle_status, name='LoopThread')
            self.loop_thread.start()
            return self.__vehicle
        except:
            print "Failed to connect sdk"

    def read_vehicle_status(self):
        print("read_vehicle_status +++")
        if self.__fake_data is True:
            self.__falcon_is_on = True

        while self.__falcon_is_on:
            try:
                if self.__fake_data is False:
                    gps_position = self.__vehicle.drone_control().gps_position().get_gps_position()
                    self.lat = gps_position['latitude']
                    self.lon = gps_position['longitude']
                    height = gps_position['height']
                    self.lon *= 1.0e+7
                    self.lat *= 1.0e+7
                    self.lon -= 4294967276  # subtracting 2^32

                    self.hdg = 35260
                else:
                    self.lat -= 25
                    self.lon -= 100
                    self.hdg = 35260

                uint16_max = 65535
                current_time = time.time()
                milli_sec = int(round((current_time - self.mpstate.sim_start_time_sec) * 1000))
                micro_sec = int(round(current_time * 1000000))
                global_position_int_msg = common.MAVLink_global_position_int_message(
                        1000, int(self.lat), int(self.lon), 20000, 20000, 0, 0, 0, self.hdg)

                # dispatch MAVLink packet to other modules
                self.dispatch_status_packet(global_position_int_msg)

                #VFR_HUD message needed to get location from the mavlink utility. Fields needed are:
                #'airspeed' in m/s (float), 'groundspeed' in m/s float, 'heading' degrees in compass units (0...360, 0=north) int16_t, 'throttle' uint16_t (1 to 100), 'alt' in meters float, 'climb' m/s float
                vfr_hud_msg = common.MAVLink_vfr_hud_message(5.05, 5.05, int(self.hdg*0.01), 30, 20.0, 1.5)
                vfr_hud_msg.pack(self.mpstate.master().mav)

                #GPS_RAW_INT message needed to get location from the mavlink utility. Fields needed are:
                #'time_usec' in microseconds uint64_t, 'fix_type' in GPS_FIX_TYPE enum uint8_t, 'lat' in degrees (lat*1e7) int32_t, 'lon' in degrees (lat*1e7) int32_t, 'alt' in m (*1000) int32_t, 'eph' if unknown set to UNIT16_MAX, 'epv' if unknown set to UNIT16_MAX, 'vel' m/s *100 uint16_t, 'cog' if unknown set to UNIT16_MAX, 'satellites_visible' uint8_t if unknown set to 255.
                gps_raw_int_msg = common.MAVLink_gps_raw_int_message(
                        1000, 4, int(self.lat), int(self.lon), 30000, uint16_max, uint16_max, 300, uint16_max, 255)
                gps_raw_int_msg.pack(self.mpstate.master().mav)

                global_position_int_msg.pack(self.mpstate.master().mav)

                system_time_msg = common.MAVLink_system_time_message(micro_sec, milli_sec)
                system_time_msg.pack(self.mpstate.master().mav)
                #print (len(self.mpstate.mav_outputs))
                for r in self.mpstate.mav_outputs:
                    r.write(vfr_hud_msg.get_msgbuf())
                    r.write(gps_raw_int_msg.get_msgbuf())
                    r.write(system_time_msg.get_msgbuf())
                    r.write(global_position_int_msg.get_msgbuf())

                # Write in the log.
                self.mpstate.falconlog.hil_log(global_position_int_msg)

                time.sleep(.3)
            except:
                traceback.print_exc()
                print "read_vehicle_status failed"

    def dispatch_status_packet(self, packet):
        try:
            # pass to modules
            for (mod, pm) in self.mpstate.modules:
                if not hasattr(mod, 'hil_packet'):
                    continue
                mod.hil_packet(packet)
        except:
            print "dispatch status packet failed"

    def stop_loop_thread(self):
        self.__falcon_is_on = False
