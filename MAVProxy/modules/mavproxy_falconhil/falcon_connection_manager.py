#!/usr/bin/env python
'''
FalconConnection

This class is used to manage sdk connection.

'''

import sdk


class FalconConnectionManager:

    def __init__(self):
        print("FalconConnection __init__ +++")

    def create_connection(self, serviceHost, servicePort):
        print("create_connection +++")
        try:
            print "create sdk vehicle"
            self.__vehicle = sdk.Vehicle()
            print "Connecting to Navigation Services @ %s:%d ...\n" % (serviceHost, servicePort)
            # self.vehicle.createConnection(serviceHost, servicePort)
            i = self.__vehicle.create_connection("169.254.149.19", 65101)
            if i == 0:
                print("connected sdk")
            else:
                print("Connection to sdk failed #######")
                self.__vehicle = None

            # start thread to fetch status from SDK
            # self.loop_thread = threading.Thread(target=self.read_vehicle_status, name='LoopThread')
            # self.loop_thread.start()
            return self.__vehicle
        except:
            print "Failed to connect sdk"
