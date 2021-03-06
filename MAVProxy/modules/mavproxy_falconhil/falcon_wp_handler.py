#!/usr/bin/env python
'''
FalconWPHandler

This class is used to handle WP commands.

'''

import sdk
import csv
import time
from ast import literal_eval
import threading
from ast import literal_eval
import csv
import sys
import traceback

from pymavlink.dialects.v10 import common
from pymavlink import mavutil


class FalconWPHandler:
    
    def __init__(self, vehicle, mpstate):
        print("create FalconWPHandler +++")
        self.__vehicle = vehicle
        self.mpstate = mpstate

    def handle_wp_commands(self, args):
        print("###handle_wp_commands +++")
        print("###handle_wp_commands: wp args: %s" % args)
        for i in range(len(args)):
            print("### handle_wp_commands args[%d] is %s" % (i, args[i]))
            print("#### handle_wp_commands args:", args[i])

        if args[1] == "start_motor":
            print("###wp start_motor")
            self.__vehicle.mission_manager().start_motors()
        elif args[1] == "stop_motor":
            print("wp stop_motor")
            self.__vehicle.mission_manager().stop_motors()
        elif args[1] == "start_flight":
            print("wp start_flight")
            self.__vehicle.mission_manager().start_flight()
        elif args[1] == "stop_flight":
            print("wp stop_flight")
            self.__vehicle.mission_manager().stop_flight()
        elif args[1] == "pause_flight":
            print("wp pause_flight")
            self.__vehicle.mission_manager().pause_flight()
        elif args[1] == "come_home":
            print("wp come_home")
            self.__vehicle.mission_manager().come_home()
        elif args[1] == 'append_waypoint':
            print("##### handle_wp_commands: append_waypoint ", args[2])
            print args[2]
            self.__vehicle.mission_manager().append_waypoint(args[2])
        elif args[1] == 'load_mission':
            print("mission file is %s" % args[2])
            self.load_mission(args[2])

        elif args[1] == "fly_to_waypoint":
            print("####wp fly_to_waypoint")
            # self.mission_thread = threading.Thread(target=self.fly_mission, name='MissionThread')
            # self.mission_thread.start()

            self.__vehicle.mission_manager().fly_to_waypoint()

    def load_mission(self, filename):
        try:
            with open(filename, 'rb') as csvfile:
                print("open csv successfully")
                reader = csv.reader(csvfile, delimiter=' ', quotechar='|')
                print("read csv successfully")
                for row in reader:
                    l = []
                    if(not row == []):
                        p = [x for x in row[0].split(',')]
                    else:
                        continue
                    for y in range(len(p)):
                        [l.append(int(p[y]))
                         if isinstance(literal_eval(p[y]), int) is True
                         else l.append(float(p[y]))]
                    print("######load_mission: append points list:", l)
                    self.__vehicle.mission_manager().append_waypoint(l)

                    self.log_waypoint(l[1], l[0]-1, l[2], l[3], l[4], 0)
                print("### load_mission: call start_fligh now")
                self.__vehicle.mission_manager().start_flight()

        except IOError as error:
            print("fly falcon mission failed")
    def fly_mission(self):
        print("fly_mission +++")
        with open('waypoints.csv', 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=' ', quotechar='|')
            for row in reader:
                l = []
                p = [x for x in row[0].split(',')]
                for y in range(len(p)):
                    [l.append(int(p[y]))
                     if isinstance(literal_eval(p[y]), int) is True
                     else l.append(float(p[y]))]
                print("fly to point: ", l[0], l[1], l[2],
                                                          l[3], l[4], l[5],
                                                          l[6], l[7], l[8],
                                                          l[9], l[10],
                                                          l[11], l[12])
                self.__vehicle.mission_manager().fly_to_waypoint(l[0], l[1], l[2],
                                                          l[3], l[4], l[5],
                                                          l[6], l[7], l[8],
                                                          l[9], l[10],
                                                          l[11], l[12])
                time.sleep(1.5)

    def log_waypoint(self, wpType, seq, lat, lon, height, holdTime):
        # Convert ACI way point data to MAVLink form, then create a MAVLink way point message and add it to our log
        # Do we need to convert the lat, lon, height?
        try:
            frame = 3  # Can we deduce coordinate space from wpType, wpEvent, or flags?
            command = 16  # Can we deduce command from wpType, wpEvent, or flags?
            current = 0  # Can we deduce current from wpType, wpEvent, or flags?
            autoContinue = 1  # Can we deduce autoContinue from wpType, wpEvent, or flags?

            mission_packet = common.MAVLink_mission_item_message(255, 0, seq, frame, command, current, autoContinue,
                                                                 0.0, 0.0, 0.0, 0.0, lat, lon, height)
            mission_packet.pack(self.mpstate.master().mav)
            self.mpstate.falconlog.hil_log(mission_packet)
        except:
            print "Failed to create the mission packet"
            traceback.print_exc()
