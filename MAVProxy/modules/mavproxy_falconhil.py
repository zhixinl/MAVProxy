#!/usr/bin/env python
'''
FalconHIL Module

This module is for Intel Falcon 8+ HIL.

'''

import os
import os.path
import sys
from pymavlink import mavutil
import errno
import time
import sdk
import pdb
import threading
import time


from MAVProxy.modules.lib import mp_module
from MAVProxy.modules.lib import mp_util
from MAVProxy.modules.lib import mp_settings

# vehicle = sdk.Vehicle()
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

        # connect falcon sdk
        try:
            print "create sdk vehicle"
            self.vehicle = sdk.Vehicle()
            # print "Connecting to Navigation Services @ %s:%d ...\n" %(serviceHost, servicePort)
            print "Connecting to Navigation Services @169.254.248.207:65101 ...\n"
            # pdb.set_trace()
            # self.vehicle.createConnection("169.254.248.207", 65101)
            self.vehicle.createConnection("169.254.248.207", 65101)
            time.sleep(2)
            # vehicle.createConnection("169.254.248.207", 65101)
            print "connected sdk"
            # self.vehicle.createConnection(serviceHost, servicePort)

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
            # print "Connecting to Navigation Services @127.0.0.1:3000 ...\n"
            # pdb.set_trace()
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
                mod.hil_packet("hello from hil")
                # except Exception as msg:
        except:
            print "dispatch status packet failed"

    def read_veichle_status(self):
        while(self.__running_sdk_loop):
            gpsState = self.vehicle.droneState().droneGPSState().getGPSState()
            print "Drone GPS state: ", gpsState
            #
            gpsPosition = self.vehicle.droneControl().droneGPSPosition().getGPSPosition()
            print "Drone GPS position: ", gpsPosition

            # TODO create MAVLink packet based on what we received from SDK

            # dispatch MAVLink packet to other modules
            self.dispatch_status_packet("hello from hil")
            time.sleep(1)



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
            self.say("%s: %s" % (self.name,message))
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
