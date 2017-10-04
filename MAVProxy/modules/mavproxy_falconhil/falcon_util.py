#!/usr/bin/env python
'''
FalconHIL Module utility file.  

FalconLogWriter class contains functionality to write in log.

'''

import sys
from pymavlink import mavutil
import threading
import time
import Queue, struct
from pymavlink.dialects.v10 import common
#import traceback


class FalconLogWriter:

    def __init__(self, falcon_logpath):
        print("Log generation __init__")

        self.hil_logqueue = Queue.Queue()
        try:
            mode = 'w'
            #TODO: change this to user defined value
            #falcon_logpath = "/home/deepticl/development/simulation/buildlogs/ArduCopter-test-map.tlog"
            
            self.falcon_logfile = open(falcon_logpath, mode=mode)
            print("Log File: %s" % falcon_logpath)
            
            # Use a separate thread for writing to the logfile to prevent
            # delays during disk writes
            t = threading.Thread(target=self.hil_logwriter, name='hil_logwriter')
            t.daemon = True
            t.start()
        except Exception as e:
            print("ERROR: opening log file for writing: %s" % e)
            #traceback.print_exc()


    def hil_logwriter(self):
        '''log writing thread'''
        while True:
            timeout = time.time() + 10
            while not self.hil_logqueue.empty() and time.time() < timeout:
                self.falcon_logfile.write(self.hil_logqueue.get())
            self.falcon_logfile.flush()
            time.sleep(0.05)

                
    def get_usec(self):
        '''time since 1970 in microseconds'''
        return int(time.time() * 1.0e6)
                            
    def hil_log(self, m):
        #print "******"
        #print "in hil_log, m is: "
        #print m 
        #print "******"
        if self.falcon_logfile and  m.get_type() != 'BAD_DATA' and m.get_type() != 'LOG_DATA':
            usec = self.get_usec() & ~3            # current time as micro sec in int form
            self.hil_logqueue.put(str(struct.pack('>Q', usec) + m.get_msgbuf()))


