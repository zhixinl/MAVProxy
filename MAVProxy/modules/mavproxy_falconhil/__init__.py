#!/usr/bin/env python
'''
FalconHIL Module

This module is for Intel Falcon 8+ HIL.

'''

import sys
from pymavlink import mavutil
import sdk
import threading
import time
from pymavlink.dialects.v10 import common

from MAVProxy.modules.lib import mp_module
from MAVProxy.modules.lib import mp_util
from MAVProxy.modules.lib import mp_settings

from falcon_connection_manager import FalconConnectionManager
from falcon_wp_handler import FalconWPHandler


class FalconHILModule(mp_module.MPModule):
    def __init__(self, mpstate):
        """Initialise module"""
        super(FalconHILModule, self).__init__(mpstate, "falconhil", "Falcon 8+ HIL")
        self.status_callcount = 0
        self.boredom_interval = 10  # seconds
        self.last_bored = time.time()

        self.packets_mytarget = 0
        self.packets_othertarget = 0
        self.verbose = False

        self._fake_data = True
        self._sdk_connected = False

        self._falcon_connection_manager = FalconConnectionManager()

        # TODO remove me
        if self._fake_data:
            self.lat = -353632608
            self.lon = 1491652351
            self.hdg = 35260

        self.start_sdk("169.254.149.19", 65101)

        # self.__wp_handler = FalconWPHandler()

        # add command
        self.FalconHILModule_settings = mp_settings.MPSettings(
            [('verbose', bool, False),
             ])
        self.add_command('falcon', self.cmd_falcon, "falcon commands",
                         ['status', 'set (LOGSETTING)', 'readsystem', 'wp'])

    def start_sdk(self, host, port):
        try:
            print "Load falconhil module"
            if self._fake_data is False:
                print "create sdk vehicle"
                # self.vehicle = sdk.Vehicle()
                # print "Connecting to Navigation Services @169.254.248.207:65101 ...\n"
                # i = self.vehicle.create_connection("169.254.149.19", 65101)
                # if i == 0:
                #     print("connected sdk")
                # else:
                #     print("Connection to sdk failed #######")

                # self.vehicle = self._falcon_connection_manager.create_connection("169.254.149.19", 65101)
                self.vehicle = self._falcon_connection_manager.create_connection(host, port)
                if self.vehicle is None:
                    print("connection to sdk failed ****")
                    return
                else:
                    print("connected sdk")

                # TODO check connection success or not
                self._sdk_connected = True

                time.sleep(2)
                print "connected sdk"
            else:
                self.vehicle = sdk.Vehicle()

            self.__running_sdk_loop = True
            self.__wp_handler = FalconWPHandler(self.vehicle)

            # start thread to fetch status from SDK
            self.loop_thread = threading.Thread(target=self.read_vehicle_status, name='LoopThread')
            self.loop_thread.start()

        except:
            print "Failed to connect sdk"

    def usage(self):
        '''show help on command line options'''
        return "Usage: falcon <status|set|readsystem>"

    def cmd_falcon(self, args):
        # if self._sdk_connected is False:
        #     print("Connect SDK first")
        #     return

        '''control behaviour of the module'''
        self.say("enter cmd_falcon")
        print("enter cmd_falcon - print")
        self.mpstate.console.writeln("enter cmd_falcon - mpstate.console.writeln")
        if len(args) == 0:
            print self.usage()
        elif args[0] == "status":
            print self.status()
        elif args[0] == "set":
            self.say("call set command with arg %s" % (args[1]))
            self.FalconHILModule_settings.command(args[1:])
        elif args[0] == "readsystem":
            self.say("call read system info command")  # goto gui-console
            print "call readsystem command - print"  # goto console
            self.mpstate.console.writeln("call readsystem command - mpstate.console.writeln")  # goto gui-console
            # dsi = self.vehicle.droneSystemInfo().getSystemInfo()

            # self.dispatch_status_packet("hello from hil")
        elif args[0] == "wp":
            print("falcon wp command")
            self.__wp_handler.handle_wp_commands(args)
        else:
            print self.usage()

    def dispatch_status_packet(self, packet):
        try:
            # pass to modules
            for (mod, pm) in self.mpstate.modules:
                if not hasattr(mod, 'hil_packet'):
                    continue
                # try:
                # mod.hil_packet("hello from hil")
                mod.hil_packet(packet)
                # except Exception as msg:
        except:
            print "dispatch status packet failed"

    def read_vehicle_status(self):
        while (self.__running_sdk_loop):
            try:
                if self._fake_data is False:
                    # gpsState = self.vehicle.droneState().droneGPSState().getGPSState()
                    # print "Drone GPS state: ", gpsState
                    # #
                    # gpsPosition = self.vehicle.droneControl().droneGPSPosition().getGPSPosition()
                    gpsPosition = self.vehicle.drone_control().gps_position().get_gps_position()
                    # print "Drone GPS position: ", gpsPosition
                    self.lat = gpsPosition['latitude']
                    self.lon = gpsPosition['longitude']
                    height = gpsPosition['height']

                    # self.lon -= 4294967276
                    self.hdg = 35260

                    # print "####### lat: ", self.lat, " lon:", self.lon, " height", height
                else:
                    self.lat += 100  # = -353632608
                    self.lon += 100  # 1491652351
                    self.hdg = 35260

                globalPositionIntMsg = common.MAVLink_global_position_int_message(1000, self.lat, self.lon, 0, 0, 0, 0,
                                                                                  0, self.hdg)
                # type = globalPositionIntMsg.get_type()
                # print "type is: ", type

                # dispatch MAVLink packet to other modules
                self.dispatch_status_packet(globalPositionIntMsg)
                time.sleep(.3)
            except:
                print "read_vehicle_status failed"

    def status(self):
        '''returns information about module'''
        self.status_callcount += 1
        self.last_bored = time.time()  # status entertains us
        return (
        "status called %(status_callcount)d times.  My target positions=%(packets_mytarget)u  Other target positions=%(packets_mytarget)u" %
        {"status_callcount": self.status_callcount,
         "packets_mytarget": self.packets_mytarget,
         "packets_othertarget": self.packets_othertarget,
         })

    def boredom_message(self):
        if self.FalconHILModule_settings.verbose:
            return ("I'm very bored")
        return ("I'm bored")

    def stop_loop_thread(self):
        self.__running_sdk_loop = False

    def unload(self):
        print "unload hil module now..."
        # TODO disconnect SDK

        # stop loop thread
        self.__running_sdk_loop = False

    def idle_task(self):
        '''called rapidly by mavproxy'''
        now = time.time()
        if now - self.last_bored > self.boredom_interval:
            self.last_bored = now
            message = self.boredom_message()
            # self.say("%s: %s" % (self.name,message))
            # See if whatever we're connected to would like to play:
            self.master.mav.statustext_send(mavutil.mavlink.MAV_SEVERITY_NOTICE,
                                            message)

    def mavlink_packet(self, m):
        '''handle mavlink packets'''
        if m.get_type() == 'GLOBAL_POSITION_INT':
            if self.settings.target_system == 0 or self.settings.target_system == m.get_srcSystem():
                self.packets_mytarget += 1
            else:
                self.packets_othertarget += 1


def init(mpstate):
    '''initialise module'''
    return FalconHILModule(mpstate)
