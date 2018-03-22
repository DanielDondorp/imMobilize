# -*- coding: utf-8 -*-
"""
Created on Fri Feb  2 10:28:07 2018

@author: ddo003
"""

from threading import Thread
import time, sys
import pandas as pd



class StimuliManager:
    def __init__(self, arduino = False):
        
        self.df = pd.DataFrame(columns = ["time_on", "time_off", "message_on", "message_off", "id"])
        self.arduino = arduino
        
    def add_stimulus(self, time_on, time_off, message_on, message_off, stim_id):
        df = pd.DataFrame([[time_on, time_off, message_on, message_off, stim_id]], columns = ["time_on", "time_off", "message_on", "message_off", "id"])
        self.df = pd.concat([self.df, df], ignore_index=True)
        self.df = self.df.sort_values("time_on")
    
    def delete_all_stims(self):
        self.df = pd.DataFrame(columns = ["time_on", "time_off", "message_on", "message_off", "id"])
        
    def delete_stimulus(self, stim_id):
        self.df = self.df[self.df.id != stim_id]
    
    def load_new_dataframe(self, path):
        self.df = pd.read_csv(path, delimiter = "\t")
    
    def start_stimuli(self):
        
        ts = []
        ms = []
        for ii in range(len(self.df)):
            s = self.df.iloc[ii]
            ts.append(s.time_on)
            ms.append(s.message_on)
            ts.append(s.time_off)
            ms.append(s.message_off)
        
        tm = pd.DataFrame(dict(zip(["time", "message"],[ts,ms])))
        tm = tm.sort_values("time")
        
        ts = tm.time
        print(ts)
        ms = tm.message
        
        thread = Thread(target = self._run, args = (ts, ms,))
        thread.start()
        
    def _run(self, ts,ms):
        if self.arduino == False:
            sys.stdout.write("\n No controller selected! Stims only printed to console. \n")
            start = time.time()
            for t, m in zip(ts, ms):
                elapsed = time.time() - start
                while elapsed <= t:
                    elapsed = time.time() - start
                    time.sleep(0.05)
                sys.stdout.write("\n"+str( elapsed)+" "+ m +"\n")
        else:
            start = time.time()
            for t, m in zip(ts, ms):
                elapsed = time.time() - start
                while elapsed <= t:
                    elapsed = time.time() - start
                    time.sleep(0.05)
                self.arduino.write(m)
                sys.stdout.write("\n"+str( elapsed)+" "+ m +"\n")
        sys.stdout.write(" \n Done Delivering Stimuli \n")
    
