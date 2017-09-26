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

class FalconHILModule(mp_module.MPModule):
    def __init__(self, mpstate):
        """Initialise module"""
        super(FalconHILModule, self).__init__(mpstate, "falconhil", "Falcon 8+ HIL")
        self.status_callcount = 0
        self.boredom_interval = 10 # seconds
        self.last_bored = time.time()

        self.packets_mytarget = 0
        self.packets_othertarget = 0
        self.verbose = False

        self._fake_data = False

        #TODO remove me
        if(self._fake_data):
            self.lat = -353632608
            self.lon = 1491652351
            self.hdg = 35260


        # connect falcon sdk
        try:
            if self._fake_data is False:
                print "create sdk vehicle"
                self.vehicle = sdk.Vehicle()
                # print "Connecting to Navigation Services @ %s:%d ...\n" %(serviceHost, servicePort)
                print "Connecting to Navigation Services @169.254.248.207:65101 ...\n"
                self.vehicle.createConnection("169.254.248.207", 65101)
                time.sleep(2)
                print "connected sdk"

            self.__running_sdk_loop = True

            # start thread to fetch status from SDK
            self.loop_thread = threading.Thread(target=self.read_veichle_status, name='LoopThread')
            self.loop_thread.start()
        except:
            print "Failed to connect sdk"


        # add command

        self.FalconHILModule_settings = mp_settings.MPSettings(
            [ ('verbose', bool, False),
          ])
        self.add_command('falcon', self.cmd_falcon, "falcon commands", ['status','set (LOGSETTING)', 'readsystem'])

    def start_sdk(self, serviceHost, servicePort):
        # connect falcon sdk
        try:
            print "create sdk vehicle"
            self.vehicle = sdk.Vehicle()
            print "Connecting to Navigation Services @ %s:%d ...\n" % (serviceHost, servicePort)
            # self.vehicle.createConnection("127.0.0.1", 3000)
            self.vehicle.createConnection(serviceHost, servicePort)

            # start thread to fetch status from SDK
            self.loop_thread = threading.Thread(target=self.read_veichle_status, name='LoopThread')
            self.loop_thread.start()
        except:
            print "Failed to connect sdk"

    def usage(self):
        '''show help on command line options'''
        return "Usage: falcon <status|set|readsystem>"

    def cmd_falcon(self, args):
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
            self.say("call read system info command") #goto gui-console
            print "call readsystem command - print" # goto console
            self.mpstate.console.writeln("call readsystem command - mpstate.console.writeln") #goto gui-console
            # dsi = self.vehicle.droneSystemInfo().getSystemInfo()

            # self.dispatch_status_packet("hello from hil")
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

    def read_veichle_status(self):
        while(self.__running_sdk_loop):
            try:
                if self._fake_data is False:
                    # gpsState = self.vehicle.droneState().droneGPSState().getGPSState()
                    # print "Drone GPS state: ", gpsState
                    # #
                    gpsPosition = self.vehicle.droneControl().droneGPSPosition().getGPSPosition()
                    # print "Drone GPS position: ", gpsPosition
                    self.lat = gpsPosition['latitude']
                    self.lon = gpsPosition['longitude']
                    height = gpsPosition['height']

                    # self.lon -= 4294967276

                    # print "####### lat: ", self.lat, " lon:", self.lon, " height", height
                else:
                    self.lat += 100 # = -353632608
                    self.lon += 100 # 1491652351
                    self.hdg = 35260

                globalPositionIntMsg = common.MAVLink_global_position_int_message(1000, self.lat, self.lon, 0, 0,0,0,0, self.hdg)
                type = globalPositionIntMsg.get_type()
                # print "type is: ", type

                # dispatch MAVLink packet to other modules
                # self.dispatch_status_packet("hello from hil")
                self.dispatch_status_packet(globalPositionIntMsg)
                time.sleep(.3)
            except:
                print "read_veichile_status failed"


    # def create_mavlink_msg(self):
        # global_position_int_encode ?

        # time_boot_ms, lat, lon, alt, relative_alt, vx, vy, vz, hdg
        # globalPositionIntMsg = common.MAVLink_global_position_int_message(1000)


    def status(self):
        '''returns information about module'''
        self.status_callcount += 1
        self.last_bored = time.time() # status entertains us
        return("status called %(status_callcount)d times.  My target positions=%(packets_mytarget)u  Other target positions=%(packets_mytarget)u" %
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
        if now-self.last_bored > self.boredom_interval:
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
