# -*- coding: utf-8 -*-
"""
Created on Thu Aug  2 12:05:02 2018

@author: install
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Mar  1 15:12:46 2018

@author: ddo003
"""

from multiprocessing import Process, Queue
from threading import Thread
import queue
import cv2
import time, sys
import numpy as np
from PyQt5 import QtCore




class Camera(QtCore.QObject):
    signal_recording_finished = QtCore.pyqtSignal()
    
    def __init__(self, camera: object = 0, framerate: object = 30, shape: object = (7680, 4320), gamma: object = 100, brightness: object = 0,
                 exposure: object = -5.0) -> object:
        """

        :param camera: Which connected camera to use.
        :param framerate:
        :param shape:
        :param gamma:
        :param brightness:
        :param exposure: negative values, gets evaluated  as 2**param_val by camera.
        """
        QtCore.QObject.__init__(self)
        self.camera = camera
        self.cap = cv2.VideoCapture(self.camera)
        self.alive = False
        self.framerate = framerate
        self.shape = shape
        
        self.brightness = self.cap.get(cv2.CAP_PROP_BRIGHTNESS)
        self.aperture = self.cap.get(cv2.CAP_PROP_APERTURE)
        self.gamma = gamma
        
        self.brightness = brightness
        self.exposure  = exposure
        self.q = queue.Queue()

    
    @property
    def framerate(self):
        return self._framerate
    
    @framerate.setter
    def framerate(self, framerate):
        self._framerate = framerate
        self.cap.set(cv2.CAP_PROP_FPS, framerate)
        
        
#        if framerate > 50:
#            self.do_gamma = False
#            print("\n Can not do calculations for gamma at framerates over 50 fps. Calculate corrected gamma on video later\n")
#        else:
#            self.do_gamma = True
        print('Framerate set to: ' + str(framerate))
     
    
    @property
    def gamma(self):
        return self._gamma
    
    @gamma.setter
    def gamma(self, gamma):
        self._gamma = gamma
        self.cap.set(cv2.CAP_PROP_GAMMA, gamma)
        print("Gamma set to ",gamma/100)
        
    @property
    def shape(self):
        return self._shape
    
    @shape.setter
    def shape(self, shape):
        self._shape = shape
        w, h = shape
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        # print("Video shape set to : ", w, h)
        
    @property
    def brightness(self):
        return self._brightness
    
    @brightness.setter
    def brightness(self, brightness):
        self._brightness = brightness
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
    
    @property
    def exposure(self):
        return self._exposure
    
    @exposure.setter
    def exposure(self, exposure):
        self._exposure = exposure
        self.cap.set(cv2.CAP_PROP_EXPOSURE, exposure)
    
    
    def reconnect(self):
        self.cap.release()
        self.cap = cv2.VideoCapture(self.camera)
        
    def read(self):

        ret = False
        while ret == False:
            ret, frame = self.cap.read()

        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
#    def gamma_correction(self, img, correction):
#        img = img/255.0
#        img = cv2.pow(img, correction)
#        return np.uint8(img*255)
    
    def video(self, name = "out", duration = 60, preview = False):
        
        self.write_alive = True
        self.cam_alive = True
        self.alive = True
        
        recording = Thread(target=self._record, args = ())
        writing = Thread(target=self._write, args = (name, duration))
        timer = Thread(target=self._timer, args = (duration,))
        
        self.q = queue.Queue()
        recording.start()
        writing.start()
        timer.start()
    
    def _record(self):
        self.cam_alive = True
        retfalse = 0
        while self.cam_alive:            
            ret, frame = self.cap.read()
            if ret == True:               
                self.q.put(frame)
            else:
                retfalse+=1
        self.q.put("done")
        sys.stdout.write("\n\n Acquisition Done. Missed "+str(retfalse)+" frames \n Finishing up writing video from Queue \n")
        
        
                
    def _write(self, name, duration):
        self.write_alive = True
        w=int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH ))
        h=int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT ))        
        framerate = self.framerate
        
        savepath  = name+".avi"
    
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(savepath,fourcc, framerate, (w,h), isColor = False)
        x = 0
        total_frames = str(self.framerate * duration)
        start = time.time()
        duration = str(duration)
        sys.stdout.write("\n Recording Started \n")
        
        while self.write_alive:
            frame = self.q.get()
            
            if not type(frame) == str:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                out.write(frame)
                x+=1
                self.q.task_done()
                sys.stdout.write("\r Frame "+str(x)+ "/"+total_frames+" Time = "+str(time.time()-start)+"/"+duration+" seconds  ")
            
            else:
                sys.stdout.write("\n\n Queue empty, video writing done \n")
                out.release()
                self.alive = False
                break
#        cv2.destroyAllWindows()

        
    
    def _timer(self, duration):
        start = time.time()
        
        while self.alive and time.time() - start < duration:
            time.sleep(0.001)
        
        self.cam_alive = False
        self.signal_recording_finished.emit()
#        sys.stdout.write("\n\n Acquisition Ended \n")
        
#        time.sleep(0.1)
#        
#        sys.stdout.write("\n\n Recording ended")
    
    def preview(self):
        p = Thread(target=self.start_preview, args = ())
        p.start()
    
    def start_preview(self):
        print("Preview Starting")

#        cap.set(cv2.CAP_PROP_FPS, self.framerate)
        self.alive = True
        
        frames = 0
        start_time = time.time()
        cv2.namedWindow("preview", cv2.WINDOW_NORMAL)
        while self.alive == True:
             
            
            ret, frame = self.cap.read()
            
            if ret == True:
                                                   
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#                if self.do_gamma:
#                    frame = self.gamma_correction(frame, self.gamma)
                cv2.imshow('preview',frame)
            
            
            frames += 1
            if frames == 10:
                end_time = time.time()
                total_time = (end_time - start_time)
                fps = frames / total_time              
                sys.stdout.write("\r fps = "+str(fps)+" time for 10 frames: "+str(total_time))
                frames = 0
                start_time = time.time()
          
        else:
            self.alive = False
            cv2.destroyWindow("preview")
#            cv2.destroyAllWindows()  
    
    def stop(self):
        self.alive = False
        self.cam_alive = False
#        self.write_alive = False
        
            