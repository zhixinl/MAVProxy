#!/usr/bin/env python
'''
FalconWPHandler

This class is used to handle WP commands.

'''

import sdk


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
            print("wp start_motor")
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
            print("wp fly_to_waypoint")
            # self.__vehicle.mission_manager().fly_to_waypoint()