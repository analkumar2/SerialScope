# -*- coding: utf-8 -*-
from __future__ import division, print_function

__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2017-, Dilawar Singh"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

import serial
import time
import threading
import math
import queue
import struct

import logging
logger = logging.getLogger("arduino")

class SerialReader():
    """docstring for SerialReader"""
    def __init__(self, port, baud, debug = False):
        self.s = None
        self.port = port
        self.baud = baud
        self.s = None
        self.temp = []
        self.debug = debug
        try:
            self.s = serial.Serial(port, baud)
        except Exception:
            pass
        self.done = False

    def run_without_arduino(self, q, done):
        t0 = time.time()
        while True:
            t = time.time() - t0
            a, b = (1+math.sin(2*math.pi*100*t))*128, (1+math.cos(2*math.pi*50*t))*128
            q.put((t, a, b))
            self.temp.append((1000*t,a,b))
            if done.value == 1:
                logger.info( 'STOP acquiring data.' )
                break
        self.done = True
        self.close()
        q.close()
        return True


    def run(self, q, done):
        # Keep runing and put data in q. 
        logger.info( f"Acquiring data from Arduino." )
        if not self.s:
            logger.warning( "Arduino is not connected.")
            return 

        startT = time.time()
        N = 2**8
        while True:
            t0 = time.time()
            data = self.s.read(2*N)
            t1 = time.time() 
            data = [ord(x) for x in struct.unpack('c'*2*N, data)]
            dt = (t1 - t0)/N
            for i in range(N):
                t, a, b = 1000*(startT+i*dt), data[2*i], data[2*i+1]
                q.put((t, a, b))
            if done == 1:
                logger.info( 'STOP acquiring data.' )
                break
        self.done = True
        self.close()
        q.close()
        return True

    def close(self):
        logger.info( f"Calling close." )
        self.s.close()

def test():
    s = SerialReader( '/dev/ttyACM0', 115200, debug=True)
    q = queue.Queue()
    done = 0
    t = threading.Thread( target=s.run,  args=(q, done))
    t.daemon = True
    t.start()
    time.sleep(200 )
    done = 1
    print(f"Total {q.qsize()} in 10 seconds.")

if __name__ == '__main__':
    test()
