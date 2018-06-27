# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 09:19:40 2018

@author: ddo003
"""

import serial
import serial.tools.list_ports
import time
import sys


class Arduino:

    def __init__(self):

        self.scan_comports()
        self.connected = False
    def scan_comports(self):

        ports = list(serial.tools.list_ports.comports())
        self.port_dict = {}
        for p in ports:
            if "intel" not in p[1].lower() and "communications" not in p[1].lower():
                self.port_dict[p[1]] = p[0]

        return self.port_dict

    def connect(self, port, baudrate = 115200):

        try:

            self.ser = serial.Serial(self.port_dict[port], baudrate)

            while not self.ser.isOpen():
                sys.stdout.write(".")
                time.sleep(0.1)
            self.port = self.port_dict[port]

            sys.stdout.write("Connected to "+port)
            time.sleep(0.2)
            self.write("nC")
            self.connected = True
        except:
            sys.stdout.write("\n Could not connect to controller on "+port)

    def disconnect(self):

        if self.ser.isOpen():
            self.ser.close()
            self.connected = False

    def write(self, message):

        message = message.encode()
        self.ser.write(message)
