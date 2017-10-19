#!/usr/bin/env python
'''
FalconHIL Module

This module is for Intel Falcon 8+ HIL.

'''

from pymavlink import mavutil
import time, os
from falcon_util import FalconLogWriter

from MAVProxy.modules.lib import mp_module
from MAVProxy.modules.lib import mp_settings

from falcon_connection_manager import FalconConnectionManager
from falcon_wp_handler import FalconWPHandler

from pymavlink.dialects.v10 import common


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

        # self._fake_data = True
        self._sdk_connected = False

        logpath = os.path.join(self.mpstate.status.logdir, "falconlog.tlog")
        self.mpstate.falconlog = FalconLogWriter(logpath)  # Open log
        mode = 4
        self.mpstate.falconlog.hil_log(
            self.heartbeat_packet_for_mode(mode))

        self._falcon_connection_manager = FalconConnectionManager(self.mpstate)

        self.connect_falcon("169.254.128.221", 65101)  # 169.254.149.19 / 169.254.248.207

        # add command
        self.FalconHILModule_settings = mp_settings.MPSettings(
            [('verbose', bool, False),
             ])
        self.add_command('falcon', self.cmd_falcon, "falcon commands",
                         ['status', 'set (LOGSETTING)', 'readsystem', 'wp'])

    #TODO move it to background thread?
    def connect_falcon(self, host, port):
        try:
            print "Load falconhil module"
            print "create sdk vehicle"
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
            self.__running_sdk_loop = True
            self.__wp_handler = FalconWPHandler(self.vehicle)
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
            print("$$$$$ falcon wp command")
            self.__wp_handler.handle_wp_commands(args)
        else:
            print self.usage()

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

    def disconnect_falcon(self):
        self.__running_sdk_loop = False
        self._falcon_connection_manager.stop_loop_thread()

    def unload(self):
        print "unload hil module now..."
        # TODO disconnect SDK

        # disconnect sdk
        self.disconnect_falcon()

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

    ''' 
        This method is used to generate HEARTBEAT packet that is going to send flightmode information for the image and the legend.
        It takes custom_mode int values. For more mapping modes look at mode_mapping_acm in mavutil.py
        default custom_mode 4 is GUIDED mode plotted in dark green
        '''

    def heartbeat_packet_for_mode(self, custom_mode=4):
        try:
            heartbeat_packet = common.MAVLink_heartbeat_message(mavutil.mavlink.MAV_TYPE_OCTOROTOR,
                                                                mavutil.mavlink.MAV_AUTOPILOT_GENERIC,
                                                                mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                                                                custom_mode, 0, 0)
            heartbeat_packet.pack(self.mpstate.master().mav)
            return heartbeat_packet
        except:
            print "heart beat packet generation failed"

def init(mpstate):
    '''initialise module'''
    return FalconHILModule(mpstate)
