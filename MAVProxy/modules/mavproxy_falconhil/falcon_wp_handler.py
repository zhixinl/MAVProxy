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


class FalconWPHandler:
    
    def __init__(self, vehicle):
        print("create FalconWPHandler +++")
        self.__vehicle = vehicle

    def handle_wp_commands(self, args):
        print("handle_wp_commands +++")
        print("wp args: %s" % args)
        for i in range(len(args)):
            print("args[%d] is %s" % (i, args[i]))

        if args[1] == "start_motor":
            print("###wp start_motor")
            # self.__vehicle.mission_manager().start_motors()
        elif args[1] == "stop_motor":
            print("wp stop_motor")
            # self.__vehicle.mission_manager().stop_motors()
        elif args[1] == "start_flight":
            print("wp start_flight")
            # self.__vehicle.mission_manager().start_fight()
        elif args[1] == "stop_flight":
            print("wp stop_flight")
            # self.__vehicle.mission_manager().stop_fight()
        elif args[1] == "pause_flight":
            print("wp pause_flight")
            # self.__vehicle.mission_manager().pause_fight()
        elif args[1] == "come_home":
            print("wp come_home")
            # self.__vehicle.mission_manager().come_home()
        elif args[1] == "fly_to_waypoint":
            print("####wp fly_to_waypoint")
            self.mission_thread = threading.Thread(target=self.fly_mission, name='MissionThread')
            self.mission_thread.start()

            # self.__vehicle.mission_manager().fly_to_waypoint()

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
                # vehicle.mission_manager().append_waypoint(*l)
                # vehicle.mission_manager().append_waypoint(l[0], l[1], l[2],
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